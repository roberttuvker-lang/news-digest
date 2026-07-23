# news-digest

Where the three Claude Code cloud routines put their briefings, so there is something to
open instead of a session transcript that vanishes — and so the same story never gets
reported twice.

**Read it:** https://dovid.github.io/news-digest/ *(replace with the real username)*
**Local clone:** `C:\Users\dovid\news-digest\index.html` — opens by double-click, offline.

## The routines

| Routine | Local time | Stream |
|---|---|---|
| `good-news-morning-0450-ai-sundays` | 04:50 | `ai` on Sundays, `morning` otherwise |
| `good-news-midday-1002` | 10:02 | `midday` |
| `good-news-afternoon-1514` | 15:14 | `afternoon` |

They run in Anthropic's cloud, not on any local machine. Each clones this repo, appends
through `add.py`, and pushes.

## Files

- `index.html` — the page. Self-contained, no CDN.
- `data.js` — the store as `window.NEWS_DATA = {...}`. **This is what the page loads.**
- `data.json` — the same content as plain JSON. What `add.py` reads and writes.
- `add.py` — the engine. Nothing else may write the data files.

`data.js` exists because Chrome blocks `fetch()` from `file://`. A `<script src>` tag is not
blocked, so the local clone works by double-click. `add.py` writes both files on every run
and `verify` fails if they drift apart.

## The contract for a routine run

```bash
python add.py recent --days 60                    # what not to repeat
# ...searches, then write candidates.json...
python add.py add --stream midday --run midday-1002 --max 3
python add.py verify                              # non-zero -> commit nothing
git add -A && git commit -m "midday 2026-07-26" && git push
```

`candidates.json` is a JSON list. `category` is optional and only used by the `ai` stream:

```json
[{"headline": "...", "blurb": "...", "url": "https://...", "category": "Models"}]
```

**One pass only.** Whatever survives dedupe is what gets published — three stories, two, or
none. There is no retry round. A short honest entry beats a padded one, and searching again
costs most on exactly the slow news days when it finds least.

The Sunday `ai` run is the exception on depth: 8–10 searches, up to 12 candidates,
`--max 8`, grouped under Models / Tools / Companies / Policy, every item under 40 words and
the whole entry under ~500. Depth comes from the searching, not the prose.

## Dedupe

Global across all streams — a story found at 10:02 cannot resurface at 15:14 or next
Tuesday. Two independent rules, both in code so they are auditable rather than a judgement
call:

- **`url_key`** — lowercase host, `www.` dropped, query string and fragment dropped,
  trailing `/` and `/amp` stripped. Exact match rejects, at any age.
- **`title_key`** — lowercased, punctuation and stopwords stripped. Rejects only when
  sequence similarity ≥ 0.85 **and** token overlap ≥ 0.6 against anything from the last 120
  days. Both conditions: similarity alone would kill two genuinely different stories about
  the same company.

Verified behaviour — a syndicated copy of the same story at a different outlet with a
reworded headline is rejected as `title-dup`; "Anthropic opens a London office" alongside
"Anthropic ships Opus 4.8" is accepted.

## Checking it

```bash
python add.py verify
```

Exit 0 only when `data.json` parses, every story has all required fields, no `url_key`
repeats, `data.js` matches `data.json`, and `index.html` is present.
