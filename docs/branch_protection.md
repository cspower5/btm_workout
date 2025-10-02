Branch protection and CI guidance
================================

Recommended CI triggers
-----------------------
- Run linting and tests on pull_request targeting `main` (already configured).
- Optionally run a lighter check on push to feature branches.

Recommended branch-protection rules for `main`
---------------------------------------------
1. Require status checks to pass before merging. Select the CI job that runs `pytest`, `ruff`, and `black --check`.
2. Require pull request reviews (1 or 2 reviewers depending on team size).
3. Dismiss stale reviews when new commits are pushed.
4. Require signed commits if your org enforces it.

How to put into practice
------------------------
1. Go to repository Settings → Branches → Add rule for `main`.
2. Enable "Require status checks to pass before merging" and select the workflow checks.
3. Enable required reviews and any additional checks.

Notes
-----
- After enabling branch protection, communicate to contributors that they'll need to open PRs and wait for CI to pass before merging.
- If you perform history rewrites (like removing large files), coordinate carefully — protected branches will complain on force-push attempts.
