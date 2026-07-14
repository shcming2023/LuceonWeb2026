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
    assert text.count("@sha256:") == 4
    assert text.count("__BACKEND_IMAGE__") == 2
    assert text.count("__FRONTEND_IMAGE__") == 1


def test_worker_does_not_inherit_backend_http_healthcheck():
    text = (DEPLOY / "compose.production.arm64.yml.tmpl").read_text()
    worker = text.split("  workflow-v2-worker:\n", 1)[1].split("\n  frontend:\n", 1)[0]

    assert "healthcheck:\n      disable: true" in worker


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
