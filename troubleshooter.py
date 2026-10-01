

import sys
import traceback
import inspect

def analyze_block(exception: Exception = None, local_vars: dict = None):
    """
    Call this when your code hits a brick wall.
    It extracts the broken line, the file name, and looks inside your variables.
    """
    analysis = []
    analysis.append("\n=== TROUBLESHOOTING REPORT ===")
   
    # 1. Capture the exact line of code that failed
    exc_type, exc_value, exc_tb = sys.exc_info()
    if exc_tb:
        frames = traceback.extract_tb(exc_tb)
        last_frame = frames[-1]
        analysis.append(f"📍 Location: File '{last_frame.filename}', Line {last_frame.lineno}")
        analysis.append(f"🛠️ Code Block: {last_frame.line}")
   
    # 2. Identify the exact error reason
    if exception:
        analysis.append(f"💥 Error Type: {type(exception).__name__}")
        analysis.append(f"📝 Reason: {str(exception)}")
   
    # 3. Inspect local variable values at the exact moment of failure
    if local_vars:
        analysis.append("\n=== SNAPSHOT OF LOCAL STORAGE ===")
        for var_name, var_value in local_vars.items():
            if not var_name.startswith('__') and not inspect.ismodule(var_value):
                val_str = str(var_value)
                if len(val_str) > 100:
                    val_str = val_str[:100] + "... [Truncated]"
                analysis.append(f" -> {var_name} = {val_str} (Type: {type(var_value).__name__})")
               
    analysis.append("==============================\n")
    return "\n".join(analysis)

 

def global_crash_handler(exc_type, exc_value, tb):
    """Automatically intercepts any crash in your project without needing code indentation."""
    import sys
    # Generate the troubleshooting report using the logic above
    report = analyze_block(exc_value, None)
   
    # Save it safely to your hard drive
    with open("crash_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
       
    print(report)
    # Pass back to default Python behavior so it cleanly exits
    sys.__excepthook__(exc_type, exc_value, tb)

# Hook it up to the entire Python process running this folder
sys.excepthook = global_crash_handler

 

