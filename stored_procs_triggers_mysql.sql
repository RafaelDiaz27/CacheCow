-- Trigger: update product average rating after insert on review
DROP TRIGGER IF EXISTS review_after_insert;
DELIMITER //
CREATE TRIGGER review_after_insert
AFTER INSERT ON review
FOR EACH ROW
BEGIN
    UPDATE product
    SET average_rating = ROUND((SELECT AVG(rating) FROM review WHERE product_id = NEW.product_id), 2)
    WHERE product_id = NEW.product_id;
END//
DELIMITER ;

-- Trigger: check stock and decrement on insert into order_item
DROP TRIGGER IF EXISTS order_item_before_insert;
DELIMITER //
CREATE TRIGGER order_item_before_insert
BEFORE INSERT ON order_item
FOR EACH ROW
BEGIN
    DECLARE current_stock INT DEFAULT 0;
    SELECT stock_qty INTO current_stock FROM product WHERE product_id = NEW.product_id FOR UPDATE;
    IF current_stock IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Product does not exist';
    ELSEIF current_stock < NEW.qty THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient stock';
    ELSE
        UPDATE product SET stock_qty = stock_qty - NEW.qty WHERE product_id = NEW.product_id;
    END IF;
END//
DELIMITER ;

-- Trigger: insert tracking row when order status changes
DROP TRIGGER IF EXISTS orders_after_update;
DELIMITER //
CREATE TRIGGER orders_after_update
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
    IF NEW.status <> OLD.status THEN
        INSERT INTO order_tracking(order_id, status, changed_at) VALUES (NEW.order_id, NEW.status, NOW());
    END IF;
END//
DELIMITER ;

-- Stored procedure: create order from cart (transactional)
DROP PROCEDURE IF EXISTS sp_create_order_from_cart;
DELIMITER //
CREATE PROCEDURE sp_create_order_from_cart(
    IN p_cart_id INT,
    IN p_account_id INT,
    IN p_payment_method_id INT
)
BEGIN
    DECLARE v_order_id INT DEFAULT 0;
    DECLARE v_total DECIMAL(12,2) DEFAULT 0.00;
    DECLARE v_order_number VARCHAR(100);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SELECT NULL AS order_id, 'error' AS status;
    END;

    START TRANSACTION;

    INSERT INTO orders(account_id, status, placed_at)
    VALUES (p_account_id, 'processing', NOW());
    SET v_order_id = LAST_INSERT_ID();

    SET v_order_number = CONCAT('ORD-', DATE_FORMAT(NOW(), '%y%m%d'), '-', v_order_id);
    UPDATE orders SET order_number = v_order_number WHERE order_id = v_order_id;

    INSERT INTO order_item(order_id, product_id, qty, unit_price_at_purchase, line_total)
    SELECT v_order_id, ci.product_id, ci.quantity, p.unit_price, (ci.quantity * p.unit_price)
    FROM cart_item ci
    JOIN product p ON p.product_id = ci.product_id
    WHERE ci.cart_id = p_cart_id;

    SELECT IFNULL(SUM(line_total), 0) INTO v_total FROM order_item WHERE order_id = v_order_id;
    UPDATE orders SET total_amount = v_total WHERE order_id = v_order_id;

    INSERT INTO payment(order_id, payment_method_id, amount, paid_at)
    VALUES (v_order_id, p_payment_method_id, v_total, NOW());

    DELETE FROM cart_item WHERE cart_id = p_cart_id;
    UPDATE cart SET status = 'ordered', updated_at = NOW() WHERE cart_id = p_cart_id;

    COMMIT;

    SELECT v_order_id AS order_id;
END//
DELIMITER ;
