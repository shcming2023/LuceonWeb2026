#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import SessionLocal
from app.models.material import CodexSkillJob
from app.services.codex_skill_jobs import CodexSkillJobError, publish_staging_job, run_codex_skill_job, run_dry_run_job


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Luceon Codex skill jobs in dry-run mode.")
    parser.add_argument("--job-id", type=int, default=0, help="Specific codex_skill_jobs.id to run.")
    parser.add_argument("--limit", type=int, default=1, help="Number of queued jobs to dry-run.")
    parser.add_argument("--staging-root", default="/data/codex-skill-work", help="Local dry-run staging root.")
    parser.add_argument("--publish-staging", action="store_true", help="Publish an existing dry-run staging directory to MinIO.")
    parser.add_argument("--run-codex", action="store_true", help="Invoke Codex CLI to produce real staging artifacts.")
    parser.add_argument("--timeout", type=int, default=0, help="Seconds before a live Codex run is marked failed; 0 disables timeout.")
    parser.add_argument("--target-bucket", default="eduassets-elegantbook", help="Publish bucket for --publish-staging.")
    parser.add_argument("--no-promote", action="store_true", help="Publish without promoting the output as current.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.publish_staging:
            query = db.query(CodexSkillJob).filter(CodexSkillJob.status.in_(["dry_run_succeeded", "validating"]))
        elif args.run_codex:
            query = db.query(CodexSkillJob).filter(CodexSkillJob.status.in_(["queued", "running", "dry_run_succeeded"]))
        else:
            query = db.query(CodexSkillJob).filter(CodexSkillJob.status == "queued")
        if args.job_id:
            query = query.filter(CodexSkillJob.id == args.job_id)
        jobs = query.order_by(CodexSkillJob.created_at.asc(), CodexSkillJob.id.asc()).limit(max(1, args.limit)).all()
        if not jobs:
            print("No matching Codex skill job found.")
            return 0
        failed = 0
        for job in jobs:
            try:
                if args.publish_staging:
                    publish_staging_job(db, job, target_bucket=args.target_bucket, promote=not args.no_promote)
                    action = "Publish"
                elif args.run_codex:
                    run_codex_skill_job(db, job, staging_root=Path(args.staging_root), timeout=args.timeout or None)
                    action = "Codex"
                else:
                    run_dry_run_job(db, job, staging_root=Path(args.staging_root))
                    action = "Dry-run"
                db.commit()
                db.refresh(job)
                print(f"{action} succeeded for job {job.id}: {job.staging_dir}")
            except CodexSkillJobError as exc:
                if job.status == "failed":
                    db.commit()
                else:
                    db.rollback()
                failed += 1
                print(f"Codex skill job {job.id} failed: {exc}", file=sys.stderr)
        if failed:
            return 2
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
