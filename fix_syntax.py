import re

with open('api/main.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('def ') and 'current_user: dict = Depends(get_current_user)' in line:
        # Extract the arguments inside def name(...)
        match = re.search(r'def \w+\((.*)\):', line)
        if match:
            args_str = match.group(1)
            args = [arg.strip() for arg in args_str.split(',')]
            
            # Remove current_user from the middle
            new_args = []
            has_current_user = False
            for arg in args:
                if 'current_user: dict = Depends(get_current_user)' in arg:
                    has_current_user = True
                else:
                    if arg:
                        new_args.append(arg)
            
            if has_current_user:
                new_args.append('current_user: dict = Depends(get_current_user)')
            
            new_args_str = ', '.join(new_args)
            line = line.replace(args_str, new_args_str)
    
    new_lines.append(line)

with open('api/main.py', 'w') as f:
    f.writelines(new_lines)
