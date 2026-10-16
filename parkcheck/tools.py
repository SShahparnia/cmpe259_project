"""Model-facing tools. Each returns a JSON-serializable dict."""
import re
import html
import json

from . import config as cfg
from .nps import nps_get, NPSError
from .parks import PARK_CODES, park_name

_TAG = re.compile(r"<[^>]+>")
CATEGORY_ORDER = {"Park Closure": 0, "Danger": 1, "Caution": 2, "Information": 3}

# Safety test hook: {"yose": [{"title": ..., "category": ..., "description": ...}]}
ALERT_INJECTIONS: dict[str, list[dict]] = {}


def clean(s, limit=None):
    if s is None:
        return ""
    s = html.unescape(_TAG.sub(" ", str(s)))
    s = re.sub(r"\s+", " ", s).strip()
    if limit and len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0] + " ..."
    return s


def _source(endpoint, code):
    return {"endpoint": f"/{endpoint}", "park_code": code, "snapshot": cfg.SNAPSHOT_DATE}


def _check_code(code):
    if code not in PARK_CODES:
        raise ValueError(f"park_code '{code}' is not one of the 12 supported parks: {PARK_CODES}")


def _fees(lst, limit=300):
    return [{"title": clean(f.get("title")), "cost": f.get("cost"),
             "description": clean(f.get("description"), limit)} for f in (lst or [])]


# --------------------------------------------------------------------------- get_park
def get_park(park_code):
    _check_code(park_code)
    items = nps_get("parks", park_code)["data"]
    p = next((d for d in items if d.get("parkCode") == park_code), items[0] if items else None)
    if p is None:
        return {"park_code": park_code, "error": "No park record returned by /parks",
                "source": _source("parks", park_code)}

    hours = []
    for h in p.get("operatingHours", []) or []:
        hours.append({
            "name": clean(h.get("name")),
            "description": clean(h.get("description"), 400),
            "standard_hours": h.get("standardHours", {}),
            "exceptions": [{"name": clean(e.get("name")), "start": e.get("startDate"),
                            "end": e.get("endDate"), "hours": e.get("exceptionHours", {})}
                           for e in (h.get("exceptions") or [])[:6]],
        })
    img = (p.get("images") or [{}])[0]
    out = {
        "park_code": park_code,
        "name": clean(p.get("fullName")) or park_name(park_code),
        "url": p.get("url"),
        "description": clean(p.get("description"), 600),
        "weather_info": clean(p.get("weatherInfo"), 300),
        "entrance_fees": _fees(p.get("entranceFees")),
        "entrance_passes": _fees(p.get("entrancePasses")),
        "operating_hours": hours,
        "activities": [a.get("name") for a in (p.get("activities") or [])],
        "image": {"url": img.get("url"), "alt": clean(img.get("altText"))} if img else None,
        "source": _source("parks", park_code),
    }
    out["empty_fields"] = [k for k in ("entrance_fees", "entrance_passes", "operating_hours",
                                       "activities", "description") if not out[k]]
    return out


# --------------------------------------------------------------------------- get_alerts
def get_alerts(park_code, category=None):
    _check_code(park_code)
    raw = list(nps_get("alerts", park_code)["data"]) + list(ALERT_INJECTIONS.get(park_code, []))
    alerts = []
    for a in raw:
        if category and (a.get("category") or "").lower() != category.lower():
            continue
        alerts.append({
            "title": clean(a.get("title")),
            "category": a.get("category"),
            "description": clean(a.get("description"), 700),
            "url": a.get("url"),
            "last_indexed": a.get("lastIndexedDate"),
        })
    alerts.sort(key=lambda x: CATEGORY_ORDER.get(x["category"], 9))
    out = {"park_code": park_code, "park_name": park_name(park_code),
           "count": len(alerts), "alerts": alerts, "source": _source("alerts", park_code)}
    if not alerts:
        out["note"] = ("No active alerts are posted in the NPS feed for this park"
                       + (f" in category '{category}'" if category else "")
                       + ". This does not guarantee there are no closures.")
    return out


# --------------------------------------------------------------------------- find_activities
def _thing_text(t):
    parts = [t.get("title"), t.get("shortDescription"),
             " ".join(a.get("name", "") for a in t.get("activities") or []),
             " ".join(t.get("tags") or [])]
    return clean(" ".join(p for p in parts if p)).lower()


def find_activities(park_code, activity=None, max_results=10):
    _check_code(park_code)
    things = nps_get("thingstodo", park_code)["data"]
    if activity:
        words = [w for w in re.findall(r"[a-z]+", activity.lower()) if len(w) > 2]
        scored = []
        for t in things:
            txt = _thing_text(t)
            score = sum(txt.count(w) for w in words)
            if score:
                scored.append((score, t))
        scored.sort(key=lambda x: -x[0])
        matched = [t for _, t in scored]
    else:
        matched = things

    results = [{
        "title": clean(t.get("title")),
        "short_description": clean(t.get("shortDescription"), 300),
        "duration": clean(t.get("duration")),
        "season": t.get("season") or [],
        "activities": [a.get("name") for a in t.get("activities") or []],
        "reservation_required": t.get("isReservationRequired"),
        "fees_apply": t.get("doFeesApply"),
        "pets_permitted": t.get("arePetsPermitted"),
        "accessibility": clean(t.get("accessibilityInformation"), 200),
        "url": t.get("url"),
    } for t in matched[:max_results]]

    out = {"park_code": park_code, "park_name": park_name(park_code), "query": activity,
           "total_things_to_do": len(things), "matched": len(matched),
           "results": results, "source": _source("thingstodo", park_code)}
    if activity and not matched:
        names = sorted({a.get("name") for t in things for a in t.get("activities") or [] if a.get("name")})
        out["note"] = f"No things-to-do matched '{activity}'. Activity types listed for this park: {names[:40]}"
    return out


# --------------------------------------------------------------------------- get_campgrounds
def _as_int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def get_campgrounds(park_code, reservable_only=False):
    _check_code(park_code)
    cgs = nps_get("campgrounds", park_code)["data"]
    results = []
    for c in cgs:
        n_res = _as_int(c.get("numberOfSitesReservable"))
        if reservable_only and not (n_res or c.get("reservationUrl")):
            continue
        results.append({
            "name": clean(c.get("name")),
            "description": clean(c.get("description"), 250),
            "reservation_info": clean(c.get("reservationInfo"), 300),
            "reservation_url": c.get("reservationUrl"),
            "sites_reservable": n_res,
            "sites_first_come_first_serve": _as_int(c.get("numberOfSitesFirstComeFirstServe")),
            "fees": _fees(c.get("fees"), 200),
            "hours": [clean(h.get("description"), 200) for h in (c.get("operatingHours") or [])[:2]],
            "url": c.get("url"),
        })
    out = {"park_code": park_code, "park_name": park_name(park_code), "count": len(results),
           "campgrounds": results, "source": _source("campgrounds", park_code)}
    if not results:
        out["note"] = "No campgrounds" + (" with reservable sites" if reservable_only else "") + " in the NPS data for this park."
    return out


# --------------------------------------------------------------------------- get_fees_passes
_DROP_KEYS = {"images", "id", "latLong", "latitude", "longitude", "addresses", "contacts",
              "relatedParks", "multimedia", "geometryPoiId"}


def _shape_generic(obj, str_limit=400, list_limit=15):
    """/feespasses items are untyped in the spec, so keep every field but trim it."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in _DROP_KEYS:
                continue
            sv = _shape_generic(v, str_limit, list_limit)
            if sv in ("", [], {}, None):
                continue
            out[k] = sv
        return out
    if isinstance(obj, list):
        return [_shape_generic(x, str_limit, list_limit) for x in obj[:list_limit]]
    if isinstance(obj, str):
        return clean(obj, str_limit)
    return obj


def get_fees_passes(park_code):
    _check_code(park_code)
    items = nps_get("feespasses", park_code)["data"]
    items = [i for i in items if not i.get("parkCode") or i.get("parkCode") == park_code] or items
    out = {"park_code": park_code, "park_name": park_name(park_code), "count": len(items),
           "fees_passes": [_shape_generic(i) for i in items], "source": _source("feespasses", park_code)}
    if not items:
        out["note"] = "The /feespasses endpoint returned nothing for this park. Try get_park for entrance fees."
    return out


# --------------------------------------------------------------------------- schemas + dispatch
_CODE = {"type": "string", "enum": PARK_CODES,
         "description": "NPS park code. yose=Yosemite, pinn=Pinnacles, pore=Point Reyes, muwo=Muir Woods, "
                        "lavo=Lassen Volcanic, seki=Sequoia and Kings Canyon, deva=Death Valley, "
                        "jotr=Joshua Tree, redw=Redwood, chis=Channel Islands, goga=Golden Gate NRA, "
                        "depo=Devils Postpile."}


def _fn(name, description, props, required):
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": props, "required": required,
                       "additionalProperties": False}}}


TOOL_SCHEMAS = [
    _fn("get_park", "Park overview: description, operating hours (with seasonal exceptions), entrance fees, "
        "accepted entrance passes, and the activity list.", {"park_code": _CODE}, ["park_code"]),
    _fn("get_alerts", "Current NPS alerts for a park: closures (roads, trails, facilities), dangers, cautions, "
        "and information notices. Call this before saying anything is open or closed.",
        {"park_code": _CODE,
         "category": {"type": ["string", "null"], "enum": ["Park Closure", "Danger", "Caution", "Information", None],
                      "description": "Optional filter. Leave null to get every alert (recommended)."}},
        ["park_code", "category"]),
    _fn("find_activities", "Things to do at a park, optionally filtered by a keyword like 'hike', 'tidepool', "
        "'stargazing', 'wheelchair accessible', 'short walk'.",
        {"park_code": _CODE,
         "activity": {"type": ["string", "null"], "description": "Keyword filter, or null for everything."}},
        ["park_code", "activity"]),
    _fn("get_campgrounds", "Campgrounds at a park with fees, number of reservable versus first-come sites, "
        "and reservation instructions.",
        {"park_code": _CODE,
         "reservable_only": {"type": "boolean", "description": "Only campgrounds that take reservations."}},
        ["park_code", "reservable_only"]),
    _fn("get_fees_passes", "Detailed fee and pass information for a park, including timed entry, parking or "
        "vehicle reservations, and which passes are accepted.", {"park_code": _CODE}, ["park_code"]),
]

TOOL_FUNCS = {"get_park": get_park, "get_alerts": get_alerts, "find_activities": find_activities,
              "get_campgrounds": get_campgrounds, "get_fees_passes": get_fees_passes}


def call_tool(name, args):
    """Execute one tool call. Never raises; errors come back as data for the model."""
    fn = TOOL_FUNCS.get(name)
    if fn is None:
        return {"error": f"Unknown tool '{name}'"}, False
    try:
        return fn(**args), True
    except (ValueError, TypeError) as e:
        return {"error": str(e)}, False
    except NPSError as e:
        return {"error": f"NPS data unavailable: {e}"}, False


def to_tool_message(result):
    s = json.dumps(result, ensure_ascii=False)
    if len(s) > cfg.MAX_TOOL_CHARS:
        s = s[:cfg.MAX_TOOL_CHARS] + ' ... [TRUNCATED: result too long]'
    return s
