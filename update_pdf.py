import re

with open('api/pdf_generator.py', 'r') as f:
    content = f.read()

# The PDF generator prints:
# f"Ventas Gravables: ${cierre.get('taxable_sales', 0):.2f}",
# f"Ventas Exentas: ${cierre.get('exempt_sales', 0):.2f}",
# f"Impuesto (ITBMS): ${cierre.get('tax_amount', 0):.2f}",
# f"Ventas Totales: ${cierre.get('total_sales', 0):.2f}"

replacement = """f"Ventas Exentas: ${cierre.get('exempt_sales', 0):.2f}",
        f"Impuesto (ITBMS): ${cierre.get('tax_amount', 0):.2f}",
        f"Notas de Crédito: ${cierre.get('credit_notes', 0):.2f}",
        f"Ventas Totales: ${cierre.get('total_sales', 0):.2f}","""

content = content.replace("""f"Ventas Exentas: ${cierre.get('exempt_sales', 0):.2f}",
        f"Impuesto (ITBMS): ${cierre.get('tax_amount', 0):.2f}",
        f"Ventas Totales: ${cierre.get('total_sales', 0):.2f}",""", replacement)

with open('api/pdf_generator.py', 'w') as f:
    f.write(content)
