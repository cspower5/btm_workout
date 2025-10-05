QA Notes - Hamburger & Mobile Parity

Date: 2025-10-04 (UTC)

Summary:
- Built and promoted updated client bundle to the local static server at `/tmp/serve_root/btm_workout`.
- Removed runtime debug injection from the served index and archived debug files.
- Ran deterministic smoke captures and saved artifacts under `artifacts/smoke_*`.

Acceptance checklist:
- [x] Portrait hamburger centered under the "BREAK THE MONOTONY" header and shows overlay with full links.
- [x] Narrow landscape header links match footer and display in a single centered row.
- [x] Large screens (>900px) preserve original layout (no change).
- [x] Smoke captures (HTML/PNG/console) created for mobile portrait, mobile landscape, tablet, and desktop.

Artifacts:
- artifacts/smoke_2025-10-05T00-31-48-167Z/
- release_artifacts/qa_cleanup_2025-10-05T00-41-20Z.tgz

Notes:
- Debug assets were archived to `/tmp/serve_root/qa_debug_archive` before removal; a copy of that archive is in `release_artifacts/`.
- If additional visual adjustments are desired, I recommend iterating on the source CSS (`client/src/assets/css/App.css` and `client/src/assets/css/Home.css`) and re-running `npm run build`.
