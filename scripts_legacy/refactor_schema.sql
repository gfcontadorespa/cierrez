-- 1. Tablas Multi-tenant base

CREATE TABLE IF NOT EXISTS tbl_companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    ruc VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tbl_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255),
    name VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tbl_company_users (
    company_id INTEGER REFERENCES tbl_companies(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES tbl_users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'user', -- 'admin', 'manager', 'user'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (company_id, user_id)
);

-- 2. Tablas de Métodos de Pago (Mantenimiento y Detalle)

CREATE TABLE IF NOT EXISTS tbl_payment_methods (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES tbl_companies(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, -- Ej: Efectivo, Yappy, Clave
    account_code VARCHAR(100),  -- Ej: 1.0.0.1, para la contabilidad
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tbl_cierre_payments (
    id SERIAL PRIMARY KEY,
    cierre_id TEXT REFERENCES tblcierresz(row_id) ON DELETE CASCADE,
    payment_method_id INTEGER REFERENCES tbl_payment_methods(id) ON DELETE RESTRICT,
    amount NUMERIC NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Modificaciones a Tablas Existentes para soportar Multi-tenant
-- Se utiliza ALTER TABLE de manera idempotente añadiendo columnas si no existen (requiere PL/pgSQL o se asume que no existen en la primera corrida)

DO $$ 
BEGIN
    -- Añadir company_id a tblsucursales
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tblsucursales' AND column_name='company_id') THEN
        ALTER TABLE tblsucursales ADD COLUMN company_id INTEGER REFERENCES tbl_companies(id) ON DELETE CASCADE;
    END IF;

    -- Añadir company_id a tblcierresz
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tblcierresz' AND column_name='company_id') THEN
        ALTER TABLE tblcierresz ADD COLUMN company_id INTEGER REFERENCES tbl_companies(id) ON DELETE CASCADE;
    END IF;

    -- Añadir company_id a tbl_depositos
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tbl_depositos' AND column_name='company_id') THEN
        ALTER TABLE tbl_depositos ADD COLUMN company_id INTEGER REFERENCES tbl_companies(id) ON DELETE CASCADE;
    END IF;

END $$;

-- NOTA: Por ahora NO borramos las columnas originales de pagos (efectivo, yappy, etc.) de tblcierresz 
-- para evitar pérdida de datos. Podremos hacer un script de migración de datos más adelante si el usuario lo desea.
