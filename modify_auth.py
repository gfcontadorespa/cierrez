import re

with open('api/main.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    # Regex to match route definitions like `def get_cierres(company_id: int | None = None):`
    # and we want to inject `current_user: dict = Depends(get_current_user)` into the arguments.
    
    # Let's do this more safely by replacing specific function definitions
    
    if line.startswith('def get_metrics('):
        line = line.replace('def get_metrics(company_id: int | None = None', 'def get_metrics(company_id: int | None = None, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def get_companies('):
        line = line.replace('def get_companies(', 'def get_companies(current_user: dict = Depends(get_current_user)')
    elif line.startswith('def create_company('):
        line = line.replace('def create_company(company: CompanyCreate', 'def create_company(company: CompanyCreate, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def update_company('):
        line = line.replace('def update_company(company_id: int', 'def update_company(company_id: int, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def get_company_users('):
        line = line.replace('def get_company_users(company_id: int', 'def get_company_users(company_id: int, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def create_company_user('):
        line = line.replace('def create_company_user(company_id: int', 'def create_company_user(company_id: int, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def delete_company_user('):
        line = line.replace('def delete_company_user(company_id: int', 'def delete_company_user(company_id: int, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def get_bank_accounts('):
        line = line.replace('def get_bank_accounts(company_id: int | None = None', 'def get_bank_accounts(company_id: int | None = None, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def create_bank_account('):
        line = line.replace('def create_bank_account(bank_account: BankAccountCreate', 'def create_bank_account(bank_account: BankAccountCreate, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def get_payment_methods('):
        line = line.replace('def get_payment_methods(company_id: int | None = None', 'def get_payment_methods(company_id: int | None = None, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def create_payment_method('):
        line = line.replace('def create_payment_method(payment_method: PaymentMethodCreate', 'def create_payment_method(payment_method: PaymentMethodCreate, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def get_users('):
        line = line.replace('def get_users(', 'def get_users(current_user: dict = Depends(get_current_user)')
    elif line.startswith('def create_user('):
        line = line.replace('def create_user(user: UserCreate', 'def create_user(user: UserCreate, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def get_cierres('):
        line = line.replace('def get_cierres(company_id: int | None = None', 'def get_cierres(company_id: int | None = None, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def create_cierre('):
        line = line.replace('def create_cierre(cierre: CierreCreate', 'def create_cierre(cierre: CierreCreate, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def get_cierre('):
        line = line.replace('def get_cierre(cierre_id: int', 'def get_cierre(cierre_id: int, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def get_branches('):
        line = line.replace('def get_branches(company_id: int | None = None', 'def get_branches(company_id: int | None = None, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def create_branch('):
        line = line.replace('def create_branch(branch: BranchCreate', 'def create_branch(branch: BranchCreate, current_user: dict = Depends(get_current_user)')
    elif line.startswith('async def upload_receipt('):
        line = line.replace('async def upload_receipt(file: UploadFile = File(...)', 'async def upload_receipt(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)')
    elif line.startswith('async def upload_logo('):
        line = line.replace('async def upload_logo(file: UploadFile = File(...)', 'async def upload_logo(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)')
    elif line.startswith('def update_cierre_status('):
        line = line.replace('def update_cierre_status(cierre_id: int, status_update: CierreStatusUpdate', 'def update_cierre_status(cierre_id: int, status_update: CierreStatusUpdate, current_user: dict = Depends(get_current_user)')
    elif line.startswith('def download_cierre_pdf('):
        line = line.replace('def download_cierre_pdf(cierre_id: int', 'def download_cierre_pdf(cierre_id: int, current_user: dict = Depends(get_current_user)')

    new_lines.append(line)

with open('api/main.py', 'w') as f:
    f.writelines(new_lines)
