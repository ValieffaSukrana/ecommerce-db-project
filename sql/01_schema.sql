-- =====================================================================
-- Elektron ticarət verilənlər bazası — sxem (DDL)
-- PostgreSQL 16
-- =====================================================================

DROP TABLE IF EXISTS payments    CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders      CASCADE;
DROP TABLE IF EXISTS products    CASCADE;
DROP TABLE IF EXISTS customers   CASCADE;
DROP TABLE IF EXISTS categories  CASCADE;

-- 1. Kateqoriyalar --------------------------------------------------------
CREATE TABLE categories (
    category_id    INTEGER      PRIMARY KEY,
    category_name  VARCHAR(100) NOT NULL UNIQUE
);

-- 2. Müştərilər ----------------------------------------------------------
CREATE TABLE customers (
    customer_id        INTEGER      PRIMARY KEY,
    first_name         VARCHAR(50)  NOT NULL,
    last_name          VARCHAR(50)  NOT NULL,
    gender             CHAR(1)      CHECK (gender IN ('M', 'F')),
    birth_date         DATE,
    email              VARCHAR(150) UNIQUE,
    phone              VARCHAR(20),
    city               VARCHAR(50)  NOT NULL,
    registration_date  DATE         NOT NULL
);

-- 3. Məhsullar -----------------------------------------------------------
CREATE TABLE products (
    product_id      INTEGER       PRIMARY KEY,
    product_name    VARCHAR(200)  NOT NULL,
    category_id     INTEGER       NOT NULL
                    REFERENCES categories (category_id) ON UPDATE CASCADE,
    brand           VARCHAR(100),
    unit_price      NUMERIC(10,2) NOT NULL CHECK (unit_price > 0),
    stock_quantity  INTEGER       NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    created_at      DATE
);

-- 4. Sifarişlər ----------------------------------------------------------
CREATE TABLE orders (
    order_id       INTEGER       PRIMARY KEY,
    customer_id    INTEGER       NOT NULL
                   REFERENCES customers (customer_id) ON DELETE RESTRICT,
    order_date     TIMESTAMP     NOT NULL,
    status         VARCHAR(20)   NOT NULL
                   CHECK (status IN ('delivered','shipped','processing','cancelled','returned')),
    shipping_city  VARCHAR(50)   NOT NULL,
    total_amount   NUMERIC(12,2) NOT NULL CHECK (total_amount >= 0)
);

-- 5. Sifariş sətirləri (orders <-> products, çox-çoxa əlaqə) --------------
CREATE TABLE order_items (
    order_item_id  INTEGER       PRIMARY KEY,
    order_id       INTEGER       NOT NULL
                   REFERENCES orders (order_id) ON DELETE CASCADE,
    product_id     INTEGER       NOT NULL
                   REFERENCES products (product_id),
    quantity       INTEGER       NOT NULL CHECK (quantity > 0),
    unit_price     NUMERIC(10,2) NOT NULL CHECK (unit_price > 0),
    discount       NUMERIC(4,2)  NOT NULL DEFAULT 0 CHECK (discount BETWEEN 0 AND 1),
    line_total     NUMERIC(12,2) NOT NULL,
    UNIQUE (order_id, product_id)
);

-- 6. Ödənişlər (orders ilə 1:1) -------------------------------------------
CREATE TABLE payments (
    payment_id      INTEGER       PRIMARY KEY,
    order_id        INTEGER       NOT NULL UNIQUE
                    REFERENCES orders (order_id) ON DELETE CASCADE,
    payment_date    TIMESTAMP     NOT NULL,
    payment_method  VARCHAR(30)   NOT NULL,
    amount          NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    payment_status  VARCHAR(20)   NOT NULL
                    CHECK (payment_status IN ('completed','failed','refunded'))
);

-- İndekslər (xarici açarlar və tez-tez filtr olunan sütunlar) --------------
CREATE INDEX idx_products_category   ON products    (category_id);
CREATE INDEX idx_orders_customer     ON orders      (customer_id);
CREATE INDEX idx_orders_date         ON orders      (order_date);
CREATE INDEX idx_orders_status       ON orders      (status);
CREATE INDEX idx_order_items_order   ON order_items (order_id);
CREATE INDEX idx_order_items_product ON order_items (product_id);
CREATE INDEX idx_payments_method     ON payments    (payment_method);
