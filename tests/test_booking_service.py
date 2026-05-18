import pytest
from unittest.mock import Mock
from services import BookingService


class TestBookingService:
    """预订服务单元测试 - 使用 Mock 对象，不依赖真实数据库"""

    def test_book_ticket_success(self):
        """测试：正常预订成功"""
        # 准备 Mock 对象
        mock_order_repo = Mock()
        mock_seat_repo = Mock()

        # 模拟舱位存在且有余票
        mock_seat_repo.get_seat_class.return_value = {
            'seat_class_id': 10,
            'remaining_seats': 5,
            'class_type': 'economy'
        }
        # 模拟订单创建成功
        mock_order_repo.create_order.return_value = (True, "预订成功")

        # 执行测试
        service = BookingService(mock_order_repo, mock_seat_repo)
        success, msg = service.book_ticket(user_id=1, flight_id=100, class_type="economy")

        # 验证结果
        assert success is True
        assert msg == "预订成功"
        mock_seat_repo.get_seat_class.assert_called_once_with(100, "economy")
        mock_order_repo.create_order.assert_called_once_with(1, 100, 10)

    def test_book_ticket_seat_not_exist(self):
        """测试：舱位不存在"""
        mock_order_repo = Mock()
        mock_seat_repo = Mock()

        # 模拟舱位不存在
        mock_seat_repo.get_seat_class.return_value = None

        service = BookingService(mock_order_repo, mock_seat_repo)
        success, msg = service.book_ticket(1, 100, "first")

        assert success is False
        assert "舱位不存在" in msg
        mock_order_repo.create_order.assert_not_called()  # 不应该调用创建订单

    def test_book_ticket_no_remaining_seats(self):
        """测试：余票不足"""
        mock_order_repo = Mock()
        mock_seat_repo = Mock()

        # 模拟舱位存在但余票为0
        mock_seat_repo.get_seat_class.return_value = {
            'seat_class_id': 10,
            'remaining_seats': 0
        }

        service = BookingService(mock_order_repo, mock_seat_repo)
        success, msg = service.book_ticket(1, 100, "economy")

        assert success is False
        assert "余票不足" in msg
        mock_order_repo.create_order.assert_not_called()

    def test_book_ticket_negative_remaining(self):
        """测试：余票为负数（异常情况）"""
        mock_order_repo = Mock()
        mock_seat_repo = Mock()

        mock_seat_repo.get_seat_class.return_value = {
            'seat_class_id': 10,
            'remaining_seats': -1
        }

        service = BookingService(mock_order_repo, mock_seat_repo)
        success, msg = service.book_ticket(1, 100, "economy")

        assert success is False
        assert "余票不足" in msg