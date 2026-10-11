#!/usr/bin/env python3
"""Sealed First Team oversight evidence report. Mirrors the team page's metrics and status logic.

Usage: python3 team_report.py <evidence.csv> [period_days]
   or: python3 team_report.py <items_dir> <outcomes_dir> [period_days]
  evidence.csv: the "Export evidence" file from a Sealed First Team page.
  items_dir: directory holding one sub-directory per reviewer id, each with that reviewer's item JSON files
             (ArtifactData out_dir output of reviews/<uid>/items), or a flat directory whose files carry "uid".
  outcomes_dir: ArtifactData out_dir output of the outcomes collection (may be empty or missing).
  period_days: 30, 90 (default) or 0 for all time.
"""
import csv, json, os, sys, time
from datetime import datetime

DAY = 86400000


def body(d):
    b = d.get("data", d) if isinstance(d, dict) else {}
    b = dict(b) if isinstance(b, dict) else {}
    b.setdefault("id", d.get("id"))
    return b


def load_items(path):
    items = []
    for root, _, files in os.walk(path):
        for f in files:
            if not f.endswith(".json"):
                continue
            with open(os.path.join(root, f)) as fh:
                b = body(json.load(fh))
            if "ref" not in b:
                continue
            if "uid" not in b:
                parts = os.path.relpath(root, path).split(os.sep)
                # out_dir layout: <dir>/reviews/<uid>/items/<id>.json
                b["uid"] = parts[-2] if len(parts) >= 2 and parts[-1] == "items" else parts[0]
            if b.get("id") is None:
                b["id"] = f[:-5]
            items.append(b)
    return items


def load_outcomes(path):
    out = {}
    if not path or not os.path.isdir(path):
        return out
    for root, _, files in os.walk(path):
        for f in files:
            if f.endswith(".json"):
                with open(os.path.join(root, f)) as fh:
                    d = json.load(fh)
                out[d.get("id") or f[:-5]] = body(d)
    return out


def iso_ms(v):
    try:
        return int(datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp() * 1000)
    except (ValueError, AttributeError):
        return 0


def load_csv(path):
    items, outcomes = [], {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for i, r in enumerate(csv.DictReader(fh)):
            uid = r.get("reviewer_id") or r.get("reviewer") or "reviewer"
            iid = r.get("fingerprint") or f"row{i}"
            items.append({"id": iid, "uid": uid, "ref": r.get("case_ref", ""), "sealed": r.get("sealed_decision"),
                          "ai": r.get("ai_recommendation"), "final": r.get("final_decision"), "why": r.get("reason", ""),
                          "attested": (r.get("attested_independent") or "").lower() == "yes",
                          "createdAt": iso_ms(r.get("sealed_at")), "submittedAt": iso_ms(r.get("submitted_at")), "status": "submitted"})
            if r.get("correct_decision"):
                outcomes[f"{uid}__{iid}"] = {"correct": r["correct_decision"]}
    return items, outcomes


def pct(a, b):
    return round(100 * a / b) if b else None


def metrics(items, outcomes, period, now):
    sub = [x for x in items if x.get("status") == "submitted" and (period == 0 or (x.get("submittedAt") or 0) >= now - period * DAY)]
    n = len(sub)
    dis = [x for x in sub if x.get("sealed") != x.get("ai")]
    changed = [x for x in sub if x.get("final") != x.get("sealed")]
    checked = []
    for x in sub:
        o = outcomes.get(f"{x['uid']}__{x['id']}")
        if o and o.get("correct") and o["correct"] != "unknown":
            checked.append((x, o["correct"]))
    flips = [(x, c) for x, c in checked if x.get("final") != x.get("sealed")]
    return {
        "reviews": n, "reviewers": len({x["uid"] for x in sub}),
        "matched_ai_before_seeing": pct(n - len(dis), n),
        "switched_to_ai_after_disagreeing": pct(len([x for x in dis if x.get("final") == x.get("ai")]), len(dis)), "disagreements": len(dis),
        "overrode_ai": pct(len([x for x in sub if x.get("final") != x.get("ai")]), n),
        "changes_with_reason": pct(len([x for x in changed if len((x.get("why") or "").strip()) >= 10]), len(changed)), "changed": len(changed),
        "attested_independent": pct(len([x for x in sub if x.get("attested")]), n),
        "outcome_checks": len(checked),
        "sealed_right": pct(len([1 for x, c in checked if x.get("sealed") == c]), len(checked)),
        "ai_right": pct(len([1 for x, c in checked if x.get("ai") == c]), len(checked)),
        "final_right": pct(len([1 for x, c in checked if x.get("final") == c]), len(checked)),
        "switches_helped": len([1 for x, c in flips if x.get("sealed") != c and x.get("final") == c]),
        "switches_hurt": len([1 for x, c in flips if x.get("sealed") == c and x.get("final") != c]),
    }


def status(m):
    if m["reviews"] < 20:
        return "Gathering evidence"
    if (m["switched_to_ai_after_disagreeing"] or 0) >= 50 and m["outcome_checks"] >= 10 and m["switches_hurt"] > m["switches_helped"]:
        return "Anchoring risk"
    if (m["matched_ai_before_seeing"] or 0) >= 95 and (m["overrode_ai"] or 0) < 2:
        return "Rubber-stamp risk"
    if m["changed"] >= 5 and (m["changes_with_reason"] or 0) < 80:
        return "Undocumented changes"
    if (m["attested_independent"] or 0) < 90:
        return "Independence not attested"
    return "Oversight working"


def main():
    if sys.argv[1].lower().endswith(".csv"):
        items, outcomes = load_csv(sys.argv[1])
        period = int(sys.argv[2]) if len(sys.argv) > 2 else 90
    else:
        items = load_items(sys.argv[1])
        outcomes = load_outcomes(sys.argv[2] if len(sys.argv) > 2 else None)
        period = int(sys.argv[3]) if len(sys.argv) > 3 else 90
    now = int(time.time() * 1000)
    m = metrics(items, outcomes, period, now)
    by = {}
    for x in items:
        by.setdefault(x["uid"], []).append(x)
    rows = [{"reviewer_id": u, **metrics(xs, outcomes, period, now)} for u, xs in by.items()]
    rows = [r for r in rows if r["reviews"]]
    pending = len([x for x in items if x.get("status") == "submitted" and f"{x['uid']}__{x['id']}" not in outcomes])
    print(json.dumps({"period_days": period, "status": status(m), "team": m, "by_reviewer": rows,
                      "awaiting_outcome": pending, "open_unsubmitted": len([x for x in items if x.get("status") != "submitted"])}, indent=1))


if __name__ == "__main__":
    main()
