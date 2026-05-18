"""
仓储接口定义层
用于解耦业务逻辑与具体数据库实现，提升可测试性
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple


class IFlightRepository(ABC):
    """航班数据访问接口"""

    @abstractmethod
    def get_available_flights(self, departure: Optional[str] = None,
                              arrival: Optional[str] = None,
                              date: Optional[str] = None) -> List[Dict]:
        """查询可用航班"""
        pass

    @abstractmethod
    def get_flight_by_id(self, flight_id: int) -> Optional[Dict]:
        """根据ID获取航班信息"""
        pass

    @abstractmethod
    def get_flight_by_no_and_date(self, flight_no: str, date: str) -> Optional[Dict]:
        """根据航班号和日期获取航班"""
        pass


class IOrderRepository(ABC):
    """订单数据访问接口"""

    @abstractmethod
    def create_order(self, user_id: int, flight_id: int, seat_class_id: int) -> Tuple[bool, str]:
        """创建订单，返回(成功标志, 消息)"""
        pass

    @abstractmethod
    def get_user_orders(self, user_id: int) -> List[Dict]:
        """获取用户的所有订单"""
        pass

    @abstractmethod
    def cancel_order(self, order_id: int) -> bool:
        """取消订单"""
        pass

    @abstractmethod
    def get_all_orders(self) -> List[Dict]:
        """获取所有订单（管理员用）"""
        pass


class ISeatClassRepository(ABC):
    """舱位数据访问接口"""

    @abstractmethod
    def get_seat_class(self, flight_id: int, class_type: str) -> Optional[Dict]:
        """获取指定航班的指定舱位信息"""
        pass

    @abstractmethod
    def get_seat_class_by_id(self, seat_class_id: int) -> Optional[Dict]:
        """根据舱位ID获取信息"""
        pass

    @abstractmethod
    def update_remaining_seats(self, seat_class_id: int, new_remaining: int) -> bool:
        """更新剩余座位数"""
        pass

    @abstractmethod
    def get_flight_seats(self, flight_id: int) -> List[Dict]:
        """获取航班的所有舱位"""
        pass


class IUserRepository(ABC):
    """用户数据访问接口"""

    @abstractmethod
    def login(self, username: str, password: str) -> Optional[Dict]:
        """用户登录验证"""
        pass

    @abstractmethod
    def register(self, username: str, password: str, real_name: str, phone: str) -> bool:
        """用户注册"""
        pass

    @abstractmethod
    def get_all_users(self) -> List[Dict]:
        """获取所有用户（管理员用）"""
        pass