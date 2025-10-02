# Safely purge checked-in virtualenv from git history

This document explains a careful, review-friendly process to remove large checked-in virtualenv directories (for example `my_jupyter_env/`) from your repository history using `git-filter-repo`.

Important: rewriting history is destructive for existing clones. Coordinate with collaborators and back up the repository (mirror clone) before proceeding.

Checklist (recommended)
- [ ] Create a mirror clone: `git clone --mirror https://github.com/<you>/<repo>.git repo.git`
- [ ] Install git-filter-repo: `pip install git-filter-repo`
- [ ] Run the filter in the mirror repo (example):

  git filter-repo --path my_jupyter_env/ --invert-paths

- [ ] Inspect the rewritten repo and run tests.
- [ ] Create a new remote or coordinate with your team and force-push the rewritten history:

  git remote add cleaned https://github.com/<you>/<repo>-cleaned.git
  git push cleaned --all --force

- [ ] Notify contributors to re-clone the cleaned repository.

Alternative: use BFG Repo Cleaner for simpler cases, but git-filter-repo is recommended.

If you'd like, I can prepare the exact commands for your repository, create the mirror clone locally, and run the filter in a safe, isolated directory — but I will not perform the force-push to origin/main without your explicit go-ahead.
