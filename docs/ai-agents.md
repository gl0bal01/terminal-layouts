# AI-agent workspace (experimental)

This first increment adds an `ai-agents` workflow to the **existing canonical manifest**. It is rendered by the existing tmuxp and Zellij generators; no new runtime or provider credentials are required.

## Try it

```sh
tl validate
tl gen tmux ai-agents
tl gen zellij ai-agents
tl install
tmuxp load -y ai-agents
# or: zellij --layout ai-agents
```

The agent panes start as shells deliberately. Launch `opencode`, `pi`, `claude`, or `codex` manually. This prevents unexpected API charges and permits per-agent authentication.

## Herdr integration: next increment

Herdr is an independent terminal runtime, **not** a tmuxp/Zellij layout format. Do not claim structural parity for Herdr until its CLI/socket API can represent the same manifest semantics.

Planned adapter:
1. Validate manifest using the existing schema.
2. Compile tabs and leaf panes into a versioned, deterministic Herdr execution plan.
3. Add `tl gen herdr <workflow>` for a dry-run plan.
4. Add explicit `tl launch herdr <workflow>` with opt-in process spawning and CLI capability checks.
5. Test unsupported features, missing executables, idempotence, and no silent fallback.

Use one Git worktree per writing agent; never allow multiple agents to edit the same checkout simultaneously. Keep API keys out of manifests and logs.

This PR does **not** implement a Herdr backend yet. It supplies the validated shared workflow that a backend can consume.
