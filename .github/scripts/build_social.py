#!/usr/bin/env python3
"""Generate the social link chips in assets/.

Same chip language as the tech marquee: ink pill, hairline border, brand dot,
mono label. Each chip is its own file so the README can wrap it in its own link.
"""

import os

FS, CW, LS, PADX, H = 13, 7.82, 0.6, 20, 34
LINKS = [
    ("x", "X", "#C6F432"),
    ("linkedin", "LINKEDIN", "#6D28D9"),
    ("medium", "MEDIUM", "#C6F432"),
    ("email", "EMAIL", "#6D28D9"),
]

os.makedirs("assets", exist_ok=True)
for slug, label, dot in LINKS:
    w = round(len(label) * (CW + LS) + PADX * 2 + 16, 1)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {H}" width="{w}" height="{H}" role="img" aria-label="{label}">
  <title>{label}</title>
  <rect x="0.75" y="0.75" width="{w - 1.5}" height="{H - 1.5}" rx="{(H - 1.5) / 2}" fill="#121214" stroke="#2A2A32" stroke-width="1.5"/>
  <circle cx="16" cy="{H / 2}" r="4" fill="{dot}"/>
  <text x="{PADX + 10}" y="{H / 2 + 4.5}" font-family="ui-monospace, &apos;SF Mono&apos;, &apos;JetBrains Mono&apos;, Menlo, Consolas, monospace" font-size="{FS}" letter-spacing="{LS}" fill="#B8B8C4">{label}</text>
</svg>
'''
    open(f"assets/social-{slug}.svg", "w").write(svg)
    print(f"assets/social-{slug}.svg  {w}x{H}")
