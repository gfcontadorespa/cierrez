DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tbl_users' AND column_name='is_global_admin') THEN
        ALTER TABLE tbl_users ADD COLUMN is_global_admin BOOLEAN DEFAULT FALSE;
    END IF;
END $$;
