# Park Check (CMPE 259 LLM project)

A trip-planning assistant for 12 California national park sites. Every factual claim must come from a live NPS Data API call, not from model memory.

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
- `parkcheck/config.py`: keys from `.env`, model IDs, prices, `SNAPSHOT_DATE`, `OFFLINE`, `MAX_STEPS=5`, `TEMPERATURE=0`, `REASONING_EFFORT="none"`. Other modules read settings at call time (`cfg.X`).
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

## Progress (as of October 15, 2026)

### Before check-in 1 (Parts 0 to 8)

- Collected 34 sources on RAG, tool use, hallucination, evaluation and prompt injection in `references.md`.
- Built the `parkcheck` package from the notebook: the cached NPS client, the 12 park lookup table, the 5 tools, the shared prompts, the tool calling loop and the 3 configs.
- Wrote the 24 test queries in `eval/queries.json`, the JSONL runner and the automatic metrics (park_recall, tool_match, bad_calls, cost, latency).
- All of this was first tested offline with mock data.

### Check-in 1

- **First live run.** The NPS key works with both auth styles. I saved one snapshot of all 12 parks and 5 endpoints to `nps_cache/2026-10-15/` (60 responses, no errors). All 5 tools ran on all 12 parks without failing, and the untyped `/feespasses` schema is handled by the generic shaping in `get_fees_passes`.
- **Bug found and fixed.** The gpt-5.6 models reject function tools on `/v1/chat/completions` unless `reasoning_effort="none"`, so Configs A and C crashed on every query. I added `REASONING_EFFORT = "none"` to `config.py` and apply it to all 3 configs so the A vs B comparison stays fair. With this setting, temperature 0 is accepted too.
- **Evaluation.** I ran all 24 queries through all 3 configs offline on the saved snapshot (72 runs, 0 errors, $0.32 total). Raw logs are in `results/runs_2026-10-15_rerun.jsonl` and the metrics are in `results/auto_metrics_2026-10-15.csv`. An earlier run of the same evaluation is kept in `results/runs_2026-10-15.jsonl`.

| Config | Park recall | Tool match | Bad calls | Mean latency | Cost per query |
|---|---|---|---|---|---|
| A grounded (gpt-5.6-terra) | 0.93 | 0.89 | 0 | 2.47 s | $0.0097 |
| B no retrieval (gpt-5.6-terra) | n/a | n/a | 0 | 2.55 s | $0.0022 |
| C small model (gpt-5.6-luna) | 1.00 | 1.00 | 0 | 3.40 s | $0.0013 |

- **What the answers show.**
  - Config B answers from memory. For "Is Tioga Road open?" it said the road is "typically closed by mid-October", while A and C checked the alert feed and told the user to confirm with the park.
  - C mentioned the new $100 nonresident fee at Yosemite from the live data and A left it out, even though C costs about 7 times less.
  - A's misses were the vague short hike question (q13, no tool calls) and the Mist Trail safety question (q22, refused without checking alerts).
  - C scored 0.93 park recall in the earlier run and 1.00 in the rerun, so its tool use varies a little between runs even at temperature 0.
- **Data gaps found.** Yosemite has 0 alerts in this snapshot, Channel Islands and Devils Postpile have no things-to-do, and 5 parks have no entrance fees in `/parks`. These will be used in the missing data safety test.
- **Check-in 1 report** is in `docs/checkin1_report.docx`.

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
