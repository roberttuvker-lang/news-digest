# Brighter

*news for a brighter future*

Where the three Claude Code cloud routines put their briefings, so there is something to
open instead of a session transcript that vanishes — and so the same story never gets
reported twice.

We do not write the news. Every story links to the outlet that reported it.

**Read it:** https://roberttuvker-lang.github.io/news-digest/
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

- `index.html` — the page. Self-contained: no CDN, no fonts, no libraries, no build.
- `data.js` — the store as `window.NEWS_DATA = {...}`. **This is what the page loads.**
- `data.json` — the same content as plain JSON. What `add.py` reads and writes.
- `add.py` — the engine. Nothing else may write the data files.
- `sw.js` + `manifest.webmanifest` + `icons/` — the installable app. See below.
- `backfill_topics.py` — assigns a topic to anything that landed without one.
- `make_assets.py` — regenerates the icons and `og.png`. Dev machine only (needs Pillow);
  the routines never call it, they only ever touch `add.py`, which stays stdlib.

`data.js` exists because Chrome blocks `fetch()` from `file://`. A `<script src>` tag is not
blocked, so the local clone works by double-click. `add.py` writes both files on every run
and `verify` fails if they drift apart.

## Topics

Every story carries a `topic`, one of exactly eight:

```
Science  Health  Environment  Nature  Space  Society  Technology  AI
```

That is what the filter row and the search run on, so "science" or "space nasa" find what
you would expect. The list is closed on purpose — an open vocabulary drifts, the routines
invent synonyms, and the filter row grows into an unusable wall.

A candidate with a missing or unrecognised topic does **not** get rejected: it falls back
(`AI` on the ai stream, `Society` elsewhere). The routines get one pass with no retries, so
a formatting slip must never cost a real story. `verify` then catches anything genuinely
broken.

`category` (Models / Tools / Companies / Policy) is separate: it is the Sunday AI
briefing's internal grouping.

## The installed app

The site is a PWA. Installed to a phone home screen it opens with no browser chrome and
works with no signal, serving the last issue from cache.

`sw.js` caches the shell cache-first and `data.js` network-first. Its `CACHE` constant is
**stamped by `add.py`**, from the same timestamp it writes onto `index.html`'s `data.js?v=`.
Never edit it by hand: a forgotten bump means the phone serves old news forever, and it
looks like the routine broke. `verify` fails if the two ever disagree.

## The contract for a routine run

```bash
python add.py recent --days 60                    # what not to repeat
# ...searches, then write candidates.json...
python add.py add --stream midday --run midday-1002 --max 3
python add.py verify                              # non-zero -> commit nothing
git add -A && git commit -m "midday 2026-07-26" && git push
```

`candidates.json` is a JSON list. `topic` is required on every item; `category` is optional
and only used by the `ai` stream:

```json
[{"headline": "...", "blurb": "...", "url": "https://...",
  "topic": "Science", "category": "Models"}]
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

Exit 0 only when `data.json` parses, every story has all required fields **including a
valid topic**, no `url_key` repeats, `data.js` matches `data.json`, `index.html` carries a
matching `?v=`, `sw.js` carries a matching cache version, and the manifest parses with
every icon it names present on disk.

That last group is the point: a broken deploy fails here, on the machine, rather than
silently on the phone.
