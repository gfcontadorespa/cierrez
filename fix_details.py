with open('frontend/src/pages/CierreZDetails.tsx', 'r') as f:
    content = f.read()

content = content.replace(
    'tax_amount: number;',
    'tax_amount: number;\n  credit_notes: number;'
)

content = content.replace(
    '<p className="text-sm font-medium text-slate-900">${cierre.tax_amount?.toFixed(2)}</p>\n              </div>\n            </div>',
    '<p className="text-sm font-medium text-slate-900">${cierre.tax_amount?.toFixed(2)}</p>\n              </div>\n              <div>\n                <p className="text-xs text-slate-500">Notas de Crédito</p>\n                <p className="text-sm font-medium text-red-600">${cierre.credit_notes?.toFixed(2)}</p>\n              </div>\n            </div>'
)

with open('frontend/src/pages/CierreZDetails.tsx', 'w') as f:
    f.write(content)
