from typing import List, Dict, Tuple, Optional
from interfaces import (
    IFlightRepository, IOrderRepository, ISeatClassRepository, IUserRepository
)
import hashlib
import json


class BookingService:
    """预订服务 - 处理机票预订相关业务逻辑"""

    def __init__(self, order_repo: IOrderRepository, seat_repo: ISeatClassRepository):
        """
        依赖注入：通过构造函数传入仓储接口
        这样在单元测试中可以传入 Mock 对象
        """
        self._order_repo = order_repo
        self._seat_repo = seat_repo

    def book_ticket(self, user_id: int, flight_id: int, class_type: str) -> Tuple[bool, str]:
        """
        预订机票的业务逻辑

        业务流程：
        1. 检查舱位是否存在
        2. 检查余票是否充足
        3. 创建订单

        Returns:
            (success: bool, message: str)
        """
        # 1. 获取舱位信息
        seat = self._seat_repo.get_seat_class(flight_id, class_type)
        if not seat:
            return False, f"航班 {flight_id} 的 {class_type} 舱位不存在"

        # 2. 检查余票
        if seat['remaining_seats'] <= 0:
            return False, f"{class_type} 舱位余票不足"

        # 3. 创建订单
        seat_class_id = seat['seat_class_id']
        success, msg = self._order_repo.create_order(user_id, flight_id, seat_class_id)

        return success, msg

    def cancel_order(self, order_repo: IOrderRepository, order_id: int) -> Tuple[bool, str]:
        """取消订单"""
        success = order_repo.cancel_order(order_id)
        if success:
            return True, "订单已取消"
        return False, "取消失败"


class FlightQueryService:
    """航班查询服务"""

    def __init__(self, flight_repo, use_cache=True):
        self._flight_repo = flight_repo
        self._use_cache = use_cache
        self._cache = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def _get_cache_key(self, departure, arrival, date):
        key_dict = {'departure': departure, 'arrival': arrival, 'date': date}
        return hashlib.md5(json.dumps(key_dict, sort_keys=True).encode()).hexdigest()

    def search_flights(self, departure=None, arrival=None, date=None):
        if not self._use_cache:
            return self._flight_repo.get_available_flights(departure, arrival, date)

        cache_key = self._get_cache_key(departure, arrival, date)

        if cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]

        self._cache_misses += 1
        result = self._flight_repo.get_available_flights(departure, arrival, date)
        self._cache[cache_key] = result
        return result

    def get_flight_detail(self, flight_id: int) -> Optional[Dict]:
        """获取航班详情"""
        return self._flight_repo.get_flight_by_id(flight_id)


class UserService:
    """用户服务"""

    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo

    def login(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """用户登录"""
        if not username or not password:
            return False, None
        user = self._user_repo.login(username, password)
        if user:
            return True, user
        return False, None

    def register(self, username: str, password: str, confirm: str,
                 real_name: str, phone: str) -> Tuple[bool, str]:
        """用户注册，包含密码确认逻辑"""
        if not username or not password:
            return False, "用户名和密码不能为空"
        if password != confirm:
            return False, "两次输入的密码不一致"

        success = self._user_repo.register(username, password, real_name, phone)
        if success:
            return True, "注册成功"
        return False, "注册失败，用户名可能已存在"