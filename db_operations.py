import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG


class DBOperator:
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

    def login(self, username, password):
        query = "SELECT * FROM User WHERE username = %s AND password = %s"
        user = self.execute_query(query, (username, password))
        return user[0] if user else None

    def register(self, username, password, real_name, phone):
        query = """
        INSERT INTO User (username, password, real_name, phone, user_type) 
        VALUES (%s, %s, %s, %s, 'passenger')
        """
        return self.execute_query(query, (username, password, real_name, phone), fetch=False)

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
        return self.execute_query(query, params)

    def get_user_orders(self, user_id):
        query = """
        SELECT * FROM v_passenger_order 
        WHERE user_id = %s 
        ORDER BY departure_time DESC
        """
        return self.execute_query(query, (user_id,))

    def book_ticket(self, user_id, flight_id, seat_class_id):
        cursor = self.connection.cursor()
        try:
            cursor.callproc('sp_book_ticket', [
                user_id,
                flight_id,
                seat_class_id,
                '',
                ''
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

    def cancel_order(self, order_id):
        query = "UPDATE `Order` SET order_status = 'cancelled' WHERE order_id = %s"
        return self.execute_query(query, (order_id,), fetch=False)

    def get_all_users(self):
        query = "SELECT user_id, username, real_name, user_type, register_time FROM User"
        return self.execute_query(query)

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
        return self.execute_query(query)

    def add_flight(self, flight_no, airline, departure_airport, arrival_airport,
                   departure_time, arrival_time, aircraft_type):
        cursor = self.connection.cursor()
        try:
            query = """
            INSERT INTO Flight (flight_no, airline, departure_airport, arrival_airport, 
                              departure_time, arrival_time, aircraft_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(query, (flight_no, airline, departure_airport,
                                   arrival_airport, departure_time,
                                   arrival_time, aircraft_type))

            flight_id = cursor.lastrowid

            economy_query = """
            INSERT INTO SeatClass (flight_id, class_type, total_seats, remaining_seats, price)
            VALUES (%s, 'economy', 200, 200, 500.00)
            """
            cursor.execute(economy_query, (flight_id,))


            business_query = """
            INSERT INTO SeatClass (flight_id, class_type, total_seats, remaining_seats, price)
            VALUES (%s, 'business', 50, 50, 1200.00)
            """
            cursor.execute(business_query, (flight_id,))

            first_query = """
            INSERT INTO SeatClass (flight_id, class_type, total_seats, remaining_seats, price)
            VALUES (%s, 'first', 20, 20, 3000.00)
            """
            cursor.execute(first_query, (flight_id,))

            self.connection.commit()
            cursor.close()
            return True

        except Error as e:
            self.connection.rollback()
            print(f"添加航班失败: {e}")
            cursor.close()
            return False

    def close(self):
        if self.connection:
            self.connection.close()