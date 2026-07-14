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
    assert text.count("image:") == 7
    assert text.count("@sha256:") == 5
    assert text.count("__BACKEND_IMAGE__") == 2
    assert text.count("__FRONTEND_IMAGE__") == 1


def test_worker_does_not_inherit_backend_http_healthcheck():
    text = (DEPLOY / "compose.production.arm64.yml.tmpl").read_text()
    worker = text.split("  workflow-v2-worker:\n", 1)[1].split("\n  frontend:\n", 1)[0]

    assert "healthcheck:\n      disable: true" in worker


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
