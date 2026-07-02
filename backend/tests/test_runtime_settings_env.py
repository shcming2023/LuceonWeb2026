from app.services import runtime_settings


def test_pipeline_env_exports_deepseek_api_base(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime_settings, "CONFIG_PATH", tmp_path / "runtime_config.json")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    env = runtime_settings.pipeline_env()

    assert env["DEEPSEEK_BASE_URL"] == "https://api.example.com/v1"
    assert env["DEEPSEEK_API_BASE"] == "https://api.example.com/v1/chat/completions"


def test_pipeline_env_preserves_chat_completions_url(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime_settings, "CONFIG_PATH", tmp_path / "runtime_config.json")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.example.com/chat/completions")

    env = runtime_settings.pipeline_env()

    assert env["DEEPSEEK_API_BASE"] == "https://api.example.com/chat/completions"
