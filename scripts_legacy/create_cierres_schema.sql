CREATE TABLE IF NOT EXISTS tbl_cierres_z_master (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES tbl_companies(id) ON DELETE CASCADE,
    branch_id INTEGER, -- Lo dejamos sin FK estricto temporalmente hasta implementar sucursales completas
    z_number VARCHAR(100) NOT NULL,
    date_closed DATE NOT NULL,
    taxable_sales DECIMAL(12, 2) DEFAULT 0.00,
    exempt_sales DECIMAL(12, 2) DEFAULT 0.00,
    tax_amount DECIMAL(12, 2) DEFAULT 0.00,
    total_sales DECIMAL(12, 2) DEFAULT 0.00,
    total_receipt DECIMAL(12, 2) DEFAULT 0.00,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by INTEGER REFERENCES tbl_users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS tbl_cierre_payments_detail (
    id SERIAL PRIMARY KEY,
    cierre_id INTEGER REFERENCES tbl_cierres_z_master(id) ON DELETE CASCADE,
    payment_method_id INTEGER REFERENCES tbl_payment_methods(id) ON DELETE RESTRICT,
    amount DECIMAL(12, 2) NOT NULL
);
