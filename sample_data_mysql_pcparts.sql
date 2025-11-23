-- Sample for CacheCow PC Parts Data

USE CacheCow;
SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE review;
TRUNCATE TABLE address;
TRUNCATE TABLE cart_item;
TRUNCATE TABLE order_item;
TRUNCATE TABLE orders;
TRUNCATE TABLE cart;
TRUNCATE TABLE product;
TRUNCATE TABLE account;

-- Accounts (we can fill this out later)
INSERT INTO account (email, phone, password_hash, first_name, last_name)
VALUES
('customer1@example.com', '555-111-1111', SHA2('password1',256), 'Alice', 'Smith'),
('customer2@example.com', '555-222-2222', SHA2('password2',256), 'Bob', 'Johnson'),
('customer3@example.com', '555-333-3333', SHA2('password3',256), 'Charlie', 'Lee');

-- Products
INSERT INTO product (name, description, unit_price, stock_qty, average_rating, is_active)
VALUES
('AMD Ryzen 5 7600', '6-Core 12-Thread CPU 4.8 GHz Boost', 249.99, 35, 4.8, TRUE),
('Intel Core i7-13700K', '16 Cores 24 Threads 5.4 GHz', 379.99, 28, 4.9, TRUE),
('Radeon RX 7700 XT', '12 GB GDDR6 Graphics Card', 459.99, 15, 4.7, TRUE),
('GeForce RTX 4070 SUPER', '12 GB GDDR6X Graphics Card', 599.99, 10, 4.9, TRUE),
('Corsair Vengeance DDR5 32 GB (2×16 GB)', '6000 MHz CL36 Memory Kit', 129.99, 42, 4.8, TRUE),
('Crucial P5 Plus 2 TB SSD', 'PCIe Gen4 NVMe M.2 SSD', 179.99, 27, 4.6, TRUE),
('Samsung 980 Pro 1 TB SSD', 'PCIe 4.0 NVMe M.2 7000 MB/s', 129.99, 33, 4.8, TRUE),
('NZXT H7 Flow Case (White)', 'Mid-Tower ATX Case Tempered Glass', 139.99, 18, 4.7, TRUE),
('Lian Li Lancool 216 Case (Black)', 'ATX Mid-Tower High-Airflow Design', 119.99, 20, 4.8, TRUE),
('Corsair RM850x Power Supply', '850 W 80+ Gold Fully Modular', 149.99, 25, 4.9, TRUE),
('Noctua NH-U12A CPU Cooler', '120 mm Dual-Fan Tower Cooler', 99.99, 30, 4.9, TRUE),
('Arctic P12 Case Fan (5-Pack)', '120 mm PWM Fans', 34.99, 60, 4.7, TRUE),
('ASUS TUF Gaming B650-PLUS WiFi', 'AM5 Motherboard DDR5 PCIe 5.0', 209.99, 22, 4.8, TRUE),
('MSI PRO Z790-A WiFi DDR5', 'LGA1700 Motherboard ATX Design', 259.99, 17, 4.8, TRUE),
('LG 27GP850-B Monitor', '27-inch QHD 165 Hz Nano IPS', 349.99, 12, 4.8, TRUE),
('Dell G3223Q Monitor', '32-inch 4K 144 Hz Gaming HDMI 2.1', 699.99, 8, 4.9, TRUE);

-- Cart & Items
INSERT INTO cart (account_id, status)
VALUES (1,'active'),(2,'active');

INSERT INTO cart_item (cart_id, product_id, quantity)
VALUES
(1,1,1),
(1,5,2),
(2,4,1);

SET FOREIGN_KEY_CHECKS = 1;
