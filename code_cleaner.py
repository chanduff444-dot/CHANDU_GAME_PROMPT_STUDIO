import re

def clean_ai_code(raw_output):
    text = raw_output
    text = re.sub(r"```python", "", text)
    text = re.sub(r"```", "", text)
    lines = text.splitlines()
    code_lines = []
    in_code = False
    skip = ("here", "this", "below", "note:", "sure", "certainly", "i will", "let me")
    for line in lines:
        s = line.strip().lower()
        if not in_code and s == "": continue
        if any(s.startswith(p) for p in skip): continue
        if s.startswith(("import ", "from ", "bpy", "#", "def ", "class ")): in_code = True
        if in_code: code_lines.append(line)
    result = "\n".join(code_lines).strip()
    return result if result else text.strip()

def validate_code(code):
    """Validate code syntax and check for common Blender API errors."""
    # Syntax check
    try:
        compile(code, "<ai_generated>", "exec")
    except SyntaxError as e:
        return False, str(e)
    
    # Common Blender API error patterns
    warnings = []
    
    # Check for invalid operator parameters
    if re.search(r'bpy\.ops\.\w+\.add\([^)]*size=', code):
        if not re.search(r'mesh\.primitive.*size=', code):
            warnings.append("WARNING: 'size' parameter may be invalid for this operator")
    
    # Check for accessing attributes on None
    if '.horizon_color' in code or '.metrics' in code:
        warnings.append("WARNING: Attempting to access invalid Blender attributes")
    
    # Check for uninitialized object access
    if 'obj.data.materials' in code and 'bpy.context.active_object' not in code.split('obj.data.materials')[0]:
        warnings.append("INFO: Ensure active object is set before accessing obj.data")
    
    if warnings:
        return True, "\n".join(warnings)  # Return True but include warnings
    
    return True, None