-- =============================================================================
-- SAP SmartSupply AI — PostgreSQL Schema (Phase 2) — corrected to match
-- actual generated CSV columns.
-- =============================================================================

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id             VARCHAR(50) PRIMARY KEY,
    supplier_name           VARCHAR(255),
    supplier_category       VARCHAR(100),
    country                 VARCHAR(100),
    city                    VARCHAR(100),
    lead_time_days          INTEGER,
    defect_rate             NUMERIC(10,4),
    on_time_delivery_rate   NUMERIC(6,2),
    supplier_rating         NUMERIC(6,2),
    risk_score              NUMERIC(6,3)
);

CREATE TABLE IF NOT EXISTS products (
    product_id      VARCHAR(50) PRIMARY KEY,
    product_name    VARCHAR(255),
    category        VARCHAR(100),
    brand           VARCHAR(100),
    unit_cost       NUMERIC(12,2),
    unit_price      NUMERIC(12,2) CHECK (unit_price >= 0),
    supplier_id     VARCHAR(50) REFERENCES suppliers(supplier_id),
    lead_time_days  INTEGER,
    reorder_point   INTEGER,
    safety_stock    INTEGER,
    created_at      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id        VARCHAR(50) PRIMARY KEY,
    warehouse_name      VARCHAR(255),
    city                VARCHAR(100),
    state               VARCHAR(100),
    capacity            INTEGER,
    utilized_capacity   INTEGER,
    manager_name        VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id     VARCHAR(50) PRIMARY KEY,
    product_id       VARCHAR(50) REFERENCES products(product_id),
    warehouse_id     VARCHAR(50) REFERENCES warehouses(warehouse_id),
    stock_on_hand    INTEGER CHECK (stock_on_hand >= 0),
    stock_reserved   INTEGER,
    available_stock  INTEGER,
    last_updated     TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sales (
    order_id         VARCHAR(50) PRIMARY KEY,
    order_date       DATE,
    product_id       VARCHAR(50) REFERENCES products(product_id),
    warehouse_id     VARCHAR(50) REFERENCES warehouses(warehouse_id),
    customer_region  VARCHAR(100),
    quantity         INTEGER CHECK (quantity > 0),
    unit_price       NUMERIC(12,2),
    revenue          NUMERIC(12,2),
    promotion_flag   BOOLEAN
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    po_id                    VARCHAR(50) PRIMARY KEY,
    supplier_id              VARCHAR(50) REFERENCES suppliers(supplier_id),
    product_id               VARCHAR(50) REFERENCES products(product_id),
    warehouse_id             VARCHAR(50) REFERENCES warehouses(warehouse_id),
    quantity                 INTEGER,
    order_date               DATE,
    expected_delivery_date   DATE,
    actual_delivery_date     DATE,
    status                   VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS defects (
    defect_id        VARCHAR(50) PRIMARY KEY,
    product_id       VARCHAR(50) REFERENCES products(product_id),
    supplier_id      VARCHAR(50) REFERENCES suppliers(supplier_id),
    warehouse_id     VARCHAR(50) REFERENCES warehouses(warehouse_id),
    defect_type      VARCHAR(100),
    defect_count     INTEGER CHECK (defect_count > 0),
    inspection_date  DATE,
    severity         VARCHAR(20)
);

CREATE INDEX IF NOT EXISTS idx_sales_product_date ON sales(product_id, order_date);
CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_warehouse ON inventory(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_po_product ON purchase_orders(product_id);
CREATE INDEX IF NOT EXISTS idx_defects_product ON defects(product_id);