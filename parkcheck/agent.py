"""Tool-calling loop and run(query, config)."""
import json
import time
import uuid
import datetime as dt
from dataclasses import dataclass

from . import config as cfg
from .prompts import build_system_prompt
from .tools import TOOL_SCHEMAS, call_tool, to_tool_message


@dataclass(frozen=True)
class Config:
    name: str
    label: str
    model: str
    use_tools: bool


def get_configs():
    return {
        "A": Config("A", "grounded", cfg.MODEL_MID, True),
        "B": Config("B", "no retrieval", cfg.MODEL_MID, False),
        "C": Config("C", "small model", cfg.MODEL_SMALL, True),
    }


_client = None
_NO_TEMPERATURE = set()   # models that rejected a custom temperature


def client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=cfg.OPENAI_API_KEY or None)
    return _client


def _chat(model, messages, tools=None, tool_choice=None):
    kwargs = {"model": model, "messages": messages}
    if cfg.REASONING_EFFORT:
        kwargs["reasoning_effort"] = cfg.REASONING_EFFORT
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice or "auto"
    if model not in _NO_TEMPERATURE:
        kwargs["temperature"] = cfg.TEMPERATURE
    try:
        return client().chat.completions.create(**kwargs)
    except Exception as e:  # openai.BadRequestError, kept generic so tests can mock it
        if "temperature" in str(e).lower() and "temperature" in kwargs:
            _NO_TEMPERATURE.add(model)
            kwargs.pop("temperature")
            return client().chat.completions.create(**kwargs)
        raise


def _usage(resp):
    u = getattr(resp, "usage", None)
    if not u:
        return 0, 0
    return getattr(u, "prompt_tokens", 0) or 0, getattr(u, "completion_tokens", 0) or 0


def cost_usd(model, prompt_tokens, completion_tokens):
    pin, pout = cfg.PRICES_PER_1M.get(model, (0.0, 0.0))
    return round(prompt_tokens / 1e6 * pin + completion_tokens / 1e6 * pout, 6)


def run(query, config="A", history=None, today=None, keep_tool_results=True):
    """Run one user turn through a config. `history` is a list of prior
    {"role": "user"|"assistant", "content": str} turns (for pushback tests)."""
    conf = get_configs()[config] if isinstance(config, str) else config
    today = today or cfg.SNAPSHOT_DATE
    messages = [{"role": "system", "content": build_system_prompt(conf.use_tools, today)}]
    messages += list(history or [])
    messages.append({"role": "user", "content": query})
    tools = TOOL_SCHEMAS if conf.use_tools else None

    rec = {
        "run_id": uuid.uuid4().hex[:12],
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "snapshot": cfg.SNAPSHOT_DATE, "config": conf.name, "config_label": conf.label,
        "model": conf.model, "use_tools": conf.use_tools, "query": query,
        "history_turns": len(history or []), "reasoning_effort": cfg.REASONING_EFFORT,
        "answer": None, "tool_calls": [], "tool_results": [], "steps": 0,
        "prompt_tokens": 0, "completion_tokens": 0, "error": None,
    }
    t0 = time.perf_counter()
    try:
        for step in range(cfg.MAX_STEPS):
            last_step = step == cfg.MAX_STEPS - 1
            resp = _chat(conf.model, messages, tools, "none" if (tools and last_step) else None)
            rec["steps"] += 1
            pt, ct = _usage(resp)
            rec["prompt_tokens"] += pt
            rec["completion_tokens"] += ct
            msg = resp.choices[0].message
            rec["finish_reason"] = resp.choices[0].finish_reason

            if not getattr(msg, "tool_calls", None):
                rec["answer"] = msg.content or ""
                break

            messages.append({
                "role": "assistant", "content": msg.content,
                "tool_calls": [{"id": tc.id, "type": "function",
                                "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                               for tc in msg.tool_calls],
            })
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                t1 = time.perf_counter()
                result, ok = call_tool(tc.function.name, args)
                rec["tool_calls"].append({
                    "step": step, "name": tc.function.name, "args": args, "ok": ok,
                    "latency_s": round(time.perf_counter() - t1, 3),
                })
                if keep_tool_results:
                    rec["tool_results"].append({"name": tc.function.name, "args": args, "result": result})
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": to_tool_message(result)})
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"

    rec["latency_s"] = round(time.perf_counter() - t0, 3)
    rec["cost_usd"] = cost_usd(conf.model, rec["prompt_tokens"], rec["completion_tokens"])
    rec["temperature_used"] = None if conf.model in _NO_TEMPERATURE else cfg.TEMPERATURE
    return rec


def run_side_by_side(query, configs=("A", "B"), **kw):
    """For the demo toggle: same question through several configs."""
    return {c: run(query, c, **kw) for c in configs}
