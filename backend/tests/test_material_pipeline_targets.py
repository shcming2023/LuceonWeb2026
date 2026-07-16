from app.services.material_inventory import pipeline_command, pipeline_preflight_command, pipeline_target_args, popo_resume_command


def test_pipeline_target_args_preserve_multiple_selected_materials():
    args = pipeline_target_args(
        material_ids=["pdf-first", "pdf-second"],
        input_objects=["first.pdf", "second.pdf"],
    )

    assert args == [
        "--material-id",
        "pdf-first",
        "--material-id",
        "pdf-second",
        "--input-object",
        "first.pdf",
        "--input-object",
        "second.pdf",
    ]


def test_pipeline_command_targets_every_selected_material():
    command = pipeline_command(
        apply=True,
        limit=2,
        material_ids=["pdf-first", "pdf-second"],
        input_objects=["first.pdf", "second.pdf"],
    )

    assert command.count("--material-id") == 2
    assert command.count("--input-object") == 2
    assert command[-2:] == ["--apply", "--wait"]
    assert "--input-status-only" in command


def test_completed_reprocess_requires_explicit_cli_flag():
    ordinary = pipeline_preflight_command(1, material_ids=["pdf-first"])
    versioned = pipeline_preflight_command(1, material_ids=["pdf-first"], reprocess_completed=True)
    apply_versioned = pipeline_command(
        apply=True,
        limit=1,
        material_ids=["pdf-first"],
        reprocess_completed=True,
    )

    assert "--reprocess-completed" not in ordinary
    assert "--reprocess-completed" in versioned
    assert "--reprocess-completed" in apply_versioned


def test_popo_resume_command_reuses_frozen_mineru_without_resubmitting_it():
    command = popo_resume_command(
        existing_mineru_batch_id="mineru-batch-1",
        material_id="pdf-first",
        input_object="first.pdf",
        apply=True,
    )

    assert command[:3] == ["python3", command[1], "run-staged"]
    assert command[command.index("--existing-mineru-batch-id") + 1] == "mineru-batch-1"
    assert "--reuse-frozen-mineru" in command
    assert command[-2:] == ["--apply", "--wait"]
