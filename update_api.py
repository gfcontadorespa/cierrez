with open('api/main.py', 'r') as f:
    content = f.read()

# 1. Update CierreCreate model
content = content.replace(
    'tax_amount: float\n    total_sales: float',
    'tax_amount: float\n    total_sales: float\n    credit_notes: float = 0.0'
)

# 2. Update get_cierres
content = content.replace(
    'taxable_sales, exempt_sales, tax_amount, total_sales, total_receipt, status, difference_amount, image_url, pos_receipt_url, deposit_receipt_url, workflow_status\n            FROM tbl_cierres_z_master',
    'taxable_sales, exempt_sales, tax_amount, total_sales, total_receipt, status, difference_amount, image_url, pos_receipt_url, deposit_receipt_url, workflow_status, credit_notes\n            FROM tbl_cierres_z_master'
)

content = content.replace(
    '"pos_receipt_url": row[13], "deposit_receipt_url": row[14], "workflow_status": row[15]}',
    '"pos_receipt_url": row[13], "deposit_receipt_url": row[14], "workflow_status": row[15], "credit_notes": float(row[16] or 0)}'
)

# 3. Update create_cierre insert statement
content = content.replace(
    '(company_id, branch_id, z_number, date_closed, taxable_sales, exempt_sales, tax_amount, total_sales, total_receipt, difference_amount, status, image_url, pos_receipt_url, deposit_receipt_url, workflow_status)',
    '(company_id, branch_id, z_number, date_closed, taxable_sales, exempt_sales, tax_amount, total_sales, total_receipt, difference_amount, status, image_url, pos_receipt_url, deposit_receipt_url, workflow_status, credit_notes)'
)
content = content.replace(
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s, %s, 'draft')\n",
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s, %s, 'draft', %s)\n"
)
content = content.replace(
    "cierre.total_receipt, cierre.difference_amount, cierre.image_url, cierre.pos_receipt_url, cierre.deposit_receipt_url))",
    "cierre.total_receipt, cierre.difference_amount, cierre.image_url, cierre.pos_receipt_url, cierre.deposit_receipt_url, cierre.credit_notes))"
)

# 4. Update get_cierre detailed view
content = content.replace(
    "taxable_sales, exempt_sales, tax_amount, total_sales, total_receipt, status, difference_amount, image_url, pos_receipt_url, deposit_receipt_url, workflow_status ",
    "taxable_sales, exempt_sales, tax_amount, total_sales, total_receipt, status, difference_amount, image_url, pos_receipt_url, deposit_receipt_url, workflow_status, credit_notes "
)

content = content.replace(
    "'pos_receipt_url': c_row[13], 'deposit_receipt_url': c_row[14], 'workflow_status': c_row[15]",
    "'pos_receipt_url': c_row[13], 'deposit_receipt_url': c_row[14], 'workflow_status': c_row[15], 'credit_notes': float(c_row[16] or 0)"
)

# 5. Add to daily report background job (pdf_generator is imported, we should also include credit_notes in the select if needed, wait, daily report uses get_cierres logic? Let's check.)
content = content.replace(
    "total_sales, total_receipt, status, difference_amount, image_url, workflow_status FROM",
    "total_sales, total_receipt, status, difference_amount, image_url, workflow_status, credit_notes FROM"
)
# For the daily report payload mapping:
content = content.replace(
    '"workflow_status": row[11]\n                }',
    '"workflow_status": row[11],\n                    "credit_notes": float(row[12] or 0)\n                }'
)

with open('api/main.py', 'w') as f:
    f.write(content)
