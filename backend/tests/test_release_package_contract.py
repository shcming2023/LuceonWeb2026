from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy" / "luceon-v1"


def test_production_compose_template_has_no_build_or_mutable_image_tags():
    text = (DEPLOY / "compose.production.arm64.yml.tmpl").read_text()

    assert "build:" not in text
    assert ":latest" not in text
    assert ":local" not in text
    assert "/Users/concm" not in text
    assert "~/.codex" not in text
    assert text.count("image:") == 9
    assert text.count("@sha256:") == 5
    assert text.count("__BACKEND_IMAGE__") == 4
    assert text.count("__FRONTEND_IMAGE__") == 1


def test_worker_does_not_inherit_backend_http_healthcheck():
    text = (DEPLOY / "compose.production.arm64.yml.tmpl").read_text()
    worker = text.split("  workflow-v2-worker:\n", 1)[1].split("\n  frontend:\n", 1)[0]

    assert "healthcheck:\n      disable: true" in worker
    assert "material-task-worker:" in worker
    assert "backup-task-worker:" in worker

    local_text = (ROOT / "docker-compose.luceon-review.yml").read_text()
    local_workers = local_text.split("  workflow-v2-worker:\n", 1)[1].split("\n  redis:\n", 1)[0]
    assert local_workers.count("healthcheck:\n      disable: true") == 3


def test_release_requires_explicit_minio_endpoints_and_external_backup_volume():
    compose = (DEPLOY / "compose.production.arm64.yml.tmpl").read_text()
    env = (DEPLOY / ".env.production.example").read_text()
    preflight = (DEPLOY / "scripts" / "preflight").read_text()

    assert "MINIO_INTERNAL_ENDPOINT=" in env
    assert "MINIO_PUBLIC_ENDPOINT=" in env
    assert "LUCEON_EXTERNAL_BACKUP_PATH=" in env
    assert "LUCEON_EXTERNAL_BACKUP_ROOT: /external-backups" in compose
    assert "backup_task_worker.py" in compose
    assert 'test -w "$external_backup_path"' in preflight
    assert 'device_id state/backend' in preflight
    assert 'device_id "$external_backup_path"' in preflight


def test_release_preflight_requires_sufficient_docker_vm_memory():
    preflight = (DEPLOY / "scripts" / "preflight").read_text()

    assert "docker info --format '{{.MemTotal}}'" in preflight
    assert "15 * 1024 * 1024 * 1024" in preflight


def test_compiler_uses_current_overleaf_data_path():
    text = (DEPLOY / "compose.production.arm64.yml.tmpl").read_text()
    compiler = text.split("  texlive:\n", 1)[1].split("\n  backend:\n", 1)[0]

    assert "compiler-data:/var/lib/overleaf" in compiler
    assert "/var/lib/sharelatex" not in compiler
    assert "OVERLEAF_MONGO_URL:" in compiler
    assert "OVERLEAF_REDIS_HOST:" in compiler
    assert "SHARELATEX_" not in compiler
    assert 'SANDBOXED_COMPILES: "false"' in compiler
    assert "ALL_TEX_LIVE_DOCKER_IMAGE_NAMES: TeX Live" in compiler
    assert "ALL_TEX_LIVE_DOCKER_IMAGES: ghcr.io/lcpu-club/sharelatex@sha256:" in compiler


def test_release_verifier_reads_actual_container_runtime_state():
    text = (DEPLOY / "scripts" / "verify").read_text()

    assert "docker inspect --format" in text
    assert ".State.OOMKilled" in text
    assert ".RestartCount" in text
    assert '.State.Health.Status' in text
    assert "config --services" in text
    assert "ps -aq" in text


def test_release_verifier_requires_stable_database_health_and_one_worker_per_database():
    text = (DEPLOY / "scripts" / "verify").read_text()

    assert 'while [ "$probe" -le 5 ]' in text
    assert 'health.get("database") != "ok"' in text
    assert 'health.get("gpu_required") is not False' in text
    assert 'item.startswith("WORKFLOW_DATABASE_URL=")' in text
    assert '"workflow_v2_worker.py" not in command' in text
    assert "expected exactly the release worker for this database" in text


def test_release_start_waits_for_declared_healthchecks():
    text = (DEPLOY / "scripts" / "start").read_text()

    assert "up -d --no-build --pull never" in text
    assert "--wait --wait-timeout 180" in text


def test_release_package_separates_private_skills_from_public_source():
    text = (DEPLOY / "skill-lock.json").read_text()
    compose = (DEPLOY / "compose.production.arm64.yml.tmpl").read_text()

    assert '"distribution": "private-state-package-only"' in text
    assert "./private/skills:/private/skills:ro" in compose
    assert not (DEPLOY / "private").exists()


def test_release_package_contains_operational_handoff_files():
    required = [
        ".env.production.example",
        "images.lock.json.tmpl",
        "skill-lock.json",
        "config/runtime-config.example.json",
        "scripts/preflight",
        "scripts/pull-or-load",
        "scripts/backup",
        "scripts/migrate",
        "scripts/start",
        "scripts/verify",
        "scripts/rollback",
        "scripts/render-release-package",
        "docs/install.md",
        "docs/upgrade.md",
        "docs/rollback.md",
        "docs/acceptance.md",
    ]

    assert all((DEPLOY / item).is_file() for item in required)
