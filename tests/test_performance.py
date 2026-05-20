import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from db_operations import DBOperator
from services import FlightQueryService, BookingService


class TestPerformance:
    """性能基准测试"""

    @pytest.fixture
    def db(self):
        return DBOperator()

    def test_flight_query_performance(self, db, benchmark):
        """测试航班查询性能基准"""
        service = FlightQueryService(db)

        def query():
            return service.search_flights(departure="北京", arrival="上海")

        result = benchmark(query)
        assert result is not None

    def test_booking_query_performance(self, db, benchmark):
        """测试预订查询性能（不实际下单）"""
        flights = db.get_available_flights()
        if not flights:
            pytest.skip("没有可用航班")

        flight = flights[0]

        def get_seat():
            return db.get_seat_class(flight['flight_id'], 'economy')

        result = benchmark(get_seat)
        assert result is not None