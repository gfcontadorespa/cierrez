with open('frontend/src/pages/CierreZForm.tsx', 'r') as f:
    content = f.read()

content = content.replace(
    'tax_amount: parseFloat(header.tax_amount) || 0,\n        total_sales: totalSales,',
    'tax_amount: parseFloat(header.tax_amount) || 0,\n        credit_notes: parseFloat(header.credit_notes) || 0,\n        total_sales: totalSales,'
)

with open('frontend/src/pages/CierreZForm.tsx', 'w') as f:
    f.write(content)
