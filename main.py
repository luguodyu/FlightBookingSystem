from db_operations import DBOperator
from services import BookingService, FlightQueryService, UserService
from ui_components import LoginWindow


def main():
    print("机票预订系统启动")

    # 1. 创建数据库操作对象（实现所有仓储接口）
    db = DBOperator()

    # 2. 创建服务层对象（注入依赖）
    booking_service = BookingService(db, db)  # db 同时实现了 IOrderRepository 和 ISeatClassRepository
    flight_service = FlightQueryService(db)  # db 实现了 IFlightRepository
    user_service = UserService(db)  # db 实现了 IUserRepository

    # 3. 创建UI窗口（注入服务层）
    app = LoginWindow(booking_service, flight_service, user_service, db)
    app.run()


if __name__ == "__main__":
    main()