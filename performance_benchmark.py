"""
性能基准测试脚本
用于定位性能瓶颈和对比优化效果
"""
import cProfile
import pstats
import io
import time
from db_operations import DBOperator
from services import BookingService, FlightQueryService


def benchmark_flight_query():
    """测试航班查询性能"""
    db = DBOperator()
    service = FlightQueryService(db)

    # 模拟多次查询
    for i in range(100):
        result = service.search_flights(
            departure="北京",
            arrival="上海",
            date="2025-12-01"
        )
    return len(result) if result else 0


def benchmark_booking():
    """测试预订流程性能（不实际写入，只测试查询部分）"""
    db = DBOperator()
    booking_service = BookingService(db, db)

    # 获取一个有效航班
    flights = db.get_available_flights()
    if not flights:
        return

    flight = flights[0]
    # 测试查询舱位（不实际创建订单）
    seat = db.get_seat_class(flight['flight_id'], 'economy')
    return seat


def run_profile():
    """运行性能分析"""
    profiler = cProfile.Profile()
    profiler.enable()

    # 运行被测函数
    benchmark_flight_query()
    benchmark_booking()

    profiler.disable()

    # 输出结果
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    stats.print_stats(20)  # 打印前20个耗时函数

    print(s.getvalue())

    # 保存结果文件，可用 snakeviz 可视化
    stats.dump_stats('profile_results.prof')
    print("\n性能分析结果已保存到 profile_results.prof")
    print("使用 'snakeviz profile_results.prof' 查看可视化火焰图")


if __name__ == "__main__":
    run_profile()