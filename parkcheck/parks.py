"""The twelve in-scope parks and a name -> park_code resolver."""
import re

PARKS = {
    "yose": {"name": "Yosemite National Park",
             "aliases": ["yosemite", "tioga", "half dome", "mist trail", "yosemite valley", "glacier point", "mariposa grove"]},
    "pinn": {"name": "Pinnacles National Park",
             "aliases": ["pinnacles"]},
    "pore": {"name": "Point Reyes National Seashore",
             "aliases": ["point reyes", "pt reyes"]},
    "muwo": {"name": "Muir Woods National Monument",
             "aliases": ["muir woods", "muir"]},
    "lavo": {"name": "Lassen Volcanic National Park",
             "aliases": ["lassen", "lassen volcanic"]},
    "seki": {"name": "Sequoia and Kings Canyon National Parks",
             "aliases": ["sequoia", "kings canyon", "big trees", "generals highway", "general sherman", "seki"]},
    "deva": {"name": "Death Valley National Park",
             "aliases": ["death valley", "badwater"]},
    "jotr": {"name": "Joshua Tree National Park",
             "aliases": ["joshua tree", "jtree", "j tree"]},
    "redw": {"name": "Redwood National and State Parks",
             "aliases": ["redwood national", "redwood national park", "redwood"]},
    "chis": {"name": "Channel Islands National Park",
             "aliases": ["channel islands", "santa cruz island", "anacapa"]},
    "goga": {"name": "Golden Gate National Recreation Area",
             "aliases": ["golden gate", "goga", "marin headlands", "alcatraz", "lands end", "crissy field"]},
    "depo": {"name": "Devils Postpile National Monument",
             "aliases": ["devils postpile", "devil's postpile", "rainbow falls"]},
}

PARK_CODES = list(PARKS.keys())


def park_name(code: str) -> str:
    return PARKS.get(code, {}).get("name", code)


def resolve_parks(text: str) -> list[str]:
    """Return every in-scope park code mentioned in free text, in order of appearance.
    Longest aliases are matched first so 'redwood national' wins over 'redwood'."""
    t = " " + re.sub(r"\s+", " ", re.sub(r"[^a-z0-9' ]", " ", text.lower())) + " "
    pairs = sorted(((a, c) for c, p in PARKS.items() for a in p["aliases"]), key=lambda x: -len(x[0]))
    found = {}
    for alias, code in pairs:
        m = re.search(r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])", t)
        if m:
            found.setdefault(code, m.start())
            t = t[:m.start()] + " " * len(alias) + t[m.end():]
    if "muwo" in found:          # 'redwoods' in a Muir Woods question is Muir Woods
        found.pop("redw", None)
    return sorted(found, key=found.get)
