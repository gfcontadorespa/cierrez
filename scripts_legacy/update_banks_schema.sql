-- 1. Crear tabla de Cuentas de Banco / Caja
CREATE TABLE IF NOT EXISTS tbl_bank_accounts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES tbl_companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    account_number VARCHAR(100),
    accounting_code VARCHAR(100),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Modificar tbl_payment_methods
DO $$ 
BEGIN
    -- Añadir la nueva columna de relación con el banco/caja
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tbl_payment_methods' AND column_name='bank_account_id') THEN
        ALTER TABLE tbl_payment_methods ADD COLUMN bank_account_id INTEGER REFERENCES tbl_bank_accounts(id) ON DELETE RESTRICT;
    END IF;

    -- Eliminar la columna vieja account_code si existe (ya que ahora vive en la cuenta de banco)
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tbl_payment_methods' AND column_name='account_code') THEN
        ALTER TABLE tbl_payment_methods DROP COLUMN account_code;
    END IF;
END $$;
