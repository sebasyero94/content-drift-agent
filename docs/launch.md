# Launch commands

Open one terminal tab per session. Start `lead` first.

```bash
cd "$HOME/Library/Mobile Documents/com~apple~CloudDocs/sebastian_all/Projects/content-drift-agent" && claude -n lead "$(cat docs/prompts/lead.txt)"

cd "$HOME/Library/Mobile Documents/com~apple~CloudDocs/sebastian_all/Projects/content-drift-agent" && claude -n plumbing "$(cat docs/prompts/plumbing.txt)"

cd "$HOME/Library/Mobile Documents/com~apple~CloudDocs/sebastian_all/Projects/content-drift-agent" && claude -n data "$(cat docs/prompts/data.txt)"

cd "$HOME/Library/Mobile Documents/com~apple~CloudDocs/sebastian_all/Projects/content-drift-agent" && claude -n engine "$(cat docs/prompts/engine.txt)"

cd "$HOME/Library/Mobile Documents/com~apple~CloudDocs/sebastian_all/Projects/content-drift-agent" && claude -n evals "$(cat docs/prompts/evals.txt)"

```
