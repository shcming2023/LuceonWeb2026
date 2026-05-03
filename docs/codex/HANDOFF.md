# Codex Thread Handoff

Last updated: 2026-05-03

This file is the short entry point for moving Luceon2026 work from the current Windows Codex environment to the Home Mac mini Codex environment.

## Source Environment

- Current active folder: `D:\Users\moonp\OneDrive\Mac\项目开发\Luceon2026`
- Current repository branch: `main`
- Current local state before this handoff: `main` was ahead of `origin/main` by 10 commits
- Codex thread state on this Windows machine is local to `C:\Users\moonp\.codex`

Do not rely on OneDrive or local Codex thread history as the durable project memory. Use GitHub and repository docs.

## Target Environment

Home Mac mini will become the main Codex host.

Suggested directories:

```text
~/dev/Luceon2026
~/staging/Luceon2026
/opt/luceon2026
```

Suggested container/project naming:

```text
luceon-dev
luceon-staging
luceon-prod
```

## Threads To Recreate Or Continue

### lucia

Read:

- `AGENTS.md`
- `docs/codex/roles/lucia.md`
- `docs/codex/PROJECT_STATE.md`

Use lucia for architecture control, task writing, review, and final judgment. Lucia must not take over code implementation, PRD maintenance, or Tier 2 execution.

### luplan

Read:

- `AGENTS.md`
- `docs/codex/roles/luplan.md`
- `docs/prd/README.md`
- `docs/prd/luplan-prd-maintenance.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`

Use luplan for PRD, changelog, decision, and project-state maintenance only.

### lutest

Read:

- `AGENTS.md`
- `docs/codex/roles/lutest.md`
- `docs/codex/TEST_POLICY.md`

lutest is a transition role. Once the Mac mini becomes the only Codex host, move its remaining validation knowledge into `luceonhmm` and archive lutest.

### luceonhmm

Create on the Mac mini when ready. It will own staging, production validation, deployment, rollback, and evidence capture.

## Before Leaving The Windows Machine

1. Check status:

```bash
git status --short --branch
```

2. Commit handoff docs.
3. Push all local commits to GitHub after Director approves.
4. Do not copy `C:\Users\moonp\.codex` as a multi-machine sync mechanism.
5. Rotate any exposed MinerU token before production use.

## First Commands On Mac Mini

```bash
mkdir -p ~/dev ~/staging
cd ~/dev
git clone <github-repo-url> Luceon2026
cd Luceon2026
git status --short --branch
npm install
npx tsc --noEmit
npm run build
npm run local:check
```

Then run the Tier 2 Standard command set with real MinerU env values.
