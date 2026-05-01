import re

with open('api/main.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    
    # Inject verify_company_access right after the try: block for relevant endpoints
    if line.strip() == "try:" and i > 0:
        prev_line = lines[i-1]
        
        # Check if it's an endpoint that receives company_id
        if "company_id: int" in prev_line or "company: CompanyCreate" in prev_line or "cierre: CierreCreate" in prev_line or "user: UserCreate" in prev_line or "branch: BranchCreate" in prev_line or "payment_method: PaymentMethodCreate" in prev_line or "bank_account: BankAccountCreate" in prev_line:
            
            # Figure out the variable name for company_id
            indent = line[:len(line) - len(line.lstrip())] + "    "
            
            if "company_id: int" in prev_line:
                if "get_cierres" not in prev_line: # get_cierres is already handled
                    new_lines.append(f"{indent}if company_id:\n{indent}    verify_company_access(current_user, company_id)\n")
            elif "company: CompanyCreate" in prev_line:
                pass # Can't verify on creation if they don't belong yet, or maybe only global admin can?
            elif "cierre: CierreCreate" in prev_line:
                new_lines.append(f"{indent}verify_company_access(current_user, cierre.company_id)\n")
            elif "user: UserCreate" in prev_line:
                new_lines.append(f"{indent}verify_company_access(current_user, user.company_id)\n")
            elif "branch: BranchCreate" in prev_line:
                new_lines.append(f"{indent}verify_company_access(current_user, branch.company_id)\n")
            elif "payment_method: PaymentMethodCreate" in prev_line:
                new_lines.append(f"{indent}verify_company_access(current_user, payment_method.company_id)\n")
            elif "bank_account: BankAccountCreate" in prev_line:
                new_lines.append(f"{indent}verify_company_access(current_user, bank_account.company_id)\n")

with open('api/main.py', 'w') as f:
    f.writelines(new_lines)
