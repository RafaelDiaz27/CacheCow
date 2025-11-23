-- Code for the schema of our database

SET SQL_MODE = 'TRADITIONAL';
SET FOREIGN_KEY_CHECKS = 1;

-- ACCOUNT
CREATE TABLE IF NOT EXISTS account (
    account_id        INT AUTO_INCREMENT PRIMARY KEY,
    email             VARCHAR(255) UNIQUE NOT NULL,
    phone             VARCHAR(50),
    password_hash     VARCHAR(255) NOT NULL,
    first_name        VARCHAR(100),
    last_name         VARCHAR(100),
    role              VARCHAR(50) DEFAULT 'customer',
    points_balance    INT DEFAULT 0,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ADDRESS
CREATE TABLE IF NOT EXISTS address (
    address_id        INT AUTO_INCREMENT PRIMARY KEY,
    account_id        INT,
    line_1            VARCHAR(255),
    city              VARCHAR(100),
    province_state    VARCHAR(100),
    postal_code       VARCHAR(30),
    country           VARCHAR(100),
    is_default_shipping BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (account_id) REFERENCES account(account_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- CATEGORY
CREATE TABLE IF NOT EXISTS category (
    category_id       INT AUTO_INCREMENT PRIMARY KEY,
    name              VARCHAR(150) NOT NULL,
    description       TEXT
) ENGINE=InnoDB;

-- PRODUCT
CREATE TABLE IF NOT EXISTS product (
    product_id        INT AUTO_INCREMENT PRIMARY KEY,
    category_id       INT,
    name              VARCHAR(255) NOT NULL,
    description       TEXT,
    unit_price        DECIMAL(10,2) NOT NULL DEFAULT 0,
    stock_qty         INT NOT NULL DEFAULT 0,
    is_active         BOOLEAN DEFAULT TRUE,
    average_rating    DECIMAL(3,2) DEFAULT 0,
    FOREIGN KEY (category_id) REFERENCES category(category_id)
) ENGINE=InnoDB;

CREATE INDEX idx_product_name ON product(name);
CREATE INDEX idx_product_category ON product(category_id);

-- REVIEW
CREATE TABLE IF NOT EXISTS review (
    review_id         INT AUTO_INCREMENT PRIMARY KEY,
    product_id        INT,
    account_id        INT,
    rating            SMALLINT CHECK (rating >= 1 AND rating <= 5),
    title             VARCHAR(255),
    body              TEXT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES product(product_id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES account(account_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- SESSION (for guest carts)
CREATE TABLE IF NOT EXISTS session (
    session_id        CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    account_id        INT,
    session_token     VARCHAR(255) UNIQUE,
    is_guest          BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES account(account_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- CART
CREATE TABLE IF NOT EXISTS cart (
    cart_id           INT AUTO_INCREMENT PRIMARY KEY,
    account_id        INT,
    session_id        CHAR(36),
    status            VARCHAR(50) DEFAULT 'active',
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES account(account_id),
    FOREIGN KEY (session_id) REFERENCES session(session_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- CART_ITEM
CREATE TABLE IF NOT EXISTS cart_item (
    cart_item_id      INT AUTO_INCREMENT PRIMARY KEY,
    cart_id           INT,
    product_id        INT,
    quantity          INT NOT NULL,
    added_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_cart_product (cart_id, product_id),
    FOREIGN KEY (cart_id) REFERENCES cart(cart_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES product(product_id)
) ENGINE=InnoDB;

-- ORDERS
CREATE TABLE IF NOT EXISTS orders (
    order_id          INT AUTO_INCREMENT PRIMARY KEY,
    account_id        INT,
    postal_code       VARCHAR(30),
    total_amount      DECIMAL(12,2) DEFAULT 0,
    placed_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status            VARCHAR(50) DEFAULT 'pending',
    order_number      VARCHAR(50) UNIQUE,
    province          VARCHAR(100),
    line_1            VARCHAR(255),
    city              VARCHAR(100),
    country           VARCHAR(100),
    FOREIGN KEY (account_id) REFERENCES account(account_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ORDER_ITEM
CREATE TABLE IF NOT EXISTS order_item (
    order_item_id     INT AUTO_INCREMENT PRIMARY KEY,
    order_id          INT,
    product_id        INT,
    qty               INT NOT NULL,
    unit_price_at_purchase DECIMAL(10,2) NOT NULL,
    line_total        DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES product(product_id)
) ENGINE=InnoDB;

-- ORDER_TRACKING
CREATE TABLE IF NOT EXISTS order_tracking (
    order_tracking_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id          INT,
    status            VARCHAR(100),
    changed_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- PAYMENT_METHOD
CREATE TABLE IF NOT EXISTS payment_method (
    payment_method_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id        INT,
    type              VARCHAR(50),
    cvv               VARCHAR(10),
    expiry_date       DATE,
    card_number_mask  VARCHAR(50),
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES account(account_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- PAYMENT
CREATE TABLE IF NOT EXISTS payment (
    payment_id        INT AUTO_INCREMENT PRIMARY KEY,
    order_id          INT,
    payment_method_id INT,
    amount            DECIMAL(12,2),
    paid_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (payment_method_id) REFERENCES payment_method(payment_method_id)
) ENGINE=InnoDB;

-- Useful view: order_summary
DROP VIEW IF EXISTS vw_order_summary;
CREATE VIEW vw_order_summary AS
SELECT o.order_id, o.order_number, o.account_id, o.total_amount, o.placed_at, o.status,
       COUNT(oi.order_item_id) AS items_count
FROM orders o
LEFT JOIN order_item oi ON oi.order_id = o.order_id
GROUP BY o.order_id;
