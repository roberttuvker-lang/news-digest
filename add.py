#!/usr/bin/env python3
"""news-digest store and dedupe engine.

Stdlib only. The agent never edits data.json or data.js by hand — it calls this.

    python add.py recent --days 60 --limit 120
    python add.py add --stream ai --run morning-0450 --max 8 --in candidates.json
    python add.py verify

candidates.json is a JSON list of objects:

    [{"headline": "...", "blurb": "...", "url": "https://...",
      "category": "Models"}]

`category` is optional and only used by the Sunday AI stream
(Models / Tools / Companies / Policy).
"""

import argparse
import difflib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_JSON = os.path.join(HERE, "data.json")
DATA_JS = os.path.join(HERE, "data.js")
INDEX = os.path.join(HERE, "index.html")

JS_PREFIX = "window.NEWS_DATA = "
JS_SUFFIX = ";\n"

STREAMS = ("ai", "morning", "midday", "afternoon")
CATEGORIES = ("Models", "Tools", "Companies", "Policy")

# Deliberately small. Stripping too much makes unrelated headlines collide.
STOPWORDS = {
    "a", "an", "and", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "its", "of", "on", "or", "that", "the", "this", "to",
    "was", "were", "with",
}

# A title is a duplicate only if BOTH hold. Sequence ratio alone kills two
# genuinely different stories about the same company; token overlap alone is
# far too eager.
TITLE_RATIO = 0.85
TITLE_JACCARD = 0.6
TITLE_WINDOW_DAYS = 120


# ---------------------------------------------------------------- keys

def canon_url(url):
    """Canonical form used for exact-duplicate detection."""
    parts = urlsplit(url.strip())
    host = (parts.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if ":" in host:  # strip a default port
        host = host.split(":", 1)[0]
    path = parts.path or ""
    # Syndicated copies differ only in tracking params and AMP suffixes.
    path = re.sub(r"/amp/?$", "", path)
    path = path.rstrip("/")
    return (host + path).lower()


def source_of(url):
    host = (urlsplit(url.strip()).netloc or "").lower()
    return host[4:] if host.startswith("www.") else host


def title_key(headline):
    s = headline.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    tokens = [t for t in s.split() if t and t not in STOPWORDS]
    return " ".join(tokens)


def _tokens(key):
    return set(key.split())


def titles_collide(a, b):
    if not a or not b:
        return False
    if difflib.SequenceMatcher(None, a, b).ratio() < TITLE_RATIO:
        return False
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return False
    jaccard = len(ta & tb) / len(ta | tb)
    return jaccard >= TITLE_JACCARD


# ---------------------------------------------------------------- store

def blank():
    return {"version": 1, "updated": None, "stories": [], "runs": []}


def load():
    if not os.path.exists(DATA_JSON):
        return blank()
    with open(DATA_JSON, encoding="utf-8") as fh:
        return json.load(fh)


def _atomic_write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)


def save(data):
    """Write data.json and data.js together. They must never drift."""
    data["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = json.dumps(data, indent=2, ensure_ascii=False)
    _atomic_write(DATA_JSON, body + "\n")
    # data.js exists so the local clone works from file:// — fetch() is blocked
    # there by CORS, a <script src> tag is not.
    _atomic_write(DATA_JS, JS_PREFIX + body + JS_SUFFIX)


# ---------------------------------------------------------------- commands

def cmd_recent(args):
    data = load()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).strftime("%Y-%m-%d")
    rows = [s for s in data["stories"] if s.get("date", "") >= cutoff]
    rows.sort(key=lambda s: s.get("date", ""), reverse=True)
    rows = rows[: args.limit]
    if not rows:
        print("(nothing logged yet — everything is fair game)")
        return 0
    print("Already covered — do NOT report any of these again:")
    for s in rows:
        print("- %s  [%s] %s" % (s["headline"], s.get("date", "?"), s["url"]))
    return 0


def cmd_add(args):
    raw = sys.stdin.read() if args.infile == "-" else open(args.infile, encoding="utf-8").read()
    try:
        cands = json.loads(raw)
    except json.JSONDecodeError as exc:
        print("candidates file is not valid JSON: %s" % exc, file=sys.stderr)
        return 1
    if isinstance(cands, dict) and "stories" in cands:
        cands = cands["stories"]
    if not isinstance(cands, list):
        print("candidates must be a JSON list", file=sys.stderr)
        return 1

    data = load()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    window = (datetime.now(timezone.utc) - timedelta(days=TITLE_WINDOW_DAYS)).strftime("%Y-%m-%d")

    existing_urls = {s["url_key"] for s in data["stories"]}
    recent_titles = [s["title_key"] for s in data["stories"] if s.get("date", "") >= window]

    accepted, rejected = [], []

    for cand in cands:
        if len(accepted) >= args.max:
            rejected.append({"url": cand.get("url", ""), "reason": "over-max"})
            continue

        headline = (cand.get("headline") or "").strip()
        blurb = (cand.get("blurb") or "").strip()
        url = (cand.get("url") or "").strip()
        if not headline or not url:
            rejected.append({"url": url, "reason": "missing-field"})
            continue

        ukey = canon_url(url)
        tkey = title_key(headline)

        if ukey in existing_urls:
            rejected.append({"url": url, "reason": "url-dup"})
            continue
        if any(titles_collide(tkey, prev) for prev in recent_titles):
            rejected.append({"url": url, "reason": "title-dup"})
            continue

        category = cand.get("category")
        if category not in CATEGORIES:
            category = None

        story = {
            "stream": args.stream,
            "run": args.run,
            "date": today,
            "headline": headline,
            "blurb": blurb,
            "url": url,
            "source": source_of(url),
            "url_key": ukey,
            "title_key": tkey,
        }
        if category:
            story["category"] = category

        accepted.append(story)
        # Guard against the batch repeating itself, not just the archive.
        existing_urls.add(ukey)
        recent_titles.append(tkey)

    data["stories"].extend(accepted)
    data["runs"].append({
        "run": args.run,
        "stream": args.stream,
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "accepted": len(accepted),
        "rejected": len(rejected),
    })
    save(data)

    print(json.dumps({
        "accepted": [{"headline": s["headline"], "url": s["url"]} for s in accepted],
        "rejected": rejected,
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_verify(args):
    problems = []

    if not os.path.exists(DATA_JSON):
        print("FAIL: data.json missing", file=sys.stderr)
        return 1
    try:
        with open(DATA_JSON, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        print("FAIL: data.json does not parse: %s" % exc, file=sys.stderr)
        return 1

    required = ("stream", "run", "date", "headline", "url", "url_key", "title_key")
    seen = {}
    for i, s in enumerate(data.get("stories", [])):
        missing = [f for f in required if not s.get(f)]
        if missing:
            problems.append("story %d missing %s" % (i, ", ".join(missing)))
        if s.get("stream") not in STREAMS:
            problems.append("story %d has unknown stream %r" % (i, s.get("stream")))
        key = s.get("url_key")
        if key in seen:
            problems.append("duplicate url_key %r (stories %d and %d)" % (key, seen[key], i))
        else:
            seen[key] = i

    if not os.path.exists(DATA_JS):
        problems.append("data.js missing")
    else:
        with open(DATA_JS, encoding="utf-8") as fh:
            js = fh.read()
        if not js.startswith(JS_PREFIX):
            problems.append("data.js has the wrong prefix")
        else:
            try:
                mirrored = json.loads(js[len(JS_PREFIX):].rstrip().rstrip(";"))
                if mirrored != data:
                    problems.append("data.js and data.json have drifted apart")
            except json.JSONDecodeError as exc:
                problems.append("data.js does not parse: %s" % exc)

    if not os.path.exists(INDEX):
        problems.append("index.html missing")

    if problems:
        print("FAIL", file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        return 1

    print("OK: %d stories, %d runs, no duplicates, data.js in sync"
          % (len(data.get("stories", [])), len(data.get("runs", []))))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("recent", help="print what has already been covered")
    p.add_argument("--days", type=int, default=60)
    p.add_argument("--limit", type=int, default=120)
    p.set_defaults(func=cmd_recent)

    p = sub.add_parser("add", help="dedupe candidates and append the survivors")
    p.add_argument("--stream", required=True, choices=STREAMS)
    p.add_argument("--run", required=True)
    p.add_argument("--max", type=int, default=3)
    p.add_argument("--in", dest="infile", default="candidates.json")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("verify", help="check the store is intact")
    p.set_defaults(func=cmd_verify)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
