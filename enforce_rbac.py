import re

with open('api/main.py', 'r') as f:
    content = f.read()

# Endpoints to secure with require_admin=True
admin_endpoints = [
    'update_company',
    'get_company_users',
    'create_company_user',
    'delete_company_user',
    'get_bank_accounts',
    'create_bank_account',
    'create_payment_method',
    'create_branch'
]

# Simple state machine to find the endpoint and replace its verify_company_access call
lines = content.split('\n')
in_admin_endpoint = False
for i, line in enumerate(lines):
    if line.startswith('def '):
        func_name = re.search(r'def (\w+)\(', line).group(1)
        if func_name in admin_endpoints:
            in_admin_endpoint = True
        else:
            in_admin_endpoint = False
            
    if in_admin_endpoint and 'verify_company_access(current_user,' in line:
        # Avoid replacing if already has require_admin=True
        if 'require_admin=True' not in line:
            lines[i] = line.replace(')', ', require_admin=True)')
            in_admin_endpoint = False # Replaced for this endpoint

# Also fix upload_logo
for i, line in enumerate(lines):
    if 'if not current_user.get("is_global_admin"):' in line and 'upload_logo' in '\n'.join(lines[max(0, i-5):i]):
        lines[i] = '    if not current_user.get("is_global_admin") and current_user.get("role") != "admin":'

with open('api/main.py', 'w') as f:
    f.write('\n'.join(lines))
