import json
import time

from app.workflow_v2 import queue


def test_execution_lease_covers_long_cpu_bound_stages():
    assert queue.EXECUTION_LEASE_SECONDS >= 1800


def test_reclaim_consumer_leases_only_removes_same_consumer(monkeypatch):
    class FakeRedis:
        def __init__(self):
            self.values = {
                b"workflow-v2:lock:old": b"worker-test",
                b"workflow-v2:lock:active": b"another-worker",
            }

        def scan_iter(self, *, match):
            assert match == "workflow-v2:lock:*"
            return iter(tuple(self.values))

        def get(self, key):
            return self.values.get(key)

        def delete(self, key):
            self.values.pop(key, None)

    fake = FakeRedis()
    monkeypatch.setattr(queue.redis_client, "client", fake)

    assert queue.reclaim_consumer_leases("worker-test") == ["old"]
    assert b"workflow-v2:lock:old" not in fake.values
    assert fake.values[b"workflow-v2:lock:active"] == b"another-worker"


class FakeRedis:
    def __init__(self):
        self.values = {}

    def setex(self, key, _ttl, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def xautoclaim(self, *_args, **_kwargs):
        return ("0-0", [])


def test_worker_heartbeat_makes_execution_available(monkeypatch):
    client = FakeRedis()
    monkeypatch.setattr(queue.redis_client, "client", client)
    queue.record_worker_heartbeat("worker-test")
    assert queue.worker_health()["available"] is True
    assert queue.worker_health()["worker_id"] == "worker-test"


def test_stale_worker_heartbeat_is_not_available(monkeypatch):
    client = FakeRedis()
    client.values[queue.HEARTBEAT_KEY] = json.dumps({"worker_id": "old", "timestamp": time.time() - 20})
    monkeypatch.setattr(queue.redis_client, "client", client)
    assert queue.worker_health() == {"available": False, "worker_id": "old", "age_seconds": 20.0}


def test_execution_lease_refreshes_global_worker_heartbeat(monkeypatch):
    class OneTickStop:
        calls = 0

        def wait(self, _seconds):
            self.calls += 1
            return self.calls > 1

    class FakeSession:
        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    client = FakeRedis()
    client.values["lock"] = "worker-test"
    client.expire = lambda *_args: True
    monkeypatch.setattr(queue.redis_client, "client", client)
    monkeypatch.setattr(queue, "workflow_session_factory", lambda: lambda: FakeSession())
    monkeypatch.setattr(queue, "touch_stage_heartbeat", lambda *_args, **_kwargs: True)

    queue._refresh_execution_lease(OneTickStop(), "lock", "job-1", "worker-test")

    heartbeat = json.loads(client.values[queue.HEARTBEAT_KEY])
    assert heartbeat["worker_id"] == "worker-test"


def test_lock_conflict_records_observable_wait(monkeypatch):
    client = FakeRedis()
    client.read_rows = [(b"7-0", {b"job_id": b"job-1"})]
    client.set = lambda *_args, **_kwargs: False
    recorded = []
    monkeypatch.setattr(queue.redis_client, "client", client)
    monkeypatch.setattr(queue.redis_client, "read_stream", lambda *_args, **_kwargs: client.read_rows)
    monkeypatch.setattr(queue, "_record_queue_wait", lambda *args: recorded.append(args))

    result = queue.consume_once(consumer="worker-test")

    assert result == {"ok": False, "job_id": "job-1", "deferred": True, "reason": "job lock is held"}
    assert recorded == [("job-1", b"7-0", "worker-test")]


def test_successful_stage_queues_the_next_stage(monkeypatch):
    client = FakeRedis()
    client.read_rows = [(b"1-0", {b"job_id": b"job-1"})]
    client.added = []
    client.acked = []
    client.deleted = []
    client.set = lambda key, value, **_kwargs: client.values.setdefault(key, value) is value
    client.xadd = lambda stream, fields: client.added.append((stream, fields)) or b"2-0"
    client.xack = lambda stream, group, message_id: client.acked.append((stream, group, message_id))
    client.delete = lambda key: client.deleted.append(key)
    monkeypatch.setattr(queue.redis_client, "client", client)
    monkeypatch.setattr(queue.redis_client, "read_stream", lambda *_args, **_kwargs: client.read_rows)
    monkeypatch.setattr(queue.redis_client, "ack_message", lambda stream, group, message_id: client.xack(stream, group, message_id))
    monkeypatch.setattr(queue, "run_one_stage", lambda *_args, **_kwargs: {"ok": True, "job_status": "queued"})
    monkeypatch.setattr(queue.threading.Thread, "start", lambda _self: None)
    monkeypatch.setattr(queue.threading.Thread, "join", lambda _self, **_kwargs: None)

    result = queue.consume_once(consumer="worker-test")

    assert result["next_message_id"] == "2-0"
    assert client.added == [(queue.STREAM, {"job_id": "job-1"})]
    assert client.acked == [(queue.STREAM, queue.GROUP, b"1-0")]


def test_failed_independent_review_queues_bounded_auto_repair(monkeypatch):
    client = FakeRedis()
    client.read_rows = [(b"1-0", {b"job_id": b"job-1"})]
    client.added = []
    client.set = lambda key, value, **_kwargs: client.values.setdefault(key, value) is value
    client.xadd = lambda stream, fields: client.added.append((stream, fields)) or b"2-0"
    client.delete = lambda _key: None
    monkeypatch.setattr(queue.redis_client, "client", client)
    monkeypatch.setattr(queue, "POST_QA_AUTO_REPAIR_ENABLED", True)
    monkeypatch.setattr(queue.redis_client, "read_stream", lambda *_args, **_kwargs: client.read_rows)
    monkeypatch.setattr(queue.redis_client, "ack_message", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        queue,
        "run_one_stage",
        lambda *_args, **_kwargs: {"ok": False, "stage": "independent_final_review", "job_status": "failed"},
    )
    monkeypatch.setattr(queue, "_try_auto_rule_repair", lambda _public_id: {"queued": True, "stage_attempt": 2})
    monkeypatch.setattr(queue.threading.Thread, "start", lambda _self: None)
    monkeypatch.setattr(queue.threading.Thread, "join", lambda _self, **_kwargs: None)

    result = queue.consume_once(consumer="worker-test")

    assert result["auto_rule_repair"]["queued"] is True
    assert result["next_message_id"] == "2-0"
    assert client.added == [(queue.STREAM, {"job_id": "job-1"})]


def test_failed_independent_review_does_not_auto_repair_during_core_convergence(monkeypatch):
    client = FakeRedis()
    client.read_rows = [(b"1-0", {b"job_id": b"job-1"})]
    client.added = []
    client.set = lambda key, value, **_kwargs: client.values.setdefault(key, value) is value
    client.xadd = lambda stream, fields: client.added.append((stream, fields)) or b"2-0"
    client.delete = lambda _key: None
    monkeypatch.setattr(queue.redis_client, "client", client)
    monkeypatch.setattr(queue.redis_client, "read_stream", lambda *_args, **_kwargs: client.read_rows)
    monkeypatch.setattr(queue.redis_client, "ack_message", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(queue, "POST_QA_AUTO_REPAIR_ENABLED", False)
    monkeypatch.setattr(
        queue,
        "run_one_stage",
        lambda *_args, **_kwargs: {"ok": False, "stage": "independent_final_review", "job_status": "failed"},
    )
    monkeypatch.setattr(queue, "_try_auto_rule_repair", lambda _public_id: (_ for _ in ()).throw(AssertionError("must not run")))
    monkeypatch.setattr(queue.threading.Thread, "start", lambda _self: None)
    monkeypatch.setattr(queue.threading.Thread, "join", lambda _self, **_kwargs: None)

    result = queue.consume_once(consumer="worker-test")

    assert result["ok"] is False
    assert "auto_rule_repair" not in result
    assert client.added == []


def test_codex_repair_message_runs_sidecar_then_queues_review(monkeypatch):
    from app.workflow_v2 import sidecar_apply

    client = FakeRedis()
    client.read_rows = [(b"1-0", {b"job_id": b"job-1", b"kind": b"codex_repair", b"repair_id": b"82"})]
    client.added = []
    client.set = lambda key, value, **_kwargs: client.values.setdefault(key, value) is value
    client.xadd = lambda stream, fields: client.added.append((stream, fields)) or b"2-0"
    client.delete = lambda _key: None
    monkeypatch.setattr(queue.redis_client, "client", client)
    monkeypatch.setattr(queue, "SIDECAR_ENABLED", True)
    monkeypatch.setattr(queue.redis_client, "read_stream", lambda *_args, **_kwargs: client.read_rows)
    monkeypatch.setattr(queue.redis_client, "ack_message", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        sidecar_apply,
        "run_registered_codex_repair",
        lambda public_id, repair_id: {
            "ok": True,
            "kind": "codex_repair",
            "job_id": public_id,
            "repair_id": str(repair_id),
            "job_status": "queued",
        },
    )
    monkeypatch.setattr(queue.threading.Thread, "start", lambda _self: None)
    monkeypatch.setattr(queue.threading.Thread, "join", lambda _self, **_kwargs: None)

    result = queue.consume_once(consumer="worker-test")

    assert result["repair_id"] == "82"
    assert result["next_message_id"] == "2-0"
    assert client.added == [(queue.STREAM, {"job_id": "job-1"})]


def test_codex_repair_message_is_audited_but_not_run_during_core_convergence(monkeypatch):
    client = FakeRedis()
    client.read_rows = [(b"1-0", {b"job_id": b"job-1", b"kind": b"codex_repair", b"repair_id": b"147"})]
    client.acked = []
    client.set = lambda key, value, **_kwargs: client.values.setdefault(key, value) is value
    client.delete = lambda _key: None
    monkeypatch.setattr(queue.redis_client, "client", client)
    monkeypatch.setattr(queue.redis_client, "read_stream", lambda *_args, **_kwargs: client.read_rows)
    monkeypatch.setattr(queue.redis_client, "ack_message", lambda _stream, _group, message_id: client.acked.append(message_id))
    monkeypatch.setattr(queue, "SIDECAR_ENABLED", False)
    monkeypatch.setattr(queue.threading.Thread, "start", lambda _self: None)
    monkeypatch.setattr(queue.threading.Thread, "join", lambda _self, **_kwargs: None)

    result = queue.consume_once(consumer="worker-test")

    assert result == {
        "ok": False,
        "job_id": "job-1",
        "repair_id": "147",
        "kind": "codex_repair",
        "paused": True,
        "reason": "core_convergence_mode",
    }
    assert client.acked == [b"1-0"]


def test_enqueue_codex_repair_is_disabled_during_core_convergence(monkeypatch):
    monkeypatch.setattr(queue, "SIDECAR_ENABLED", False)

    try:
        queue.enqueue_codex_repair("job-1", 147)
    except RuntimeError as exc:
        assert "paused" in str(exc)
    else:
        raise AssertionError("sidecar enqueue must be disabled")
