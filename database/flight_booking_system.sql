-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS flight_booking_system;
USE flight_booking_system;

-- 2. 创建用户表
CREATE TABLE User (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    real_name VARCHAR(50),
    id_card VARCHAR(20),
    phone VARCHAR(20),
    user_type ENUM('passenger', 'admin') NOT NULL DEFAULT 'passenger',
    register_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_user_type (user_type)
);

-- 3. 创建航班表
CREATE TABLE Flight (
    flight_id INT PRIMARY KEY AUTO_INCREMENT,
    flight_no VARCHAR(20) UNIQUE NOT NULL,
    airline VARCHAR(50) NOT NULL,
    departure_airport VARCHAR(50) NOT NULL,
    arrival_airport VARCHAR(50) NOT NULL,
    departure_time DATETIME NOT NULL,
    arrival_time DATETIME NOT NULL,
    aircraft_type VARCHAR(30),
    CONSTRAINT chk_time CHECK (arrival_time > departure_time),
    INDEX idx_departure_time (departure_time),
    INDEX idx_route (departure_airport, arrival_airport)
);

-- 4. 创建舱位表
CREATE TABLE SeatClass (
    seat_class_id INT PRIMARY KEY AUTO_INCREMENT,
    flight_id INT NOT NULL,
    class_type ENUM('economy', 'business', 'first') NOT NULL,
    total_seats INT NOT NULL CHECK (total_seats > 0),
    remaining_seats INT NOT NULL CHECK (remaining_seats >= 0 AND remaining_seats <= total_seats),
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    CONSTRAINT fk_seatclass_flight FOREIGN KEY (flight_id)
        REFERENCES Flight(flight_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_flight_class (flight_id, class_type)
);

-- 5. 创建订单表
CREATE TABLE `Order` (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    flight_id INT NOT NULL,
    seat_class_id INT NOT NULL,
    order_status ENUM('pending', 'paid', 'completed', 'cancelled') NOT NULL DEFAULT 'pending',
    order_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_order_user FOREIGN KEY (user_id)
        REFERENCES User(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_order_flight FOREIGN KEY (flight_id)
        REFERENCES Flight(flight_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_order_seatclass FOREIGN KEY (seat_class_id)
        REFERENCES SeatClass(seat_class_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_order_status (order_status),
    INDEX idx_user_order (user_id, order_status)
);

-- 6. 创建订单状态日志表（触发器使用）
CREATE TABLE OrderStatusLog (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    change_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(50),
    CONSTRAINT fk_log_order FOREIGN KEY (order_id)
        REFERENCES `Order`(order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_change_time (change_time)
);

-- 7. 创建航班余票视图
CREATE VIEW v_flight_availability AS
SELECT
    f.flight_id,
    f.flight_no,
    f.airline,
    f.departure_airport,
    f.arrival_airport,
    f.departure_time,
    f.arrival_time,
    sc.seat_class_id,
    sc.class_type,
    sc.total_seats,
    sc.remaining_seats,
    sc.price
FROM Flight f
JOIN SeatClass sc ON f.flight_id = sc.flight_id
WHERE sc.remaining_seats > 0
AND f.departure_time > NOW();

-- 8. 创建乘客订单视图
CREATE VIEW v_passenger_order AS
SELECT
    o.order_id,
    o.order_no,
    o.order_status,
    f.flight_no,
    f.airline,
    f.departure_airport,
    f.arrival_airport,
    f.departure_time,
    f.arrival_time,
    sc.class_type,
    sc.price,
    o.user_id
FROM `Order` o
JOIN Flight f ON o.flight_id = f.flight_id
JOIN SeatClass sc ON o.seat_class_id = sc.seat_class_id
WHERE EXISTS (
    SELECT 1 FROM User u
    WHERE u.user_id = o.user_id
    AND u.user_type = 'passenger'
);

-- 9. 创建管理员总览视图
CREATE VIEW v_admin_overview AS
SELECT
    u.user_id,
    u.username,
    u.real_name,
    u.user_type,
    u.register_time,
    COUNT(o.order_id) as order_count
FROM User u
LEFT JOIN `Order` o ON u.user_id = o.user_id
GROUP BY u.user_id;

-- 10. 创建预订机票的存储过程
DELIMITER $$

CREATE PROCEDURE sp_book_ticket(
    IN p_user_id INT,
    IN p_flight_id INT,
    IN p_seat_class_id INT,
    OUT p_order_no VARCHAR(50),
    OUT p_result VARCHAR(100)
)
BEGIN
    DECLARE v_remaining_seats INT;
    DECLARE v_user_type VARCHAR(20);
    DECLARE v_order_count INT;

    -- 检查用户是否存在且为乘客
    SELECT user_type INTO v_user_type
    FROM User WHERE user_id = p_user_id;

    IF v_user_type != 'passenger' THEN
        SET p_result = '错误：只有乘客可以预订机票';
        SET p_order_no = NULL;
    ELSE
        -- 检查余票
        SELECT remaining_seats INTO v_remaining_seats
        FROM SeatClass
        WHERE seat_class_id = p_seat_class_id
        AND flight_id = p_flight_id;

        IF v_remaining_seats <= 0 THEN
            SET p_result = '错误：该舱位已无余票';
            SET p_order_no = NULL;
        ELSE
            -- 生成订单号：年月日+随机数
            SET p_order_no = CONCAT(
                DATE_FORMAT(NOW(), '%Y%m%d'),
                LPAD(FLOOR(RAND() * 10000), 4, '0')
            );

            -- 检查订单号是否唯一
            SELECT COUNT(*) INTO v_order_count
            FROM `Order` WHERE order_no = p_order_no;

            WHILE v_order_count > 0 DO
                SET p_order_no = CONCAT(
                    DATE_FORMAT(NOW(), '%Y%m%d'),
                    LPAD(FLOOR(RAND() * 10000), 4, '0')
                );
                SELECT COUNT(*) INTO v_order_count
                FROM `Order` WHERE order_no = p_order_no;
            END WHILE;

            -- 开始事务
            START TRANSACTION;

            -- 插入订单
            INSERT INTO `Order` (order_no, user_id, flight_id, seat_class_id, order_status)
            VALUES (p_order_no, p_user_id, p_flight_id, p_seat_class_id, 'pending');

            -- 扣减余票
            UPDATE SeatClass
            SET remaining_seats = remaining_seats - 1
            WHERE seat_class_id = p_seat_class_id;

            -- 提交事务
            COMMIT;

            SET p_result = '成功：订单已生成，请及时支付';
        END IF;
    END IF;
END$$

DELIMITER ;

-- 11. 创建订单状态变化触发器
DELIMITER $$

CREATE TRIGGER tr_order_status_change
AFTER UPDATE ON `Order`
FOR EACH ROW
BEGIN
    IF OLD.order_status != NEW.order_status THEN
        INSERT INTO OrderStatusLog (order_id, old_status, new_status, changed_by)
        VALUES (NEW.order_id, OLD.order_status, NEW.order_status, USER());
    END IF;
END$$

DELIMITER ;

-- 12. 创建余票检查触发器
DELIMITER $$

CREATE TRIGGER tr_check_seat_availability
BEFORE UPDATE ON SeatClass
FOR EACH ROW
BEGIN
    IF NEW.remaining_seats < 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '错误：剩余座位数不能为负数';
    END IF;

    IF NEW.remaining_seats > NEW.total_seats THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '错误：剩余座位数不能超过总座位数';
    END IF;
END$$

DELIMITER ;
