"""Thin NPS Data API client with a disk snapshot cache."""
import json
import time
import hashlib
import datetime as dt

import requests

from . import config as cfg


class NPSError(Exception):
    pass


_AUTH_MODE = None   # "header" or "query", set by detect_auth_mode()


def _auth(mode):
    if mode == "header":
        return {"X-Api-Key": cfg.NPS_API_KEY}, {}
    return {}, {"api_key": cfg.NPS_API_KEY}


def detect_auth_mode(verbose=True):
    """Try the header and the query parameter; keep the first that returns 200."""
    global _AUTH_MODE
    if not cfg.NPS_API_KEY:
        raise NPSError("NPS_API_KEY is not set (put it in .env)")
    status = {}
    for mode in ("header", "query"):
        h, p = _auth(mode)
        try:
            r = requests.get(f"{cfg.NPS_BASE}/parks", headers=h,
                             params={"parkCode": "yose", "limit": 1, **p}, timeout=20)
            status[mode] = r.status_code
        except requests.RequestException as e:
            status[mode] = f"error: {e}"
    if verbose:
        print("auth check:", status)
    for mode in ("header", "query"):
        if status[mode] == 200:
            _AUTH_MODE = mode
            return mode, status
    raise NPSError(f"Neither auth mode worked: {status}")


def cache_path(endpoint, park_code, params=None, snapshot=None):
    snapshot = snapshot or cfg.SNAPSHOT_DATE
    extra = ""
    if params:
        extra = "__" + hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:8]
    ep = endpoint.strip("/").replace("/", "_")
    return cfg.CACHE_DIR / snapshot / ep / f"{park_code}{extra}.json"


def _get_with_retry(url, headers, params, tries=4):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                last = f"HTTP {r.status_code}"
                time.sleep(2 ** i)
                continue
            raise NPSError(f"HTTP {r.status_code} for {url}: {r.text[:200]}")
        except requests.RequestException as e:
            last = str(e)
            time.sleep(2 ** i)
    raise NPSError(f"Failed after {tries} tries: {last}")


def nps_get(endpoint, park_code, params=None, snapshot=None, refresh=False):
    """Return {"_meta": {...}, "data": [...]} for one endpoint and park.
    Reads the snapshot cache first; fetches (with pagination) only if missing."""
    snapshot = snapshot or cfg.SNAPSHOT_DATE
    path = cache_path(endpoint, park_code, params, snapshot)
    if path.exists() and not refresh:
        return json.loads(path.read_text())
    if cfg.OFFLINE:
        raise NPSError(f"OFFLINE mode and no cached snapshot for /{endpoint} {park_code} on {snapshot}")

    mode = _AUTH_MODE or detect_auth_mode(verbose=False)[0]
    headers, auth_params = _auth(mode)
    url = f"{cfg.NPS_BASE}/{endpoint.strip('/')}"
    data, start, total, page = [], 0, 0, 50
    while True:
        q = {"parkCode": park_code, "limit": page, "start": start, **(params or {}), **auth_params}
        body = _get_with_retry(url, headers, q).json()
        batch = body.get("data", []) or []
        data.extend(batch)
        try:
            total = int(body.get("total") or len(data))
        except (TypeError, ValueError):
            total = len(data)
        start += len(batch)
        if not batch or start >= total or start >= 1000:
            break

    payload = {
        "_meta": {
            "endpoint": endpoint, "park_code": park_code, "params": params or {},
            "snapshot": snapshot, "total": total,
            "fetched_at": dt.datetime.now().isoformat(timespec="seconds"),
        },
        "data": data,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1))
    return payload


ENDPOINTS = ["parks", "alerts", "thingstodo", "campgrounds", "feespasses"]


def prefetch_snapshot(park_codes, endpoints=ENDPOINTS, refresh=False, verbose=True):
    """Fetch every endpoint for every park into today's snapshot. Returns rows of counts."""
    rows = []
    for code in park_codes:
        row = {"park": code}
        for ep in endpoints:
            try:
                row[ep] = len(nps_get(ep, code, refresh=refresh)["data"])
            except NPSError as e:
                row[ep] = f"ERR {str(e)[:60]}"
        rows.append(row)
        if verbose:
            print(row)
    return rows
