import re
import json

def parse_functions(code: str):
    """
    Parses a C++ header/source string for function/method declarations and returns 
    a list of dictionaries containing:
      - name: The function/method name
      - signature: The full signature (return type + name + parameter list + modifiers)
      - parameters: List of dicts, each with 'type' and 'name'
      - return_type: The return type of the function
    """
    # Remove single line comments
    code_clean = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
    
    # Remove block comments
    code_clean = re.sub(r'/\*.*?\*/', '', code_clean, flags=re.DOTALL)
    
    # Remove annotations/macros like UFUNCTION(...), UPROPERTY(...)
    code_clean = re.sub(r'\b[A-Z0-9_]+\s*\([^)]*\)', '', code_clean)
    
    # Regex to match function declarations/definitions
    # It looks for: [return_type] [name]([params]) [const/override/etc...] [; or {]
    # We want to be careful with spaces, pointers, references, and nested templates.
    # Note: This pattern assumes standard C++ declaration style.
    pattern = re.compile(
        r'(?P<return_type>[\w::<>\*&\s]+?)\s+'
        r'(?P<name>\w+)\s*'
        r'\((?P<params>[^)]*)\)'
        r'(?P<modifiers>[\s\w]*)(?=\s*[{;])'
    )
    
    functions = []
    
    # Find all matches
    for match in pattern.finditer(code_clean):
        gd = match.groupdict()
        
        # Clean up return type
        ret_type = re.sub(r'\s+', ' ', gd['return_type']).strip()
        
        # Skip control flow structures that look like functions
        if ret_type in ('if', 'while', 'for', 'switch', 'catch') or gd['name'] in ('if', 'while', 'for', 'switch', 'catch', 'void'):
            continue
            
        params_str = gd['params'].strip()
        parameters = []
        
        if params_str and params_str.lower() != 'void':
            # Split parameters by comma, taking care not to split inside template brackets like TMap<FString, int32>
            # Let's write a simple nested bracket parser for parameter splitting
            raw_params = []
            current_param = []
            bracket_level = 0
            for char in params_str:
                if char == '<':
                    bracket_level += 1
                elif char == '>':
                    bracket_level -= 1
                
                if char == ',' and bracket_level == 0:
                    raw_params.append(''.join(current_param).strip())
                    current_param = []
                else:
                    current_param.append(char)
            if current_param:
                raw_params.append(''.join(current_param).strip())
                
            for p in raw_params:
                if not p:
                    continue
                # Split type and name. Usually the last word is the variable name.
                # Special cases: pointers or references attached to name, e.g. int* x or int &x, default values.
                # Let's clean up default values first: "int32 X = 0" -> "int32 X"
                p_clean = p.split('=')[0].strip()
                
                # Split by space
                parts = p_clean.split()
                if not parts:
                    continue
                
                if len(parts) == 1:
                    # Only type is specified, e.g. (int)
                    parameters.append({'type': parts[0], 'name': ''})
                else:
                    # The last part is likely the name, everything before is the type
                    # Keep in mind if it's like "const FString& Name"
                    param_name = parts[-1]
                    # If name starts with * or &, strip it and attach to type
                    while param_name and param_name[0] in ('*', '&'):
                        parts[-2] += param_name[0]
                        param_name = param_name[1:]
                    
                    param_type = ' '.join(parts[:-1]).strip()
                    parameters.append({'type': param_type, 'name': param_name})
                    
        # Reconstruct clean signature
        modifiers = re.sub(r'\s+', ' ', gd['modifiers']).strip()
        sig = f"{ret_type} {gd['name']}({params_str})"
        if modifiers:
            sig += f" {modifiers}"
            
        functions.append({
            'name': gd['name'],
            'signature': sig,
            'parameters': parameters,
            'return_type': ret_type
        })
        
    return functions

# Test cases
test_code = """
UFUNCTION(BlueprintCallable, Category = "Vehicle")
virtual void InitializeHUD(APlayerController* PlayerController);

UFUNCTION(BlueprintCallable)
TMap<FString, int32> GetScores(const FString& TeamName, int32 MinScore = 10) const;

// This is a comment
void SimpleFunc();

/* Block comment 
   void CommentedFunc(); 
*/
int* GetPointer(const int& RefVal);
"""

print(json.dumps(parse_functions(test_code), indent=2))
