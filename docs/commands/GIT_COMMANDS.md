# Git Commands Used In This Project

Last updated: 2026-03-30
Scope: Commands used in day-to-day development, release flow, and roadmap/release-note practices for this repository.

## How To Read This File

For each command, this guide explains:
- What it is used for
- When to use it
- Where to run it
- How it works
- Recommended tags/options (flags) and why
- Alternatives

---

## 1) Check Branch And Working State

Command:

```bash
git status -sb
```

Used for:
- Quick view of current branch, upstream relationship, and changed files.

When to use:
- Before starting work
- Before committing
- Before pushing

Where to use:
- Repository root

How it works:
- -s gives short output
- -b includes branch/ahead/behind info

Tags/options and why:
- -s: concise output for faster scanning
- -b: branch context to prevent committing to the wrong branch

Alternatives:
- git status (full detailed format)

---

## 2) Stage Files

Command:

```bash
git add <path>
```

Used for:
- Add specific files to the next commit.

When to use:
- After validating edits and before commit

Where to use:
- Repository root (or any subdirectory)

How it works:
- Moves file changes from working tree to staging area.

Tags/options and why:
- Use explicit paths (recommended): safer than broad staging for large repos
- git add .: acceptable when all local changes are intentional

Alternatives:
- git add -p for interactive hunk staging

---

## 3) Create A Commit

Command:

```bash
git commit -m "<message>"
```

Used for:
- Save a logical unit of work in project history.

When to use:
- After staging and passing required checks

Where to use:
- Repository root

How it works:
- Captures staged snapshot with metadata and message.

Tags/options and why:
- -m: fast one-line commit messages
- Prefer conventional style prefixes (feat, fix, docs, chore) for readable history

Alternatives:
- git commit (opens editor for longer messages)

---

## 4) Push To Remote

Command:

```bash
git push origin master
```

Used for:
- Publish local commits to remote repository.

When to use:
- After local validation/tests and commit completion

Where to use:
- Repository root

How it works:
- Sends local branch objects to remote tracking branch.

Tags/options and why:
- Explicit remote and branch avoids accidental push destination
- -u may be used once for new branches to set upstream

Alternatives:
- git push (when upstream already set)

---

## 5) View Recent History

Command:

```bash
git log -n 5 --oneline
```

Used for:
- Inspect recent commit sequence quickly.

When to use:
- Before release notes, docs updates, or PR preparation

Where to use:
- Repository root

How it works:
- Shows abbreviated hash + subject line for last commits.

Tags/options and why:
- --oneline for compact history
- -n 5 limits output noise

Alternatives:
- git log (full detailed history)

---

## 6) Compare Changes

Command:

```bash
git diff
```

Used for:
- Review unstaged modifications before staging/commit.

When to use:
- During code review of your own changes

Where to use:
- Repository root

How it works:
- Shows line-level changes in working tree vs index.

Tags/options and why:
- --staged: review staged content before commit
- -- <path>: focus on one file

Alternatives:
- git show <commit> for committed diffs

---

## 7) See Remote Configuration

Command:

```bash
git remote -v
```

Used for:
- Verify fetch/push endpoints (especially before pushing).

When to use:
- New environment setup
- Before release pushes

Where to use:
- Repository root

How it works:
- Prints remotes and URLs for fetch/push.

Tags/options and why:
- -v includes URL details

Alternatives:
- git remote show origin for deeper remote info

---

## 8) Create Annotated Release Tags (Roadmap/Release Practice)

Command:

```bash
git tag -a v0.2.0 -m "Release note summary"
```

Used for:
- Mark milestone releases with semantic versions.

When to use:
- After stable release checkpoints

Where to use:
- Repository root, on commit being released

How it works:
- Creates immutable tag object with message.

Tags/options and why:
- -a creates annotated tag (preferred over lightweight)
- vMAJOR.MINOR.PATCH naming supports release clarity and automation

Alternatives:
- Lightweight tags: git tag v0.2.0 (less metadata)

---

## 9) Push Tags

Command:

```bash
git push origin v0.2.0
```

Used for:
- Publish release tags to remote.

When to use:
- Right after creating verified release tags

Where to use:
- Repository root

How it works:
- Pushes specific tag reference to remote.

Tags/options and why:
- Explicit tag name avoids pushing unintended tags

Alternatives:
- git push --tags (bulk; use carefully)

---

## Practical Safety Notes

- Prefer small, topic-focused commits (feature, hardening, docs split is ideal).
- Always run git status -sb before commit and before push.
- Push only after required local checks (tests/lint/quality gates as applicable).
