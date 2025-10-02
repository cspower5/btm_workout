
# Safely purge checked-in virtualenv from git history

This document is a step-by-step runbook to remove large checked-in directories (for example `my_jupyter_env/` or `.venv/`) from your repository history. It includes examples for `git-filter-repo` (recommended) and the BFG Repo Cleaner (alternate), guidance for preserving tags, author/email remapping, verification steps, and exact commands you can run locally in a mirror clone.

IMPORTANT: rewriting history is destructive for collaborators. Do not run the final force-push to your primary remote until you've coordinated with the team, backed up the repository, and tested the cleaned mirror. Always operate on a mirror clone, not the working clone.

Quick overview (non-destructive workflow)
- Create a bare mirror of the repository.
- Run the filtering tool (git-filter-repo) inside the mirror to remove the unwanted paths.
- Clone the cleaned mirror to inspect and run tests.
- If satisfied, push the cleaned history to a new remote (or replace origin after coordination).

Required tools
- git
- python + pip
- git-filter-repo (recommended): `pip install git-filter-repo`
- Optional: BFG Repo Cleaner (Java-based) as an easier alternative for some cases.

Safe runbook (commands you can copy/paste)
1) Create a mirror clone (this copies all refs, tags, and branches):

```bash
git clone --mirror https://github.com/<you>/<repo>.git repo.git
cd repo.git
```

2) Run git-filter-repo to remove a path (keep everything except the path):

```bash
# remove a single directory (e.g., my_jupyter_env/)
git filter-repo --path my_jupyter_env/ --invert-paths
```

Notes on `git-filter-repo`:
- `--invert-paths` keeps everything except the listed paths.
- You can pass multiple `--path` options to remove more than one path.
- Use `--force` if you re-run the command in the same clone.

Preserving or restoring tags and refs
- The mirror clone preserves tags and refs by default. After filtering, tags and annotated refs should remain, but you should verify:

```bash
# list tags and inspect a commit
git tag --list
git show <some-tag>
```

If you want to preserve tag names but re-point them or recreate them in the cleaned repo, you can re-create tags after cloning the cleaned mirror (see verification steps).

Author/email remapping (git-filter-repo)
- Prepare a CSV `author-map.csv` with rows: `old_email,new_name,new_email`
- Example `author-map.csv` contents:

```
old@example.com,New Name,new@example.com
legacy@corp.com,Legacy Dev,legacy@newcorp.com
```

Then run git-filter-repo with a commit-callback to remap authors. A helper script is provided in `scripts/purge_and_prepare.sh` or `scripts/purge_venv_with_git_filter_repo.sh` in this repo; they support author remapping and run in a mirror clone so your working repo is untouched.

Alternative: BFG Repo Cleaner (simpler for huge files)
- BFG removes large files or directories by name. It's Java-based and easier for common cases:

```bash
# Mirror clone
git clone --mirror https://github.com/<you>/<repo>.git repo.git
cd repo.git

# Remove folder named my_jupyter_env from history
bfg --delete-folders my_jupyter_env --no-blob-protection
# Clean up and expire reflog
git reflog expire --expire=now --all && git gc --prune=now --aggressive
```

- BFG is faster on big repos but less flexible than git-filter-repo for complex author remapping and commit-level edits.

Verification steps (must do)
1. Clone the cleaned mirror into a normal repo for inspection:

```bash
cd ..
git clone ./repo.git repo-cleaned
cd repo-cleaned
```

2. Run your test suite and linters. Confirm that the unwanted directory is gone from history:

```bash
# search for path in history (should be no result)
git rev-list --all | xargs -n1 git grep --name-only --cached --untracked -- 'my_jupyter_env' || true

# or more reliable: look for blobs matching a filename, e.g.
git log --all -- '**/my_jupyter_env/**'
```

3. Inspect tags, branches, and a few sample commits:

```bash
git tag --list
git checkout main
git log --oneline --decorate --graph -n 50
```

Pushing the cleaned repo (coordinate first)
- When you're ready, push the cleaned history to a new remote for review (recommended) or to origin with force (dangerous):

```bash
# push to a new remote for safe review
git remote add cleaned https://github.com/<you>/<repo>-cleaned.git
git push cleaned --all --force
git push cleaned --tags --force

# OR (only after coordination, backups, and approval):
# git remote set-url --push origin https://github.com/<you>/<repo>.git
# git push origin --all --force
# git push origin --tags --force
```

Rollback plan
- Keep the original mirror (untouched). If anything goes wrong, collaborators can still use the original remote to reclone. Do NOT delete your backups until you're 100% satisfied.

Edge cases & tips
- Large repos: run the filter on a beefy machine; git-filter-repo is efficient but may need memory for very large histories.
- Binary files: `--invert-paths` will remove them, but blobs might remain deduplicated until garbage collection; pushing cleaned history replaces refs and makes old blobs unreachable in the cleaned remote.
- Tags & external integrations: check CI and release pipelines that rely on commit SHAs — they will change after a history rewrite.

Automated helper scripts in this repo
- `scripts/purge_venv_with_git_filter_repo.sh` — creates a mirror clone and runs git-filter-repo on a single path, leaving the cleaned mirror in place.
- `scripts/purge_and_prepare.sh` — more featureful: accepts an optional author-map CSV to remap authors during filtering.

If you want, I can:
- Produce a fully-annotated runbook with the exact commands I would run (I will not execute destructive commands unless you explicitly ask me to). 
- Help perform the final force-push to `origin/main` after you confirm backing up and coordinating contributors.

Read this file carefully and run the commands in a disposable environment (mirror clone) first.
