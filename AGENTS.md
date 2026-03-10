# AGENTS.md

## Screenshots
When the user says "look at ss" or references a screenshot, read the image from:
`/mnt/c/Users/tylerbtt/AppData/Local/Temp/ss.png`

## MLS Data Access

### Provider-Agnostic Design
All MLS code MUST be provider-agnostic. Use env vars for base URL, auth method, dataset, and credentials. RESO Data Dictionary fields are the same across providers — only auth and endpoint URLs differ.

### Bridge Interactive (Active — Dev/Test)
- Auth: Server token as query param `access_token` — NO OAuth, NO Bearer header
- Endpoint: `GET {BRIDGE_API_URL}/OData/{dataset}/{Resource}?access_token={BRIDGE_API_TOKEN}&$top=N`
- Datasets: `actris_ref` (real Austin MLS, 52k+), `test` (synthetic, 10k)
- Use `actris_ref` for development (NOT `actris` — that 404s)

### Trestle / NTREIS (Pending — Production)
- Auth: OAuth2 client_credentials → Bearer token header
- Token endpoint: `{base}/oidc/connect/token`
- OData endpoint: `{base}/odata/{Resource}`
- Waiting on broker for NTREIS IDX Vendor Authorization Form

### Swapping Providers
When NTREIS credentials arrive, only env vars change — no code changes needed if the MLS client is built correctly.

## Issue Tracking (Beads)

Uses **br** (beads-rust) — git-native, AI-friendly task tracker. Non-invasive, never runs git commands.

| Command | Purpose |
|---------|---------|
| `br ready` | Find work with no blockers (START HERE) |
| `br show <id>` | View details + blockers |
| `br update <id> --claim` | Claim work (atomic: assignee + in_progress) |
| `br close <id> --reason "..."` | Complete work |
| `br create "Title" -p 1 -t task` | Create task (P0-P3) |
| `br dep add <child> <parent>` | Add blocker |
| `br sync --flush-only` | Export DB → JSONL (then `git add .beads/ && git commit`) |
| `br sync --import-only` | Import JSONL → DB (after git pull) |

After clone/checkout: `br sync --import-only`. After git pull: `br sync --import-only`.

### Session Completion

Work is NOT complete until `git push` succeeds. MANDATORY steps:

1. File issues for remaining work
2. Close finished beads, update in-progress items
3. **Push:**
   ```bash
   git pull --rebase
   br sync --flush-only
   git add .beads/
   git commit -m "Beads updates" || true
   git push
   ```
4. Verify `git status` shows "up to date with origin"
