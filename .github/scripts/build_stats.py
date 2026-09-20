#!/usr/bin/env python3
"""Build assets/stats.svg from the GitHub API.

Runs in Actions with the built-in GITHUB_TOKEN, so it needs no personal token.
Every figure comes from a public REST endpoint; nothing is estimated.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

USER = os.environ.get("STATS_USER", "Zeegaths")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.environ.get("STATS_OUT", "assets/stats.svg")

RAMP = ["#6D28D9", "#7C3AED", "#8B5CF6", "#A78BFA", "#93B80C", "#C6F432"]
OTHER = "#3A3A46"


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USER}-profile-stats",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect():
    user = api(f"/users/{USER}")

    repos, page = [], 1
    while page <= 5:
        batch = api(f"/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    owned = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in owned)

    # Bytes per language, over the 60 largest owned repos.
    by_size = sorted(owned, key=lambda r: r.get("size", 0), reverse=True)[:60]
    langs = {}
    for r in by_size:
        try:
            for name, count in api(f"/repos/{USER}/{r['name']}/languages").items():
                langs[name] = langs.get(name, 0) + count
        except urllib.error.HTTPError:
            continue

    return {
        "repos": user.get("public_repos", len(owned)),
        "stars": stars,
        "followers": user.get("followers", 0),
        "langs": sorted(langs.items(), key=lambda kv: kv[1], reverse=True),
    }


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(d):
    total = sum(c for _, c in d["langs"]) or 1
    top = d["langs"][:6]
    shown = sum(c for _, c in top)
    segments = [(n, c / total, RAMP[i]) for i, (n, c) in enumerate(top)]
    if total - shown > 0:
        segments.append(("Other", (total - shown) / total, OTHER))

    stamp = datetime.now(timezone.utc).strftime("%b %Y").upper()
    tiles = [
        (d["repos"], "PUBLIC REPOS"),
        (d["stars"], "STARS EARNED"),
        (d["followers"], "FOLLOWERS"),
        (len(d["langs"]), "LANGUAGES USED"),
    ]

    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 230" width="1000" height="230" '
        f'role="img" aria-label="GitHub statistics for {esc(USER)}">',
        f"  <title>{esc(USER)} on GitHub</title>",
        "  <defs>",
        '    <clipPath id="p"><rect width="1000" height="230" rx="18"/></clipPath>',
        '    <clipPath id="bar"><rect x="48" y="150" width="904" height="14" rx="7"/></clipPath>',
        "    <style>",
        '      .mono { font-family: ui-monospace, "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace; }',
        "      .num { font-size: 40px; font-weight: 700; fill: #FAFAFA; }",
        "      .lbl { font-size: 11px; letter-spacing: 2px; fill: #8A8A96; }",
        "      .leg { font-size: 12px; fill: #B8B8C4; }",
        "      .eyebrow { font-size: 11px; letter-spacing: 4px; fill: #5A5A66; }",
        "    </style>",
        "  </defs>",
        '  <g clip-path="url(#p)">',
        '    <rect width="1000" height="230" fill="#0A0A0B"/>',
        '    <rect width="1000" height="230" rx="18" fill="none" stroke="#26262E" stroke-width="1.5"/>',
        f'    <text class="mono eyebrow" x="48" y="42">GITHUB <tspan fill="#6D28D9">·</tspan> UPDATED {stamp}</text>',
    ]

    for i, (value, label) in enumerate(tiles):
        x = 48 + i * 232
        out.append(f'    <text class="mono num" x="{x}" y="98">{value}</text>')
        out.append(f'    <text class="mono lbl" x="{x}" y="120">{label}</text>')

    out.append('    <g clip-path="url(#bar)">')
    out.append('      <rect x="48" y="150" width="904" height="14" fill="#15151B"/>')
    cursor = 48.0
    for name, share, color in segments:
        w = round(904 * share, 1)
        out.append(
            f'      <rect x="{round(cursor, 1)}" y="150" width="{w}" height="14" fill="{color}">'
            f'<animate attributeName="height" values="0;14" dur="0.5s" begin="{round((cursor - 48) / 904 * 0.6, 2)}s" fill="freeze"/>'
            f"</rect>"
        )
        cursor += w
    out.append("    </g>")

    lx = 48
    for name, share, color in segments:
        pct = f"{share * 100:.1f}%"
        out.append(f'    <circle cx="{lx + 5}" cy="194" r="5" fill="{color}"/>')
        out.append(f'    <text class="mono leg" x="{lx + 18}" y="198">{esc(name)} <tspan fill="#5A5A66">{pct}</tspan></text>')
        lx += 22 + int((len(name) + len(pct) + 1) * 7.3)

    out.append("  </g>")
    out.append("</svg>")
    return "\n".join(out) + "\n"


PLACEHOLDER = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 230" width="1000" height="230" role="img" aria-label="GitHub statistics are being generated">
  <title>Stats pending</title>
  <rect width="1000" height="230" rx="18" fill="#0A0A0B"/>
  <rect width="1000" height="230" rx="18" fill="none" stroke="#26262E" stroke-width="1.5"/>
  <text x="48" y="112" font-family="ui-monospace, Menlo, monospace" font-size="15" fill="#8A8A96">
    Stats are generated by GitHub Actions. First run pending.
    <animate attributeName="opacity" values="1;0.45;1" dur="2.4s" repeatCount="indefinite"/>
  </text>
</svg>
"""


if __name__ == "__main__":
    if "--placeholder" in sys.argv:
        os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
        with open(OUT, "w") as fh:
            fh.write(PLACEHOLDER)
        print(f"wrote placeholder {OUT}")
        sys.exit(0)

    if "--demo" in sys.argv:
        data = {
            "repos": 64,
            "stars": 37,
            "followers": 58,
            "langs": [
                ("TypeScript", 820000), ("Solidity", 410000), ("Rust", 305000),
                ("JavaScript", 240000), ("Motoko", 96000), ("Cairo", 41000),
                ("Svelte", 22000), ("C++", 14000),
            ],
        }
    else:
        try:
            data = collect()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"GitHub API unavailable ({e}); keeping the existing stats.svg", file=sys.stderr)
            sys.exit(0)

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w") as fh:
        fh.write(render(data))
    print(f"wrote {OUT}: {data['repos']} repos, {data['stars']} stars, {len(data['langs'])} languages")
