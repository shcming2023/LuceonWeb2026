# Home Mac Mini Migration Notes

Last updated: 2026-05-06

## Goal

Move active Codex development and validation to the Home Mac mini so all long-lived Codex threads share one environment.

Work computers should become remote desktop clients. They do not need to keep independent Codex thread state or equivalent Docker/MinerU/Ollama environments.

## Target Directories

```text
~/dev/Luceon2026
~/staging/Luceon2026
/opt/luceon2026
```

Use separate compose project names or container name conventions for dev, staging, and production.

## Migration Steps

1. Push the reviewed `main` branch to GitHub.
2. On Mac mini:

```bash
mkdir -p ~/dev ~/staging
cd ~/dev
git clone <github-repo-url> Luceon2026
cd Luceon2026
```

3. Install or verify tools:

```bash
git --version
docker --version
docker compose version
node --version
npm --version
npx pnpm@10.4.1 --version
```

4. Install and sign in to Codex on the Mac mini.
5. Create or continue Codex threads:

```text
lucia
luplan
luceonhmm
```

6. Have each thread read:

```text
AGENTS.md
docs/codex/PROJECT_STATE.md
docs/codex/roles/<role>.md
```

7. Run L1:

```bash
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
npx pnpm@10.4.1 run local:check
```

8. Run Tier 2 Standard with real MinerU env values.
9. Only after staging validation is stable, configure production deployment under `/opt/luceon2026`.

## Important Separation

Do not let Codex develop directly inside production deployment.

Use:

- dev for code changes
- staging for validation
- production for serving

Production deployment scripts should eventually include:

- backup
- pull exact commit or tag
- build
- health check
- rollback
- evidence report
