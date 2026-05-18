import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from db_operations import DBOperator


class LoginWindow:

    def __init__(self, booking_service, flight_service, user_service, db):
        # 接收服务层对象而不是直接创建 db
        self.booking_service = booking_service
        self.flight_service = flight_service
        self.user_service = user_service
        self.db = db  # 保留 db 用于管理员功能，后续也可以改为服务层
        self.current_user = None

        self.root = tk.Tk()
        self.root.title("机票预订系统 - 登录")
        self.root.geometry("400x300")

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="机票预订系统", font=("Arial", 16)).pack(pady=20)

        tk.Label(self.root, text="用户名:").pack()
        self.username_entry = tk.Entry(self.root, width=30)
        self.username_entry.pack(pady=5)

        tk.Label(self.root, text="密码:").pack()
        self.password_entry = tk.Entry(self.root, width=30, show="*")
        self.password_entry.pack(pady=5)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="登录", command=self.login, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="注册", command=self.open_register, width=10).pack(side=tk.LEFT, padx=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning("提示", "请输入用户名和密码")
            return

        success, user = self.user_service.login(username, password)
        if success:
            self.current_user = user
            self.root.destroy()

            if user['user_type'] == 'admin':
                AdminWindow(self.db, user)  # 管理员暂时保持原样
            else:
                PassengerWindow(self.booking_service, self.flight_service, user, self.db)
        else:
            messagebox.showerror("登录失败", "用户名或密码错误")

    def open_register(self):
        RegisterDialog(self.root, self.user_service)

    def run(self):
        self.root.mainloop()
        self.db.close()


class PassengerWindow:

    def __init__(self, booking_service, flight_service, user, db):
        self.booking_service = booking_service
        self.flight_service = flight_service
        self.db = db  # 保留用于部分功能
        self.user = user

        self.root = tk.Tk()
        self.root.title(f"机票预订系统 - 欢迎 {user['real_name'] or user['username']}")
        self.root.geometry("900x600")

        self.create_widgets()
        self.load_orders()

    def create_widgets(self):
        tk.Label(self.root, text="乘客功能", font=("Arial", 14)).pack(pady=10)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.query_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.query_frame, text="查询航班")
        self.create_query_tab()

        self.order_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.order_frame, text="我的订单")
        self.create_order_tab()

        self.profile_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.profile_frame, text="个人信息")
        self.create_profile_tab()

    def create_query_tab(self):
        condition_frame = ttk.LabelFrame(self.query_frame, text="查询条件")
        condition_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(condition_frame, text="出发地:").grid(row=0, column=0, padx=5, pady=5)
        self.departure_entry = ttk.Entry(condition_frame, width=20)
        self.departure_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(condition_frame, text="目的地:").grid(row=0, column=2, padx=5, pady=5)
        self.arrival_entry = ttk.Entry(condition_frame, width=20)
        self.arrival_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(condition_frame, text="日期:").grid(row=0, column=4, padx=5, pady=5)
        self.date_entry = ttk.Entry(condition_frame, width=15)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(condition_frame, text="查询", command=self.search_flights).grid(row=0, column=6, padx=10)

        list_frame = ttk.Frame(self.query_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("航班号", "航空公司", "出发", "到达", "时间", "舱位", "余票", "价格")
        self.flight_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.flight_tree.heading(col, text=col)
            self.flight_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.flight_tree.yview)
        self.flight_tree.configure(yscrollcommand=scrollbar.set)

        self.flight_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(self.query_frame, text="预订选中航班", command=self.book_selected).pack(pady=10)

    def search_flights(self):
        departure = self.departure_entry.get()
        arrival = self.arrival_entry.get()
        date = self.date_entry.get()

        flights = self.db.get_available_flights(departure, arrival, date)

        for item in self.flight_tree.get_children():
            self.flight_tree.delete(item)

        for flight in flights:
            unique_id = f"{flight['flight_id']}_{flight['class_type']}"

            values = (
                flight['flight_no'],
                flight['airline'],
                flight['departure_airport'],
                flight['arrival_airport'],
                flight['departure_time'].strftime("%Y-%m-%d %H:%M"),
                flight['class_type'],
                flight['remaining_seats'],
                f"¥{flight['price']}"
            )
            self.flight_tree.insert("", tk.END, values=values, iid=unique_id)

    def book_selected(self):
        selected = self.flight_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要预订的航班")
            return

        item = self.flight_tree.item(selected[0])
        values = item['values']

        flight_no = values[0]
        departure_time_str = values[4]
        class_type = values[5]

        try:
            # 1. 根据航班号和日期获取航班ID
            departure_date = departure_time_str[:10]
            flight = self.flight_service._flight_repo.get_flight_by_no_and_date(flight_no, departure_date)

            if not flight:
                messagebox.showerror("错误", "无法找到对应的航班")
                return

            flight_id = flight[0]['flight_id']

            # 2. 使用服务层预订

            success, msg = self.booking_service.book_ticket(
                self.user['user_id'], flight_id, class_type
            )

            if success:
                messagebox.showinfo("成功", msg)
                self.load_orders()  # 刷新订单列表
                self.search_flights()  # 刷新航班列表（更新余票）
            else:
                messagebox.showerror("失败", msg)

        except Exception as e:
            messagebox.showerror("错误", f"预订时出错: {str(e)}")

    def create_order_tab(self):
        columns = ("订单号", "航班号", "出发", "到达", "时间", "舱位", "状态", "价格")
        self.order_tree = ttk.Treeview(self.order_frame, columns=columns, show="headings", height=20)

        for col in columns:
            self.order_tree.heading(col, text=col)
            self.order_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(self.order_frame, orient=tk.VERTICAL, command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=scrollbar.set)

        self.order_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = ttk.Frame(self.order_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(btn_frame, text="刷新", command=self.load_orders).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消订单", command=self.cancel_order).pack(side=tk.LEFT, padx=5)

    def load_orders(self):
        orders = self.db.get_user_orders(self.user['user_id'])

        for item in self.order_tree.get_children():
            self.order_tree.delete(item)

        for order in orders:
            values = (
                order['order_no'],
                order['flight_no'],
                order['departure_airport'],
                order['arrival_airport'],
                order['departure_time'].strftime("%Y-%m-%d %H:%M"),
                order['class_type'],
                order['order_status'],
                f"¥{order['price']}"
            )
            self.order_tree.insert("", tk.END, values=values, iid=order['order_id'])

    def cancel_order(self):
        selected = self.order_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要取消的订单")
            return

        order_id = selected[0]
        if messagebox.askyesno("确认", "确定要取消这个订单吗？"):
            result = self.db.cancel_order(order_id)
            if result:
                messagebox.showinfo("成功", "订单已取消")
                self.load_orders()

    def create_profile_tab(self):
        info_frame = ttk.LabelFrame(self.profile_frame, text="个人信息")
        info_frame.pack(fill=tk.X, padx=20, pady=20)

        info_text = f"""
用户名: {self.user['username']}
真实姓名: {self.user['real_name'] or '未设置'}
证件号: {self.user['id_card'] or '未设置'}
手机号: {self.user['phone'] or '未设置'}
用户类型: {self.user['user_type']}
注册时间: {self.user['register_time']}
        """

        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(padx=10, pady=10)

    def run(self):
        self.root.mainloop()


class AdminWindow:

    def __init__(self, db, user):
        self.db = db
        self.user = user

        self.root = tk.Tk()
        self.root.title(f"机票预订系统 - 管理员后台")
        self.root.geometry("1100x750")

        self.create_widgets()
        self.load_users()
        self.load_all_flights()
        self.load_all_seat_classes()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.user_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.user_frame, text="用户管理")
        self.create_user_tab()

        self.order_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.order_frame, text="订单管理")
        self.create_order_tab()

        self.flight_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.flight_frame, text="航班管理")
        self.create_flight_tab()

        self.seat_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.seat_frame, text="舱位管理")
        self.create_seat_tab()

    def create_user_tab(self):
        columns = ("用户ID", "用户名", "真实姓名", "用户类型", "注册时间", "订单数量")
        self.user_tree = ttk.Treeview(self.user_frame, columns=columns, show="headings", height=20)

        for col in columns:
            self.user_tree.heading(col, text=col)
            self.user_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(self.user_frame, orient=tk.VERTICAL, command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=scrollbar.set)

        self.user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(self.user_frame, text="刷新", command=self.load_users).pack(pady=5)

    def load_users(self):
        users = self.db.get_all_users()

        for item in self.user_tree.get_children():
            self.user_tree.delete(item)

        for user in users:
            self.user_tree.insert("", tk.END, values=(
                user['user_id'],
                user['username'],
                user['real_name'],
                user['user_type'],
                user['register_time'].strftime("%Y-%m-%d %H:%M"),
                "0"
            ))

    def create_order_tab(self):
        columns = ("订单ID", "订单号", "用户名", "航班号", "舱位", "状态")
        self.admin_order_tree = ttk.Treeview(self.order_frame, columns=columns, show="headings", height=20)

        for col in columns:
            self.admin_order_tree.heading(col, text=col)
            self.admin_order_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(self.order_frame, orient=tk.VERTICAL, command=self.admin_order_tree.yview)
        self.admin_order_tree.configure(yscrollcommand=scrollbar.set)

        self.admin_order_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(self.order_frame, text="加载所有订单", command=self.load_all_orders).pack(pady=5)

    def load_all_orders(self):
        orders = self.db.get_all_orders()

        for item in self.admin_order_tree.get_children():
            self.admin_order_tree.delete(item)

        for order in orders:
            self.admin_order_tree.insert("", tk.END, values=(
                order['order_id'],
                order['order_no'],
                order['username'],
                order['flight_no'],
                order['class_type'],
                order['order_status']
            ))

    def create_flight_tab(self):
        form_frame = ttk.LabelFrame(self.flight_frame, text="添加新航班")
        form_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(form_frame, text="航班号:").grid(row=0, column=0, padx=5, pady=5)
        self.flight_no_entry = ttk.Entry(form_frame, width=20)
        self.flight_no_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="航空公司:").grid(row=0, column=2, padx=5, pady=5)
        self.airline_entry = ttk.Entry(form_frame, width=20)
        self.airline_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form_frame, text="出发机场:").grid(row=1, column=0, padx=5, pady=5)
        self.departure_entry = ttk.Entry(form_frame, width=20)
        self.departure_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="到达机场:").grid(row=1, column=2, padx=5, pady=5)
        self.arrival_entry = ttk.Entry(form_frame, width=20)
        self.arrival_entry.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(form_frame, text="起飞时间:").grid(row=2, column=0, padx=5, pady=5)
        self.departure_time_entry = ttk.Entry(form_frame, width=20)
        self.departure_time_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="到达时间:").grid(row=2, column=2, padx=5, pady=5)
        self.arrival_time_entry = ttk.Entry(form_frame, width=20)
        self.arrival_time_entry.grid(row=2, column=3, padx=5, pady=5)

        ttk.Label(form_frame, text="机型:").grid(row=3, column=0, padx=5, pady=5)
        self.aircraft_entry = ttk.Entry(form_frame, width=20)
        self.aircraft_entry.grid(row=3, column=1, padx=5, pady=5)

        ttk.Button(form_frame, text="添加航班", command=self.add_flight).grid(row=3, column=3, padx=5, pady=5)

        list_frame = ttk.LabelFrame(self.flight_frame, text="航班列表")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("航班ID", "航班号", "航空公司", "出发机场", "到达机场", "起飞时间", "到达时间", "机型")
        self.flight_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.flight_tree.heading(col, text=col)
            self.flight_tree.column(col, width=100)

        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.flight_tree.yview)
        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.flight_tree.xview)
        self.flight_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.flight_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5)

        ttk.Button(btn_frame, text="刷新航班列表", command=self.load_all_flights).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除选中航班", command=self.delete_flight).pack(side=tk.LEFT, padx=5)

    def load_all_flights(self):
        query = "SELECT * FROM Flight ORDER BY departure_time DESC"
        flights = self.db.execute_query(query)

        for item in self.flight_tree.get_children():
            self.flight_tree.delete(item)

        for flight in flights:
            self.flight_tree.insert("", tk.END, values=(
                flight['flight_id'],
                flight['flight_no'],
                flight['airline'],
                flight['departure_airport'],
                flight['arrival_airport'],
                flight['departure_time'].strftime("%Y-%m-%d %H:%M"),
                flight['arrival_time'].strftime("%Y-%m-%d %H:%M"),
                flight['aircraft_type']
            ), iid=flight['flight_id'])

    def delete_flight(self):
        selected = self.flight_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要删除的航班")
            return

        flight_id = selected[0]
        item = self.flight_tree.item(flight_id)
        flight_no = item['values'][1]

        if messagebox.askyesno("确认删除", f"确定要删除航班 {flight_no} 吗？\n注意：这将同时删除该航班的所有舱位和订单！"):
            delete_orders_query = "DELETE FROM `Order` WHERE flight_id = %s"
            self.db.execute_query(delete_orders_query, (flight_id,), fetch=False)

            delete_seats_query = "DELETE FROM SeatClass WHERE flight_id = %s"
            self.db.execute_query(delete_seats_query, (flight_id,), fetch=False)

            delete_flight_query = "DELETE FROM Flight WHERE flight_id = %s"
            result = self.db.execute_query(delete_flight_query, (flight_id,), fetch=False)

            if result:
                messagebox.showinfo("成功", f"航班 {flight_no} 已删除")
                self.load_all_flights()
                self.load_all_seat_classes()
            else:
                messagebox.showerror("失败", "删除航班失败")

    def create_seat_tab(self):
        select_frame = ttk.LabelFrame(self.seat_frame, text="选择航班")
        select_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(select_frame, text="选择航班:").grid(row=0, column=0, padx=5, pady=5)

        flights = self.db.execute_query("SELECT flight_id, flight_no FROM Flight ORDER BY flight_no")
        flight_options = [f"{f['flight_no']} (ID:{f['flight_id']})" for f in flights]

        self.selected_flight_var = tk.StringVar()
        self.flight_combo = ttk.Combobox(select_frame, textvariable=self.selected_flight_var,
                                         values=flight_options, width=30, state="readonly")
        self.flight_combo.grid(row=0, column=1, padx=5, pady=5)

        if flight_options:
            self.flight_combo.current(0)

        ttk.Button(select_frame, text="查看舱位", command=self.load_flight_seats).grid(row=0, column=2, padx=10)

        list_frame = ttk.LabelFrame(self.seat_frame, text="舱位信息")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("舱位ID", "航班号", "舱位类型", "总座位数", "剩余座位", "价格")
        self.seat_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.seat_tree.heading(col, text=col)
            self.seat_tree.column(col, width=100)

        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.seat_tree.yview)
        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.seat_tree.xview)
        self.seat_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.seat_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5)

        ttk.Button(btn_frame, text="刷新舱位", command=self.load_all_seat_classes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除选中舱位", command=self.delete_seat_class).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="修改舱位信息", command=self.edit_seat_class).pack(side=tk.LEFT, padx=5)

    def load_all_seat_classes(self):
        query = """
        SELECT sc.seat_class_id, f.flight_no, sc.class_type, 
               sc.total_seats, sc.remaining_seats, sc.price
        FROM SeatClass sc
        JOIN Flight f ON sc.flight_id = f.flight_id
        ORDER BY f.flight_no, sc.class_type
        """
        seats = self.db.execute_query(query)

        for item in self.seat_tree.get_children():
            self.seat_tree.delete(item)

        for seat in seats:
            self.seat_tree.insert("", tk.END, values=(
                seat['seat_class_id'],
                seat['flight_no'],
                seat['class_type'],
                seat['total_seats'],
                seat['remaining_seats'],
                f"¥{seat['price']}"
            ), iid=seat['seat_class_id'])

    def load_flight_seats(self):
        selected = self.selected_flight_var.get()
        if not selected:
            messagebox.showwarning("提示", "请先选择航班")
            return

        flight_id = selected.split("(ID:")[1].rstrip(")")

        query = """
        SELECT sc.seat_class_id, f.flight_no, sc.class_type, 
               sc.total_seats, sc.remaining_seats, sc.price
        FROM SeatClass sc
        JOIN Flight f ON sc.flight_id = f.flight_id
        WHERE sc.flight_id = %s
        ORDER BY sc.class_type
        """
        seats = self.db.execute_query(query, (flight_id,))

        for item in self.seat_tree.get_children():
            self.seat_tree.delete(item)

        for seat in seats:
            self.seat_tree.insert("", tk.END, values=(
                seat['seat_class_id'],
                seat['flight_no'],
                seat['class_type'],
                seat['total_seats'],
                seat['remaining_seats'],
                f"¥{seat['price']}"
            ), iid=seat['seat_class_id'])

    def delete_seat_class(self):
        selected = self.seat_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要删除的舱位")
            return

        seat_class_id = selected[0]
        item = self.seat_tree.item(seat_class_id)
        flight_no = item['values'][1]
        class_type = item['values'][2]

        if messagebox.askyesno("确认删除",
                               f"确定要删除航班 {flight_no} 的 {class_type} 舱位吗？\n注意：这将删除该舱位的所有预订！"):

            delete_orders_query = """
            DELETE FROM `Order` 
            WHERE seat_class_id = %s
            """
            self.db.execute_query(delete_orders_query, (seat_class_id,), fetch=False)

            delete_seat_query = "DELETE FROM SeatClass WHERE seat_class_id = %s"
            result = self.db.execute_query(delete_seat_query, (seat_class_id,), fetch=False)

            if result:
                messagebox.showinfo("成功", f"{class_type}舱位已删除")
                self.load_all_seat_classes()
            else:
                messagebox.showerror("失败", "删除舱位失败")

    def edit_seat_class(self):
        selected = self.seat_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要修改的舱位")
            return

        seat_class_id = selected[0]
        item = self.seat_tree.item(seat_class_id)

        dialog = tk.Toplevel(self.root)
        dialog.title("修改舱位信息")
        dialog.geometry("300x250")

        tk.Label(dialog, text="修改舱位信息", font=("Arial", 12)).pack(pady=10)

        form_frame = tk.Frame(dialog)
        form_frame.pack(pady=10)

        current_values = item['values']

        tk.Label(form_frame, text="总座位数:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        total_seats_entry = tk.Entry(form_frame, width=25)
        total_seats_entry.insert(0, current_values[3])
        total_seats_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="剩余座位:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        remaining_seats_entry = tk.Entry(form_frame, width=25)
        remaining_seats_entry.insert(0, current_values[4])
        remaining_seats_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="价格:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        price_entry = tk.Entry(form_frame, width=25)
        price_str = str(current_values[5]).replace('¥', '')
        price_entry.insert(0, price_str)
        price_entry.grid(row=2, column=1, padx=5, pady=5)

        def save_changes():
            try:
                total_seats = int(total_seats_entry.get())
                remaining_seats = int(remaining_seats_entry.get())
                price = float(price_entry.get())

                if total_seats < 0 or remaining_seats < 0 or price < 0:
                    messagebox.showwarning("提示", "数值不能为负数")
                    return

                if remaining_seats > total_seats:
                    messagebox.showwarning("提示", "剩余座位数不能大于总座位数")
                    return

                update_query = """
                UPDATE SeatClass 
                SET total_seats = %s, remaining_seats = %s, price = %s
                WHERE seat_class_id = %s
                """

                result = self.db.execute_query(update_query,
                                               (total_seats, remaining_seats, price, seat_class_id),
                                               fetch=False)

                if result:
                    messagebox.showinfo("成功", "舱位信息已更新")
                    dialog.destroy()
                    self.load_all_seat_classes()
                else:
                    messagebox.showerror("失败", "更新舱位信息失败")

            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="保存", command=save_changes, width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="取消", command=dialog.destroy, width=10).pack(side=tk.LEFT)

    def add_flight(self):
        flight_no = self.flight_no_entry.get()
        airline = self.airline_entry.get()
        departure_airport = self.departure_entry.get()
        arrival_airport = self.arrival_entry.get()
        departure_time = self.departure_time_entry.get()
        arrival_time = self.arrival_time_entry.get()
        aircraft_type = self.aircraft_entry.get()

        if not all([flight_no, airline, departure_airport, arrival_airport, departure_time, arrival_time]):
            messagebox.showwarning("提示", "请填写所有必填项")
            return

        result = self.db.add_flight(flight_no, airline, departure_airport, arrival_airport,
                                    departure_time, arrival_time, aircraft_type)
        if result:
            messagebox.showinfo("成功", "航班添加成功")
            for entry in [self.flight_no_entry, self.airline_entry, self.departure_entry,
                          self.arrival_entry, self.departure_time_entry,
                          self.arrival_time_entry, self.aircraft_entry]:
                entry.delete(0, tk.END)
            self.load_all_flights()
            self.load_all_seat_classes()
        else:
            messagebox.showerror("失败", "航班添加失败")

    def run(self):
        self.root.mainloop()


class RegisterDialog:

    def __init__(self, parent, user_service):
        self.user_service = user_service  # 注入服务层
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("用户注册")
        self.dialog.geometry("350x300")
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.dialog, text="用户注册", font=("Arial", 12)).pack(pady=10)

        form_frame = tk.Frame(self.dialog)
        form_frame.pack(pady=10)

        labels = ["用户名:", "密码:", "确认密码:", "真实姓名:", "手机号:"]
        self.entries = {}

        for i, label in enumerate(labels):
            tk.Label(form_frame, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="e")
            entry = tk.Entry(form_frame, width=25)
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.entries[label] = entry

        self.entries["密码:"].config(show="*")
        self.entries["确认密码:"].config(show="*")

        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="注册", command=self.register, width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="取消", command=self.dialog.destroy, width=10).pack(side=tk.LEFT)

    def register(self):
        username = self.entries["用户名:"].get()
        password = self.entries["密码:"].get()
        confirm = self.entries["确认密码:"].get()
        real_name = self.entries["真实姓名:"].get()
        phone = self.entries["手机号:"].get()

        # 使用 UserService 进行注册
        success, msg = self.user_service.register(username, password, confirm, real_name, phone)
        if success:
            messagebox.showinfo("成功", msg)
            self.dialog.destroy()
        else:
            messagebox.showerror("失败", msg)