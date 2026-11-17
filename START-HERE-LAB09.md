# Lab 9 on the Lab 8 codebase

This repository preserves the Lab 8 Git history and adds the Lab 9 evaluation overlay.

- `src/lab8/`: original Lab 8 agent code; do not modify for Lab 9.
- `src/lab9/`: Lab 9 evaluators, statistics, and regression gate.
- `lab9-assignment/`: original Lab 9 README, checkpoints, rubric, and submission requirements.
- `docs/`: Lab 8 documentation plus Lab 9 analysis templates.
- `main`: original Lab 8 base commit.
- `starter/d09`: combined Lab 8 and Lab 9 work.

The root README and submission files still describe Lab 8. Follow `lab9-assignment/SUBMISSION.md` for Lab 9.

## Run on Windows PowerShell

```powershell
cd src
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-lab9.txt
.\.venv\Scripts\python.exe -m lab9.smoke
.\.venv\Scripts\python.exe -m pytest -q -m student -o addopts= tests/test_lab9_graders.py
```

The existing v1 eval set and labels are included. Lab 9 exercises are not all completed:
only the two M3 graders have been implemented and tested. Complete the remaining
checkpoints before generating the final baseline and submitting.

Open the final submission PR from `starter/d09` to `main` in your new repository.
