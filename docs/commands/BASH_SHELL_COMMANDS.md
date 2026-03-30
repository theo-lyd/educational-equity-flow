# Bash and Shell Commands Used In This Project

Last updated: 2026-03-30
Scope: Terminal commands and shell patterns used by project scripts, local execution, and CI jobs.

## How To Read This File

Each command includes:
- What it is used for
- When to use it
- Where to run it
- How it works
- Recommended tags/options (flags) and why
- Alternatives

---

## 1) Activate Virtual Environment

Command:

```bash
source .venv/bin/activate
```

Used for:
- Use project-specific Python and installed dependencies.

When to use:
- Before running Python or Make targets manually

Where to use:
- Repository root

How it works:
- Updates current shell PATH/environment to use .venv binaries.

Tags/options and why:
- No flags needed

Alternatives:
- Use explicit interpreter paths: .venv/bin/python -m <module>

---

## 2) Run Full System Launcher

Command:

```bash
./run_full_system.sh
```

Used for:
- End-to-end startup: setup, ingestion, dbt, ML, quality checks, and app launch.

When to use:
- Demo prep
- Non-technical launch workflows

Where to use:
- Repository root

How it works:
- Executes the orchestration shell script with strict failure behavior.

Tags/options and why:
- Run after chmod +x if execution bits are missing

Alternatives:
- Run equivalent make targets manually, step by step

---

## 3) Make Script Executable

Command:

```bash
chmod +x run_full_system.sh
```

Used for:
- Grant execute permission to launcher scripts.

When to use:
- New clones where file mode may not be executable

Where to use:
- Repository root

How it works:
- Adds executable bit on file permissions.

Tags/options and why:
- +x to enable execution

Alternatives:
- Run with explicit shell: bash run_full_system.sh (no execute bit required)

---

## 4) Validate Shell Script Syntax

Command:

```bash
bash -n run_full_system.sh
```

Used for:
- Quick syntax validation without execution.

When to use:
- Before committing script edits

Where to use:
- Repository root

How it works:
- Parses script and reports syntax errors only.

Tags/options and why:
- -n prevents accidental execution side effects

Alternatives:
- shellcheck for deeper linting (if installed)

---

## 5) Strict Shell Mode Pattern

Command pattern:

```bash
set -euo pipefail
```

Used for:
- Fail fast and reduce hidden shell-script errors.

When to use:
- At the top of project shell scripts

Where to use:
- Inside shell script files

How it works:
- -e: exit on command failure
- -u: error on undefined variables
- -o pipefail: pipeline fails if any command fails

Tags/options and why:
- Combined strict mode is recommended for reliability

Alternatives:
- Use only set -e (weaker protection)

---

## 6) Directory Navigation Pattern

Command pattern:

```bash
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"
```

Used for:
- Make scripts robust regardless of launch location.

When to use:
- In reusable scripts that must run from project root

Where to use:
- Script preamble

How it works:
- Resolves script directory and moves shell to it.

Tags/options and why:
- Quotes prevent breakage with spaces in paths

Alternatives:
- Hardcoded absolute paths (less portable)

---

## 7) Conditional Directory Existence Check

Command pattern:

```bash
if [[ ! -d ".venv" ]]; then
  make setup-venv
fi
```

Used for:
- Auto-bootstrap environment only when missing.

When to use:
- Startup scripts meant for broad user audiences

Where to use:
- Shell scripts

How it works:
- Tests filesystem path and conditionally executes setup.

Tags/options and why:
- -d checks directory existence
- ! inverts test for missing directory

Alternatives:
- Always run make setup-venv (slower but simple)

---

## 8) CI/Pipeline Multi-Line Shell Blocks

Pattern used in workflow run blocks:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Used for:
- Deterministic environment bootstrapping in CI runners.

When to use:
- GitHub Actions run steps

Where to use:
- .github/workflows/*.yml

How it works:
- Executes sequential shell commands in the CI runner shell.

Tags/options and why:
- --upgrade keeps installer tooling current
- -e .[dev] installs project in editable mode with dev extras

Alternatives:
- pip install -r requirements-dev.txt

---

## 9) Common Diagnostic Shell Commands Used In Practice

Commands:

```bash
git status -sb
git log -n 5 --oneline
ls -lh warehouse/artifacts/
```

Used for:
- Fast verification of repo state and artifacts.

When to use:
- Before release/demo, after pipeline runs

Where to use:
- Repository root

How it works:
- Prints concise status, commit history, and file inventory.

Tags/options and why:
- -lh in ls improves readability (human sizes + long format)

Alternatives:
- tree for hierarchical listing

---

## Practical Safety Notes

- Keep shell scripts idempotent and explicit.
- Prefer explicit project-relative paths.
- Validate scripts with bash -n after edits.
