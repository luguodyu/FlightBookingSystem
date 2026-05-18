import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG
from interfaces import (
    IFlightRepository, IOrderRepository, ISeatClassRepository, IUserRepository
)


class DBOperator(IFlightRepository, IOrderRepository, ISeatClassRepository, IUserRepository):
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            print("数据库连接成功！")
        except Error as e:
            print(f"数据库连接失败: {e}")

    def execute_query(self, query, params=None, fetch=True):
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            if fetch:
                result = cursor.fetchall()
            else:
                result = cursor.rowcount
                self.connection.commit()
            return result
        except Error as e:
            print(f"查询执行失败: {e}")
            return None
        finally:
            cursor.close()

    #实现 IUserRepository 接口
    def login(self, username, password):
        query = "SELECT * FROM User WHERE username = %s AND password = %s"
        user = self.execute_query(query, (username, password))
        return user[0] if user else None

    def register(self, username, password, real_name, phone):
        query = """
        INSERT INTO User (username, password, real_name, phone, user_type) 
        VALUES (%s, %s, %s, %s, 'passenger')
        """
        result = self.execute_query(query, (username, password, real_name, phone), fetch=False)
        return result is not None and result > 0

    def get_all_users(self):
        query = "SELECT user_id, username, real_name, user_type, register_time FROM User"
        return self.execute_query(query) or []

    #实现 IFlightRepository 接口
    def get_available_flights(self, departure=None, arrival=None, date=None):
        query = "SELECT * FROM v_flight_availability WHERE 1=1"
        params = []

        if departure:
            query += " AND departure_airport LIKE %s"
            params.append(f"%{departure}%")
        if arrival:
            query += " AND arrival_airport LIKE %s"
            params.append(f"%{arrival}%")
        if date:
            query += " AND DATE(departure_time) = %s"
            params.append(date)

        query += " ORDER BY departure_time"
        return self.execute_query(query, params) or []

    def get_flight_by_id(self, flight_id):
        query = "SELECT * FROM Flight WHERE flight_id = %s"
        result = self.execute_query(query, (flight_id,))
        return result[0] if result else None

    def get_flight_by_no_and_date(self, flight_no, date):
        query = """
        SELECT flight_id FROM Flight 
        WHERE flight_no = %s AND DATE(departure_time) = %s
        """
        result = self.execute_query(query, (flight_no, date))
        return result[0] if result else None

    #实现 IOrderRepository 接口

    def create_order(self, user_id, flight_id, seat_class_id):
        """使用存储过程创建订单"""
        cursor = self.connection.cursor()
        try:
            cursor.callproc('sp_book_ticket', [
                user_id, flight_id, seat_class_id, '', ''
            ])
            cursor.execute("SELECT @_sp_book_ticket_3, @_sp_book_ticket_4")
            out_params = cursor.fetchone()
            self.connection.commit()

            if out_params and out_params[1] and '错误' not in out_params[1]:
                return True, out_params[1]
            elif out_params and out_params[1]:
                return False, out_params[1]
            else:
                return True, "预订成功"
        except Error as e:
            self.connection.rollback()
            return False, str(e)
        finally:
            cursor.close()

    def get_user_orders(self, user_id):
        query = """
        SELECT * FROM v_passenger_order 
        WHERE user_id = %s 
        ORDER BY departure_time DESC
        """
        return self.execute_query(query, (user_id,)) or []

    def cancel_order(self, order_id):
        query = "UPDATE `Order` SET order_status = 'cancelled' WHERE order_id = %s"
        result = self.execute_query(query, (order_id,), fetch=False)
        return result is not None

    def get_all_orders(self):
        query = """
        SELECT o.order_id, o.order_no, u.username, f.flight_no, 
               sc.class_type, o.order_status
        FROM `Order` o
        JOIN User u ON o.user_id = u.user_id
        JOIN Flight f ON o.flight_id = f.flight_id
        JOIN SeatClass sc ON o.seat_class_id = sc.seat_class_id
        ORDER BY o.order_id DESC
        """
        return self.execute_query(query) or []

    #实现 ISeatClassRepository 接口

    def get_seat_class(self, flight_id, class_type):
        query = """
        SELECT seat_class_id, flight_id, class_type, total_seats, remaining_seats, price
        FROM SeatClass 
        WHERE flight_id = %s AND class_type = %s
        """
        result = self.execute_query(query, (flight_id, class_type))
        return result[0] if result else None

    def get_seat_class_by_id(self, seat_class_id):
        query = "SELECT * FROM SeatClass WHERE seat_class_id = %s"
        result = self.execute_query(query, (seat_class_id,))
        return result[0] if result else None

    def update_remaining_seats(self, seat_class_id, new_remaining):
        query = "UPDATE SeatClass SET remaining_seats = %s WHERE seat_class_id = %s"
        result = self.execute_query(query, (new_remaining, seat_class_id), fetch=False)
        return result is not None

    def get_flight_seats(self, flight_id):
        query = """
        SELECT seat_class_id, class_type, total_seats, remaining_seats, price
        FROM SeatClass WHERE flight_id = %s
        """
        return self.execute_query(query, (flight_id,)) or []

    #原有方法保持兼容（但内部已实现接口

    def book_ticket(self, user_id, flight_id, seat_class_id):
        """保留原方法名，内部调用 create_order 以保持兼容"""
        return self.create_order(user_id, flight_id, seat_class_id)

    def close(self):
        if self.connection:
            self.connection.close()