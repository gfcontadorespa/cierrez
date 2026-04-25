-- Agregar columnas de auditoría a tblcierresz
ALTER TABLE tblcierresz 
ADD COLUMN IF NOT EXISTS audit_pos_visa_mc NUMERIC,
ADD COLUMN IF NOT EXISTS audit_pos_clave NUMERIC,
ADD COLUMN IF NOT EXISTS audit_diff_visa_mc NUMERIC,
ADD COLUMN IF NOT EXISTS audit_diff_clave NUMERIC;

COMMENT ON COLUMN tblcierresz.audit_pos_visa_mc IS 'Monto Visa/MC extraído por IA';
COMMENT ON COLUMN tblcierresz.audit_pos_clave IS 'Monto Clave extraído por IA';
COMMENT ON COLUMN tblcierresz.audit_diff_visa_mc IS 'Diferencia Visa/MC (AppSheet - IA)';
COMMENT ON COLUMN tblcierresz.audit_diff_clave IS 'Diferencia Clave (AppSheet - IA)';
