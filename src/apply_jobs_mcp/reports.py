"""Aggregate reports: applications.json + applications.md from the Store.

Learning notes:
- Reports are a pure projection of SQLite: any step of the pipeline can be
  verified by reading the report, and no report is ever "hand edited".
  Markdown is for humans, JSON is for machines, SQLite is the source.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import Store


def build_report(store: Store) -> dict[str, Any]:
    jobs = store.list_jobs(limit=500)
    apps = store.list_applications()
    summary: dict[str, int] = {}
    for j in jobs:
        summary[j["status"]] = summary.get(j["status"], 0) + 1
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "jobs": [
            {
                "id": j["id"],
                "url": j["url"],
                "source": j["source_id"],
                "title": j["title"],
                "employer": j["employer"],
                "location": j["location"],
                "remote": j["remote"],
                "compensation_raw": j["compensation_raw"],
                "compensation_inr_monthly": j["compensation_inr_monthly"],
                "currency": j["currency"],
                "status": j["status"],
                "score": j["role_match_score"],
                "reasons": j["reasons"],
                "visa_support": j["visa_support"],
                "discovered_at": j["discovered_at"],
            }
            for j in jobs
        ],
        "applications": [
            {
                "id": a["id"],
                "job_id": a["job_id"],
                "campaign_id": a["campaign_id"],
                "status": a["status"],
                "submitted_at": a["submitted_at"],
                "confirmation": a["confirmation"],
                "error": a["error"],
            }
            for a in apps
        ],
    }


def export_report(store: Store, report_dir: str | Path) -> dict[str, Path]:
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = build_report(store)

    json_path = report_dir / "applications.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [f"# Job applications report ({payload['generated_at']})", ""]
    if payload["summary"]:
        lines.append("## Summary")
        for status in sorted(payload["summary"]):
            lines.append(f"- {status}: {payload['summary'][status]}")
        lines.append("")
    lines.append("## Jobs")
    for j in sorted(payload["jobs"], key=lambda x: -x["score"]):
        comp = j["compensation_inr_monthly"]
        comp_s = f"₹{comp:,.0f}/mo" if comp is not None else j["compensation_raw"] or "n/a"
        loc = j["location"] or "n/a"
        lines.append(
            f"### {j['title']} - {j['employer'] or 'n/a'} "
            f"({j['status']}, score {j['score']:.0f})"
        )
        lines.append(f"- Source: {j['source']} | Location: {loc} | Comp: {comp_s}")
        lines.append(f"- Link: {j['url']}")
        if j["reasons"]:
            lines.append(f"- Why: {', '.join(j['reasons'])}")
        lines.append("")
    md_path = report_dir / "applications.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}
