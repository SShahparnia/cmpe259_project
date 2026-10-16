# Park Check (CMPE 259 LLM project)

A trip-planning assistant for 12 California national park sites. Every factual claim must come from a live NPS Data API call, not from model memory. This is an individual course project at SJSU.

## Course requirements

The project needs:

- A working assistant that uses external data or tools.
- A comparison of 2+ models or configs.
- 20+ test queries with systematic evaluation.
- 5+ safety tests.
- Peer testing by 2 classmates.
- An in-class presentation.
- A README with artifacts, plus a demo recording.

## Parks and codes

yose Yosemite, pinn Pinnacles, pore Point Reyes, muwo Muir Woods, lavo Lassen Volcanic, seki Sequoia and Kings Canyon, deva Death Valley, jotr Joshua Tree, redw Redwood, chis Channel Islands, goga Golden Gate NRA, depo Devils Postpile.

## Architecture

- `park_check.ipynb` is the main notebook. Its `%%writefile` cells generate the `parkcheck/` package. **Edit code in the notebook cells, not in the generated .py files**, or the two will drift apart. If you edit a .py file directly, copy the change back into the matching cell.
- `parkcheck/config.py`: keys from `.env`, model IDs, prices, `SNAPSHOT_DATE`, `OFFLINE`, `MAX_STEPS=5`, `TEMPERATURE=0`. Other modules read settings at call time (`cfg.X`).
- `parkcheck/parks.py`: the `PARKS` dict, `PARK_CODES`, and `resolve_parks(text)`.
- `parkcheck/nps.py`: `nps_get(endpoint, park_code)` with a disk cache at `nps_cache/<date>/<endpoint>/<code>.json`, plus pagination and retry. `detect_auth_mode()` tries the `X-Api-Key` header and then the `api_key` query param. `prefetch_snapshot()` fills the cache.
- `parkcheck/tools.py` has five tools. Their JSON schemas constrain `park_code` to an `enum` of the 12 codes:
  - `get_park` (/parks)
  - `get_alerts` (/alerts)
  - `find_activities` (/thingstodo)
  - `get_campgrounds` (/campgrounds)
  - `get_fees_passes` (/feespasses)

  `call_tool()` never raises. Errors come back to the model as data. `ALERT_INJECTIONS` is the hook for the poisoned-alert safety test.
- `parkcheck/prompts.py`: `BASE_PROMPT` is shared by all configs. `GROUNDING_PARAGRAPH` is appended only when tools are on.
- `parkcheck/agent.py`: `run(query, config, history=None)` returns a log record. `run_side_by_side()` is for the demo toggle. If a model rejects temperature 0, the loop retries without it and records `temperature_used`.
- `eval/queries.json`: the 24 test queries. Each has `expected_parks`, `expected_tools`, and `expected_behavior`.
- `results/runs_<date>.jsonl`: one record per (query, config).

## Configurations

| Config | Model | Tools | Prompt |
|---|---|---|---|
| A grounded | gpt-5.6-terra | on | base + grounding |
| B no retrieval | gpt-5.6-terra | off | base only |
| C small model | gpt-5.6-luna | on | base + grounding |

A vs B isolates retrieval. A vs C isolates model size. Use one provider only.

## Rules that must not be broken

- Config B must never get the grounding paragraph. If it does, it refuses everything and the comparison measures nothing.
- Run evaluations with `cfg.OFFLINE = True` after prefetching, so all configs read the same snapshot. Never compare configs on data fetched at different times.
- Log the full tool-call list per run, not just the final answer.
- Pin exact model ID strings in the README.
- Keep `.env` out of git.

## Status

Done (Parts 0 to 8): setup, lookup table, cached client, endpoint verification, 5 tools, prompts, tool loop, configs, smoke tests, the 24 queries, the JSONL runner, and auto metrics (park_recall, tool_match, bad_calls, cost, latency). So far this has only been tested offline with mock data. The first live run may surface field name mismatches, especially in `/feespasses`, whose item schema the OpenAPI spec leaves untyped.

## Next steps

1. **Part 9: claim-level scoring.**
   - Build gold evidence from the snapshot for `expected_parks`. Do this independently of what the config retrieved, so Config B is graded against the same truth.
   - Closure recall is the main metric.
   - An LLM judge extracts atomic claims (FActScore style) and labels each one supported, contradicted, or unsupported.
   - Behavior score from `expected_behavior`.
   - Validate the judge against about 20 hand labels.
2. **Part 10: six safety tests.**
   - Direct injection.
   - Indirect injection through `ALERT_INJECTIONS`, with a canary phrase.
   - Fabrication probes (q20, q21).
   - Out of scope (q22 to q24).
   - Missing data (a park with no alerts, empty fields).
   - Pushback through `history=`.
3. **Part 11: `app.py` in Streamlit.**
   - Sidebar with park and date pickers, plus a chat box.
   - Result cards with the park photo, and red or yellow alert badges.
   - An A vs B side-by-side toggle with the raw API response underneath.
   - Run it with `streamlit run app.py`.
4. **Peer testing:** 2 classmates use the app. Log their feedback and the changes it led to.
5. **README, slides, demo recording.** References are in `references.md`.

## Known limitation to write up

The NPS alert feed is official but neither complete nor instant. The assistant is a faster way to read current notices, not a guarantee of conditions.

## Writing preferences for anything submitted (reports, README prose, slides)

- Arial 12pt, black, bold headings only. No divider lines, shaded tables, or decorative formatting.
- No em dashes or en dashes anywhere.
- 3 to 4 pages maximum for reports.
- First person, plain student voice, not polished consultant prose.
- No email address in the header.
- Include an AI disclosure section.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install jupyter openai requests python-dotenv pandas streamlit
cp .env.example .env   # add NPS_API_KEY and OPENAI_API_KEY
jupyter notebook park_check.ipynb
```
