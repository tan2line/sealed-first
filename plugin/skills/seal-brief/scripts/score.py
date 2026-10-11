#!/usr/bin/env python3
"""Sealed First personal score. Mirrors the page's formula exactly.

Usage: python3 score.py <seals_dir_or_json> [weekly_target]
  seals_dir_or_json: a directory of per-document JSON files (ArtifactData out_dir output,
  each file either the raw body or {"id","data",...}) or one JSON file holding a list.
Prints one JSON object with the overall score, per-domain rows, flags and open items.
"""
import json, os, sys, time

DAY = 86400000
TAGS = [("clinical", "Clinical"), ("policy", "Policy & governance"), ("venture", "Venture"),
        ("technical", "Technical"), ("other", "Other")]


def load(path):
    docs = []
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for f in files:
                if f.endswith(".json"):
                    with open(os.path.join(root, f)) as fh:
                        docs.append(json.load(fh))
    else:
        with open(path) as fh:
            d = json.load(fh)
            docs = d if isinstance(d, list) else d.get("documents", [d])
    out = []
    for d in docs:
        body = d.get("data", d) if isinstance(d, dict) else {}
        if not isinstance(body, dict) or "q" not in body:
            continue
        body = dict(body)
        body.setdefault("id", d.get("id"))
        out.append(body)
    return out


def pct(a, b):
    return round(100 * a / b) if b else None


def stats(seals, weekly, tag="all", now=None):
    now = now or int(time.time() * 1000)
    in_tag = lambda s: tag == "all" or (s.get("tag") or "other") == tag
    W = [s for s in seals if (s.get("createdAt") or 0) >= now - 90 * DAY and in_tag(s)]
    judged = [s for s in W if s.get("status") in ("judged", "resolved")]
    div = [s for s in judged if s.get("verdict") and s.get("verdict") != "agree"]
    agreed = [s for s in judged if s.get("verdict") == "agree"]
    switched = [s for s in div if s.get("final") == "switched"]
    res = [s for s in W if s.get("status") == "resolved" and s.get("outcome") in ("me", "ai", "both", "neither")]
    me_r = lambda s: s.get("outcome") in ("me", "both")
    ai_r = lambda s: s.get("outcome") in ("ai", "both")

    def call_r(s):
        f = s.get("final")
        if f == "held":
            return me_r(s)
        if f == "switched":
            return ai_r(s)
        return s.get("outcome") != "neither"

    me_acc = pct(sum(map(me_r, res)), len(res))
    ai_acc = pct(sum(map(ai_r, res)), len(res))
    call_acc = pct(sum(map(call_r, res)), len(res))
    avg_conf = round(sum((s.get("conf") or 50) for s in res) / len(res)) if res else None
    gap = (avg_conf - me_acc) if res else None
    calib = max(0, 100 - 2 * abs(gap)) if res else None
    recent = len([s for s in seals if (s.get("createdAt") or 0) >= now - 28 * DAY and in_tag(s)])
    disc = min(100, pct(recent, weekly * 4)) if tag == "all" else None
    changed = [s for s in judged if s.get("final") in ("updated", "switched")]
    reasoned = pct(len([s for s in changed if len((s.get("why") or "").strip()) >= 10]), len(changed)) if changed else None
    parts = [(v, w) for v, w in ((call_acc, 45), (calib, 25), (disc, 15), (reasoned, 15)) if v is not None]
    wsum = sum(w for _, w in parts)
    score = round(sum(v * w for v, w in parts) / wsum) if res and wsum else None
    return {
        "score": score, "provisional": len(res) < 5, "resolved": len(res), "judged": len(judged), "seals": len(W),
        "final_calls_right": call_acc, "calibration": calib, "confidence_gap": gap, "cadence": disc,
        "reasoned_changes": reasoned, "you_right": me_acc, "ai_right": ai_acc,
        "divergence": pct(len(div), len(judged)), "deference": pct(len(switched), len(div)),
        "agreements": len(agreed), "agreements_redteamed": pct(len([s for s in agreed if s.get("redteam")]), len(agreed)),
        "recent_28d": recent,
    }


def band(s):
    if s is None:
        return "Not scored yet"
    return "Strong retention" if s >= 80 else "Holding" if s >= 60 else "Slipping" if s >= 40 else "Deferring"


def flags(st, rows):
    out = []
    if st["judged"] >= 8 and st["divergence"] is not None and st["divergence"] < 15:
        out.append("Almost never disagrees with the AI.")
    if st["resolved"] >= 5 and (st["deference"] or 0) >= 60 and st["ai_right"] is not None and st["ai_right"] <= st["you_right"]:
        out.append("Switches to the AI in most disagreements without the record supporting it.")
    if st["resolved"] >= 5 and st["confidence_gap"] is not None and abs(st["confidence_gap"]) >= 20:
        out.append(("Overconfident" if st["confidence_gap"] > 0 else "Underconfident") + f" by {abs(st['confidence_gap'])} points.")
    if st["agreements"] >= 5 and st["agreements_redteamed"] is not None and st["agreements_redteamed"] < 20:
        out.append("Rarely red-teams agreements.")
    for r in rows:
        s = r["stats"]
        if s["resolved"] >= 3 and (s["deference"] or 0) >= 60 and s["ai_right"] is not None and s["ai_right"] <= s["you_right"]:
            out.append(f"Defers more than the record supports in {r['domain']}.")
    return out


def main():
    seals = load(sys.argv[1])
    weekly = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    now = int(time.time() * 1000)
    st = stats(seals, weekly, now=now)
    rows = [{"domain": n, "stats": stats(seals, weekly, t, now)} for t, n in TAGS]
    rows = [r for r in rows if r["stats"]["seals"] > 0]
    wk_start = now - 7 * DAY
    open_items = sorted(
        [{"q": s["q"][:90], "status": s.get("status"), "days_waiting": (now - (s.get("judgedAt") or s.get("createdAt") or now)) // DAY}
         for s in seals if s.get("status") in ("sealed", "revealed", "judged")],
        key=lambda x: -x["days_waiting"])
    print(json.dumps({
        "overall": st, "band": band(st["score"]), "by_domain": rows, "flags": flags(st, rows),
        "last_7_days": {
            "sealed": len([s for s in seals if (s.get("createdAt") or 0) >= wk_start]),
            "judged": len([s for s in seals if (s.get("judgedAt") or 0) >= wk_start]),
            "resolved": len([s for s in seals if (s.get("resolvedAt") or 0) >= wk_start]),
        },
        "weekly_target": weekly, "open_items": open_items[:10], "total_seals": len(seals),
    }, indent=1))


if __name__ == "__main__":
    main()
