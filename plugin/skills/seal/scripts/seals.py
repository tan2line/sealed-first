#!/usr/bin/env python3
"""Sealed First local log. Works in any agent that can run Python.

The log is one JSON file (a list of seals), the same shape the sealedfirst.com app
imports and exports, so a log can move between your AI tools and the browser app.

Location: $SEALED_FIRST_LOG, else ~/.sealed-first/seals.json

Commands
  new --q TEXT --take TEXT [--conf 75] [--tag policy]   seal a take; prints the record
  update ID key=value [key=value ...]                    set fields (values parsed as JSON when possible)
  get ID                                                 print one seal
  list [--status sealed|revealed|judged|resolved]        print seals, newest first
  path                                                   print the log location

Sealed fields (q, take, conf, createdAt, hash) cannot be changed after sealing.
"""
import argparse, hashlib, json, os, secrets, sys, time

TAGS = {"clinical", "policy", "venture", "technical", "other"}
LOCKED = {"q", "take", "conf", "createdAt", "hash", "id"}
STATUSES = ["sealed", "revealed", "judged", "resolved"]


def log_path():
    return os.environ.get("SEALED_FIRST_LOG") or os.path.join(os.path.expanduser("~"), ".sealed-first", "seals.json")


def load():
    p = log_path()
    if not os.path.exists(p):
        return []
    with open(p) as fh:
        data = json.load(fh)
    return data.get("seals", []) if isinstance(data, dict) else data


def save(seals):
    p = log_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(seals, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, p)


def fingerprint(q, take, created):
    # Must match the browser app: SHA-256 of q + "\n" + take + "\n" + createdAt, first 12 hex chars.
    return hashlib.sha256(f"{q}\n{take}\n{created}".encode()).hexdigest()[:12]


def parse_val(v):
    try:
        return json.loads(v)
    except (json.JSONDecodeError, ValueError):
        return v


def find(seals, sid):
    for s in seals:
        if s.get("id") == sid:
            return s
    sys.exit(f"No seal with id {sid}. Run `list` to see ids.")


def main():
    ap = argparse.ArgumentParser(description="Sealed First local log")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("--q", required=True)
    n.add_argument("--take", required=True)
    n.add_argument("--conf", type=int, default=75)
    n.add_argument("--tag", default="other")
    u = sub.add_parser("update")
    u.add_argument("id")
    u.add_argument("pairs", nargs="+")
    g = sub.add_parser("get")
    g.add_argument("id")
    l = sub.add_parser("list")
    l.add_argument("--status", choices=STATUSES)
    sub.add_parser("path")
    a = ap.parse_args()

    if a.cmd == "path":
        print(log_path())
        return
    seals = load()
    if a.cmd == "new":
        q, take = a.q.strip(), a.take.strip()
        if len(q) < 5 or len(take) < 3:
            sys.exit("Both the question and the take are required.")
        if not 50 <= a.conf <= 100:
            sys.exit("Confidence must be between 50 and 100.")
        created = int(time.time() * 1000)
        s = {"id": secrets.token_hex(10), "q": q, "take": take, "conf": a.conf,
             "tag": a.tag if a.tag in TAGS else "other", "createdAt": created,
             "hash": fingerprint(q, take, created), "status": "sealed"}
        seals.append(s)
        save(seals)
        print(json.dumps(s, ensure_ascii=False))
    elif a.cmd == "update":
        s = find(seals, a.id)
        for pair in a.pairs:
            if "=" not in pair:
                sys.exit(f"Use key=value, got: {pair}")
            k, v = pair.split("=", 1)
            if k in LOCKED:
                sys.exit(f"{k} is sealed and can't be changed.")
            s[k] = parse_val(v)
        if s.get("status") and s["status"] not in STATUSES:
            sys.exit(f"Status must be one of {', '.join(STATUSES)}.")
        save(seals)
        print(json.dumps(s, ensure_ascii=False))
    elif a.cmd == "get":
        print(json.dumps(find(seals, a.id), ensure_ascii=False, indent=1))
    elif a.cmd == "list":
        rows = [s for s in seals if not a.status or s.get("status") == a.status]
        rows.sort(key=lambda s: -(s.get("createdAt") or 0))
        print(json.dumps(rows, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
