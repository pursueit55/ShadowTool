

import sys
import os
import shutil
import traceback
import datetime
import ollama

# Voice configurations placeholder
_kokoro_pipeline = None
_voice_name = "af_bella"

# The folder of the script you ran. Only files inside this folder can be patched.
if sys.argv and sys.argv[0]:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(sys.argv[0]))
else:
    PROJECT_ROOT = os.getcwd()

# Errors that usually mean "something is missing", not "the code is wrong"
ENVIRONMENT_ERROR_TYPES = (FileNotFoundError, ModuleNotFoundError, PermissionError, ConnectionError)
ENVIRONMENT_HINTS = (
    "not found",
    "does not exist",
    "no such file",
    "failed to create",
    "cannot find",
    "could not find",
    "connection refused",
)


def register_voice_engine(pipeline, voice="af_bella"):
    """Call this from your main loop to link your existing Kokoro pipeline to the shadow programmer."""
    global _kokoro_pipeline, _voice_name
    _kokoro_pipeline = pipeline
    _voice_name = voice


def _speak_alert(text: str):
    """Silently passes alerts to Kokoro to read out loud."""
    global _kokoro_pipeline, _voice_name
    if _kokoro_pipeline:
        try:
            import sounddevice as sd
            generator = _kokoro_pipeline(text, voice=_voice_name, speed=1.0)
            for _, _, audio in generator:
                sd.play(audio, samplerate=24000)
                sd.wait()
        except Exception:
            pass


def _is_project_file(path):
    """True only for files inside the project folder. Never library, system, or Shadow Programmer files."""
    if not path or path.startswith("<"):
        return False
    full = os.path.abspath(path)
    lowered = full.lower()
    if "site-packages" in lowered or "dist-packages" in lowered:
        return False
    if os.path.basename(full).lower() == "shadow_programmer.py":
        return False
    if not os.path.exists(full):
        return False
    try:
        root = os.path.normcase(PROJECT_ROOT)
        return os.path.commonpath([os.path.normcase(full), root]) == root
    except ValueError:
        # Different drives on Windows
        return False


def _looks_like_environment_problem(exc_type, exc_value):
    """Missing files, folders, models, modules, or connections are reported, not rewritten."""
    if issubclass(exc_type, ENVIRONMENT_ERROR_TYPES):
        return True
    message = str(exc_value).lower()
    return any(hint in message for hint in ENVIRONMENT_HINTS)


def autonomous_repair_hook(exc_type, exc_value, tb):
    """Automated crash interceptor loop."""
    # Always show the real error first so it is never hidden
    sys.__excepthook__(exc_type, exc_value, tb)

    if issubclass(exc_type, KeyboardInterrupt):
        return

    frames = traceback.extract_tb(tb)

    # Find the deepest crash point that is inside YOUR project, not inside a library
    target = None
    for frame in reversed(frames):
        if _is_project_file(frame.filename):
            target = frame
            break

    if target is None:
        print("\n[Shadow Programmer] The crash came from outside your project folder. Nothing was patched.")
        _speak_alert("The crash came from outside your project. Nothing was patched.")
        return

    filepath = os.path.abspath(target.filename)
    line_number = target.lineno
    crash_line = target.line or ""
    error_message = f"{exc_type.__name__}: {exc_value}"
    filename_only = os.path.basename(filepath)

    if _looks_like_environment_problem(exc_type, exc_value):
        print("\n[Shadow Programmer] This looks like a missing file, folder, model, module, or connection, not a code bug.")
        print(f"[Shadow Programmer] Nothing was patched. Check line {line_number} of {filename_only}:")
        print(f"    {crash_line}")
        _speak_alert(f"Something is missing, not broken. Check line {line_number} of {filename_only}.")
        return

    _speak_alert(f"Crash detected in {filename_only} on line {line_number}. Analyzing error with Llama.")

    # Read the broken source file
    with open(filepath, "r", encoding="utf-8") as f:
        original_code = f.read()

    # Construct the instruction prompt for local Llama 3.2
    prompt = f"""You are an autonomous code repair agent. A Python script crashed.

File Path: {filepath}
Crash Line Number: {line_number}
Crash Line: {crash_line}
Error Encountered: {error_message}

Original Code Base:
```python
{original_code}
```

Task: Fix the bug causing this crash. Return ONLY the complete, fully corrected Python file inside a single ```python markdown code block. Do not write introductory text, explanations, or sign-offs.
"""

    try:
        # Call local Llama 3.2 via Ollama
        response = ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}]
        )

        raw_reply = response['message']['content']

        if "```python" in raw_reply:
            repaired_code = raw_reply.split("```python")[1].split("```")[0].strip()
        else:
            repaired_code = raw_reply.strip()

        if not repaired_code or len(repaired_code) < 5:
            raise ValueError("Llama generated an empty file patch.")

        # Local Verification: Compile check (syntax only, it does not prove the bug is fixed)
        compile(repaired_code, filepath, 'exec')

        # Timestamped backup so earlier backups are never overwritten
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{filepath}.{stamp}.bak"
        shutil.copyfile(filepath, backup_path)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(repaired_code + "\n")

        _speak_alert(f"Patched {filename_only}. Original saved as a backup. Run your code again to check the fix.")
        print(f"\n[Shadow Programmer] Patched: {filepath}")
        print(f"[Shadow Programmer] Original saved as: {backup_path}")
        print("[Shadow Programmer] The patch compiles. Run your script again to confirm the bug is really fixed.")

    except Exception as e:
        _speak_alert("Shadow repair failed to patch the error.")
        print(f"\n[Shadow Programmer] Repair failed: {e}. Nothing was changed.")


# Register the global process hook
sys.excepthook = autonomous_repair_hook

 
