#!/usr/bin/env python3
"""Clean-scope UAT smoke checks for a running LuceonWeb review stack.

The script intentionally skips GPU, Standard, and Final Review checks.
It verifies auth, MinIO/model readiness, material sync, existing Clean samples,
PDF/review APIs, and the review-asset invariant that protects downstream
materials from being relinked to input-only assets.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any


DEFAULT_API_BASE = "http://localhost:28080/api"
DEFAULT_DB = str(Path(__file__).resolve().parents[2] / "runtime/backend/mineru.db")
DEFAULT_EMAIL = "uat-clean-smoke@example.test"


@dataclass
class HttpResult:
    status: int
    body: bytes
    headers: Any


class ApiClient:
    def __init__(self, api_base: str) -> None:
        self.api_base = api_base.rstrip("/")
        self.cookies = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResult:
        url = f"{self.api_base}{path}"
        data = None
        request_headers = dict(headers or {})
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
        request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
        try:
            with self.opener.open(request, timeout=60) as response:
                return HttpResult(response.status, response.read(), response.headers)
        except urllib.error.HTTPError as exc:
            return HttpResult(exc.code, exc.read(), exc.headers)

    def json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
        result = self.request(method, path, payload=payload)
        try:
            return result.status, json.loads(result.body.decode("utf-8"))
        except json.JSONDecodeError:
            return result.status, {"_raw": result.body.decode("utf-8", errors="replace")}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_status(label: str, status: int, expected: set[int]) -> None:
    if status not in expected:
        fail(f"{label} returned HTTP {status}, expected {sorted(expected)}")


def bool_value(value: Any) -> bool:
    return str(value).lower() in {"1", "true", "yes"}


def review_asset_invariant(db_path: str) -> dict[str, int]:
    path = Path(db_path)
    if not path.exists():
        return {"db_exists": 0, "downstream_total": 0, "downstream_input_review_asset": -1}
    conn = sqlite3.connect(path)
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            select count(*) as downstream_total,
                   sum(case when coalesce(ra.review_stage,'') = 'input' then 1 else 0 end)
                     as downstream_input_review_asset
            from materials m
            left join review_assets ra on ra.id = m.review_asset_id
            where m.ignored = 0
              and (
                m.mineru_manifest_object is not null
                or m.popo_manifest_object is not null
                or m.raw_manifest_object is not null
                or m.clean_manifest_object is not null
                or m.standard_manifest_object is not null
              )
            """
        ).fetchone()
    finally:
        conn.close()
    return {
        "db_exists": 1,
        "downstream_total": int(row["downstream_total"] or 0),
        "downstream_input_review_asset": int(row["downstream_input_review_asset"] or 0),
    }


def pick_clean_samples(materials: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for row in materials:
        if not row.get("review_asset_id"):
            continue
        if not bool_value(row.get("raw_available")) or not bool_value(row.get("clean_available")):
            continue
        samples.append(row)
        if len(samples) >= count:
            break
    return samples


def body_len(result: HttpResult) -> int:
    return len(result.body or b"")


def authenticate(client: ApiClient, email: str, password: str) -> tuple[int, dict[str, Any], str]:
    register_status, register_body = client.json("POST", "/auth/register", {"email": email, "password": password})
    if register_status == 200:
        return register_status, register_body, "registered"
    if register_status != 409:
        require_status("auth.register", register_status, {200, 409})

    login_status, login_body = client.json("POST", "/auth/login", {"email": email, "password": password})
    require_status("auth.login existing smoke user", login_status, {200})
    return login_status, login_body, "reused"


def run(args: argparse.Namespace) -> dict[str, Any]:
    client = ApiClient(args.api_base)
    email = args.email
    password = args.password

    auth_status, auth_body, auth_mode = authenticate(client, email, password)
    me_status, me_body = client.json("GET", "/auth/me")
    require_status("auth.me", me_status, {200})

    wrong_client = ApiClient(args.api_base)
    wrong_status, wrong_body = wrong_client.json("POST", "/auth/login", {"email": email, "password": f"{password}-wrong"})
    require_status("auth.login wrong password", wrong_status, {401})

    minio_status, minio_body = client.json("POST", "/runtime/minio/check")
    require_status("runtime.minio.check", minio_status, {200})
    if not minio_body.get("contract_ok"):
        fail(f"MinIO contract is not ok: {minio_body}")

    model_status = 0
    model_body: Any = {"skipped": True}
    if not args.skip_model_check:
        model_status, model_body = client.json("POST", "/runtime/models/check")
        require_status("runtime.models.check", model_status, {200})
        if not model_body.get("ok"):
            fail(f"Model connectivity is not ok: {model_body}")

    sync_status, sync_body = client.json("POST", f"/materials/sync?limit={args.sync_limit}")
    require_status("materials.sync", sync_status, {200})
    summary_status, summary_body = client.json("GET", "/materials/summary")
    require_status("materials.summary", summary_status, {200})

    list_status, list_body = client.json("GET", f"/materials?stage=clean&page=1&page_size={args.page_size}")
    require_status("materials clean list", list_status, {200})
    samples = pick_clean_samples(list_body.get("materials") or [], args.samples)
    if len(samples) < args.samples:
        fail(f"Only found {len(samples)} Clean samples with review assets, expected {args.samples}")

    sample_results = []
    for row in samples:
        asset_id = str(row["review_asset_id"])
        material_id = str(row.get("material_id") or "")
        filename = str(row.get("filename") or row.get("title") or "")
        checks: dict[str, Any] = {}

        content = client.request("GET", f"/review/assets/{asset_id}/content", headers={"Range": "bytes=0-511"})
        require_status(f"asset {asset_id} content range", content.status, {206})
        checks["content_range"] = {"status": content.status, "bytes": body_len(content)}

        page_image = client.request("GET", f"/review/assets/{asset_id}/page_image?page=1&width=720")
        require_status(f"asset {asset_id} page image", page_image.status, {200})
        checks["page_image"] = {"status": page_image.status, "bytes": body_len(page_image)}

        for variant in ("markdown", "markdown_page", "popo"):
            parsed = client.request("GET", f"/review/assets/{asset_id}/parsed_content?variant={variant}")
            require_status(f"asset {asset_id} parsed {variant}", parsed.status, {200})
            checks[f"parsed_{variant}"] = {"status": parsed.status, "bytes": body_len(parsed)}

        source_status, source_body = client.json("GET", f"/review/assets/{asset_id}/source_map")
        require_status(f"asset {asset_id} source_map", source_status, {200})
        source_pages = len(source_body.get("pages") or []) if isinstance(source_body, dict) else 0
        checks["source_map"] = {"status": source_status, "pages": source_pages}

        outline_status, outline_body = client.json("GET", f"/review/assets/{asset_id}/outline_review")
        require_status(f"asset {asset_id} outline_review", outline_status, {200})
        directory_units = len(outline_body.get("directory_units") or []) if isinstance(outline_body, dict) else 0
        outline_summary = outline_body.get("summary") if isinstance(outline_body, dict) else {}
        checks["outline_review"] = {
            "status": outline_status,
            "directory_units": directory_units,
            "raw_available": bool(outline_summary.get("raw_markdown_available")),
            "clean_available": bool(outline_summary.get("clean_markdown_available")),
        }
        if directory_units <= 0:
            fail(f"asset {asset_id} has no outline directory units")
        if not checks["outline_review"]["raw_available"] or not checks["outline_review"]["clean_available"]:
            fail(f"asset {asset_id} outline review does not expose Raw and Clean markdown")

        sample_results.append(
            {
                "asset_id": asset_id,
                "material_id": material_id,
                "filename": filename,
                "checks": checks,
            }
        )

    invariant = review_asset_invariant(args.db_path)
    if invariant["downstream_input_review_asset"] != 0:
        fail(f"Downstream materials still point at input-only review assets: {invariant}")

    return {
        "status": "pass",
        "scope": "clean",
        "gpu_checked": False,
        "standard_checked": False,
        "final_review_checked": False,
        "auth": {
            "email": email,
            "mode": auth_mode,
            "auth_status": auth_status,
            "me_status": me_status,
            "wrong_password_status": wrong_status,
            "user_id": (auth_body.get("user") or {}).get("id") if isinstance(auth_body, dict) else "",
            "wrong_password_detail": wrong_body.get("detail") if isinstance(wrong_body, dict) else "",
            "me_email": (me_body or {}).get("email") if isinstance(me_body, dict) else "",
        },
        "runtime": {
            "minio_status": minio_status,
            "minio_contract_ok": bool(minio_body.get("contract_ok")),
            "model_status": model_status,
            "model_ok": bool(model_body.get("ok")) if isinstance(model_body, dict) else False,
            "model_skipped": bool(args.skip_model_check),
        },
        "materials": {
            "sync_status": sync_status,
            "summary_status": summary_status,
            "total": summary_body.get("total"),
            "availability": summary_body.get("availability"),
            "clean_list_status": list_status,
            "clean_total": list_body.get("total"),
        },
        "samples": sample_results,
        "review_asset_invariant": invariant,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Clean-scope UAT smoke checks against a LuceonWeb review stack.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help=f"API base URL, default: {DEFAULT_API_BASE}")
    parser.add_argument("--email", default=DEFAULT_EMAIL, help=f"UAT email, default: {DEFAULT_EMAIL}")
    parser.add_argument("--password", default="secret123", help="UAT password, default: secret123")
    parser.add_argument("--sync-limit", type=int, default=1000, help="Material sync limit, default: 1000")
    parser.add_argument("--page-size", type=int, default=20, help="Clean material page size, default: 20")
    parser.add_argument("--samples", type=int, default=3, help="Number of existing Clean samples to verify, default: 3")
    parser.add_argument("--skip-model-check", action="store_true", help="Skip LLM/Vision model connectivity check.")
    parser.add_argument("--db-path", default=DEFAULT_DB, help=f"SQLite DB path for invariant checks, default: {DEFAULT_DB}")
    return parser.parse_args()


def main() -> None:
    summary = run(parse_args())
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
