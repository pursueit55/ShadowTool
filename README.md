


# Shadow Tools

Two small, local Python tools for catching crashes and repairing code with a local AI model. Everything runs offline on my own computer. No code is sent to an outside server.

Built by Michelle Evans.

## The tools

### troubleshooter.py: crash reports in plain English

Catches an error and prints a readable report of what went wrong. It **only reports**. It never changes any files.

```python
import troubleshooter

try:
    run_my_program()
except Exception as e:
    report = troubleshooter.analyze_block(exception=e, local_vars=locals())
    print(report)
```

### shadow_programmer.py: a local AI coding agent

Add one line to the top of a script:

```python
import shadow_programmer
```

When the script crashes, Shadow Programmer catches the crash, sends the broken file to a local Llama 3.2 model (through Ollama), and writes back a repaired version.

Safety rules built in:

- **Always shows the real error first.** Nothing is hidden.
- **Only edits files inside your project folder.** It never touches installed libraries (`site-packages`).
- **Reports missing files instead of rewriting code.** If the crash is a missing file, folder, model or connection, it tells you which line to check and changes nothing.
- **Timestamped backups.** Every change saves the original first, like `main.py.20261001_141500.bak`, so backups never overwrite each other.
- **Honest about what it proved.** A patch that compiles is not proof the bug is fixed, so it tells you to run the script again to confirm.

## Requirements

- Python 3.11
- [Ollama](https://ollama.com) running locally with the `llama3.2` model (`ollama serve`)
- `pip install ollama`

## Why the safety rules exist

On October 1, 2026, I tested the first version of Shadow Programmer on my voice assistant project. The crash was caused by a wrong folder path to a voice model. The first version grabbed the last file in the crash report, which was a file inside the Vosk library, rewrote it, and reported "Auto-patched." The real problem was still there and an installed library had been changed.

I traced the cause (it always picked the last file in the traceback) and rebuilt it with the rules above. The lesson: an AI agent that changes code needs limits, a human checkpoint, and proof, not just a success message.

## Known issues and next steps

- The fix is checked by compiling, not yet by running tests.
- **Next: Shadow Gate.** The AI will propose a fix as a reviewable plan, a human approves or rejects it, pytest verifies it, and every run saves an evidence receipt.

 
