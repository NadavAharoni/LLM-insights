#!/usr/bin/env python3
"""
Generates an SVG diagram: a sequence of token-vectors ("rods") flows in from
the left, through an LLM "machine", and tokens are emitted one-by-one on the right.

Everything is parametric. The knobs you are most likely to turn live in CONFIG
and PALETTE below. Change a value, re-run, re-render.
"""

import random

# ---------------------------------------------------------------------------
# KNOBS
# ---------------------------------------------------------------------------
CONFIG = dict(
    W=1240, H=600,
    cy=250,                 # vertical centre of the main flow band
    n_cells=5,              # vector components per token (cells per rod)
    rod_w=26, rod_h=120,    # token rod size
    n_input=6,
    input_x0=170,
    input_gap=58,
    machine_x=560, machine_w=250, machine_h=210,
    n_output=4,
    output_gap=60,
    show_feedback=True,
    show_callout=True,
    show_title=True,
    title="A language model reads a sequence of token-vectors and emits the next token",
)

PALETTE = dict(
    bg="#FBFAF8",
    ink="#222A33",
    muted="#8B919A",
    machine_fill="#EDF1F5",
    machine_stroke="#2B3340",
    layer_line="#C9D2DC",
    accent="#C98A2C",
    neg="#3E6FA8", mid="#EEE8DE", pos="#B8472F",
    rod_edge="#3A434D",
)

FONT = "Inter, 'Segoe UI', system-ui, sans-serif"
MONO = "'SF Mono', 'Consolas', 'Roboto Mono', monospace"


# ---------------------------------------------------------------------------
# colour helpers
# ---------------------------------------------------------------------------
def _h2r(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def _r2h(r):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in r)

def _lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

def heat(v):
    """v in [-1,1] -> diverging colour."""
    v = max(-1.0, min(1.0, v))
    mid = _h2r(PALETTE["mid"])
    if v < 0:
        return _r2h(_lerp(mid, _h2r(PALETTE["neg"]), -v))
    return _r2h(_lerp(mid, _h2r(PALETTE["pos"]), v))


# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------
def rod(x, y, w, h, values, highlight=False, faded=False, numbers=False):
    """A token rendered as a vertical 'rod' whose cells are a vector."""
    n = len(values)
    ch = h / n
    edge = PALETTE["accent"] if highlight else PALETTE["rod_edge"]
    ew = 3.0 if highlight else 1.4
    op = 0.45 if faded else 1.0
    out = [f'<g opacity="{op}">']
    for i, v in enumerate(values):
        cy = y + i * ch
        out.append(
            f'<rect x="{x:.1f}" y="{cy:.1f}" width="{w:.1f}" height="{ch:.1f}" '
            f'fill="{heat(v)}"/>'
        )
        if numbers:
            out.append(
                f'<text x="{x + w/2:.1f}" y="{cy + ch/2 + 3:.1f}" font-family="{MONO}" '
                f'font-size="10" fill="{PALETTE["ink"]}" text-anchor="middle">{v:+.1f}</text>'
            )
    out.append(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="5" '
        f'fill="none" stroke="{edge}" stroke-width="{ew}"/>'
    )
    out.append("</g>")
    return "".join(out)


def arrow(x1, y1, x2, y2, color=None, width=7, head=16, dashed=False):
    color = color or PALETTE["ink"]
    dash = ' stroke-dasharray="9 7"' if dashed else ""
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    perp = ang + math.pi / 2
    hw = head * 0.62
    p1 = (bx + hw * math.cos(perp), by + hw * math.sin(perp))
    p2 = (bx - hw * math.cos(perp), by - hw * math.sin(perp))
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
        f'stroke="{color}" stroke-width="{width}" stroke-linecap="round"{dash}/>'
        f'<path d="M{x2:.1f},{y2:.1f} L{p1[0]:.1f},{p1[1]:.1f} L{p2[0]:.1f},{p2[1]:.1f} Z" '
        f'fill="{color}"/>'
    )


def text(x, y, s, size=15, color=None, anchor="middle", family=None, weight="400", italic=False):
    color = color or PALETTE["ink"]
    family = family or FONT
    style = ' font-style="italic"' if italic else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
        f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{style}>{s}</text>'
    )


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
def build():
    C, P = CONFIG, PALETTE
    rng = random.Random(7)
    svg = [
        f'<svg viewBox="0 0 {C["W"]} {C["H"]}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="{FONT}">',
        f'<rect x="0" y="0" width="{C["W"]}" height="{C["H"]}" fill="{P["bg"]}"/>',
    ]

    def vec():
        return [round(rng.uniform(-1, 1), 1) for _ in range(C["n_cells"])]

    cy = C["cy"]
    rh, rw = C["rod_h"], C["rod_w"]
    rod_top = cy - rh / 2

    if C["show_title"]:
        svg.append(text(C["W"] / 2, 46, C["title"], size=20, weight="600"))

    # input queue
    input_xs = [C["input_x0"] + i * C["input_gap"] for i in range(C["n_input"])]
    for dx in (-34, -24, -14):
        svg.append(f'<circle cx="{C["input_x0"] + dx:.1f}" cy="{cy}" r="2.3" fill="{P["muted"]}"/>')
    for x in input_xs:
        svg.append(rod(x, rod_top, rw, rh, vec()))
    svg.append(text((input_xs[0] + input_xs[-1]) / 2 + rw / 2, cy + rh / 2 + 34,
                    "input sequence  (the context so far)", size=14, color=P["muted"]))

    # arrow into machine
    feed_start = input_xs[-1] + rw + 12
    feed_end = C["machine_x"] - 12
    feed_mid = (feed_start + feed_end) / 2
    svg.append(arrow(feed_start, cy, feed_end, cy))

    # machine
    mx, mw, mh = C["machine_x"], C["machine_w"], C["machine_h"]
    my = cy - mh / 2
    svg.append(
        f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="16" '
        f'fill="{P["machine_fill"]}" stroke="{P["machine_stroke"]}" stroke-width="2.4"/>'
    )
    for i in range(1, 6):
        ly = my + mh * i / 6
        svg.append(
            f'<line x1="{mx + 16}" y1="{ly:.1f}" x2="{mx + mw - 16}" y2="{ly:.1f}" '
            f'stroke="{P["layer_line"]}" stroke-width="1.4"/>'
        )
    svg.append(text(mx + mw / 2, cy - 6, "LLM", size=34, weight="700", color=P["machine_stroke"]))
    svg.append(text(mx + mw / 2, cy + 20, "stacked transformer layers", size=12.5, color=P["muted"]))
    svg.append(text(mx + mw / 2, cy + 38, "next-token model", size=12.5, color=P["muted"]))

    # arrow out of machine
    out_x0 = mx + mw + 28
    svg.append(arrow(mx + mw + 12, cy, out_x0 - 2, cy, color=P["accent"]))

    # output stream (emitted one by one)
    out_xs = [out_x0 + i * C["output_gap"] for i in range(C["n_output"])]
    for i, x in enumerate(out_xs):
        svg.append(rod(x, rod_top, rw, rh, vec(), highlight=(i == 0), faded=(i > 0)))
    hx = out_xs[0] + rw / 2
    svg.append(text(hx, rod_top - 16, "emitted now", size=13, weight="600", color=P["accent"]))
    svg.append(arrow(hx, rod_top - 10, hx, rod_top - 1, color=P["accent"], width=3, head=8))
    svg.append(text((out_xs[0] + out_xs[-1]) / 2 + rw / 2, cy + rh / 2 + 34,
                    "output tokens  (one at a time)", size=14, color=P["muted"]))

    # feedback loop
    if C["show_feedback"]:
        sx = out_xs[0] + rw / 2
        sy = rod_top - 28
        ex = feed_mid
        ey = rod_top - 6
        top = my - 24
        r = 12
        svg.append(
            f'<path d="M{sx:.1f},{sy:.1f} L{sx:.1f},{top + r:.1f} '
            f'Q{sx:.1f},{top:.1f} {sx - r:.1f},{top:.1f} '
            f'L{ex + r:.1f},{top:.1f} '
            f'Q{ex:.1f},{top:.1f} {ex:.1f},{top + r:.1f} '
            f'L{ex:.1f},{ey:.1f}" '
            f'fill="none" stroke="{P["muted"]}" stroke-width="2" stroke-dasharray="8 7"/>'
        )
        svg.append(arrow(ex, top + r + 6, ex, ey, color=P["muted"], width=2, head=10))
        svg.append(text((sx + ex) / 2, top - 8,
                        "each emitted token is appended, then the whole sequence is read again",
                        size=12.5, color=P["muted"], italic=True))

    # callout: one token = one vector
    if C["show_callout"]:
        gy = 470
        zx, zy = 150, gy - 60
        zw, zh = 46, 150
        svg.append(rod(zx, zy, zw, zh, vec(), numbers=True))
        bx = zx + zw + 14
        svg.append(
            f'<path d="M{bx},{zy} q8,0 8,8 l0,{zh/2 - 14:.0f} q0,8 8,8 q-8,0 -8,8 '
            f'l0,{zh/2 - 14:.0f} q0,8 -8,8" fill="none" stroke="{P["ink"]}" stroke-width="1.6"/>'
        )
        svg.append(text(bx + 26, zy + zh / 2 - 8, "one token", size=15, weight="600", anchor="start"))
        svg.append(text(bx + 26, zy + zh / 2 + 13, "= a vector of numbers", size=15, anchor="start"))
        svg.append(text(bx + 26, zy + zh / 2 + 33, "(its embedding)", size=13, anchor="start", color=P["muted"]))
        lrx = input_xs[0] + rw / 2
        svg.append(
            f'<path d="M{lrx:.1f},{cy + rh/2 + 6:.1f} C{lrx:.1f},{gy - 120:.1f} '
            f'{zx + zw/2:.1f},{gy - 150:.1f} {zx + zw/2:.1f},{zy - 6:.1f}" '
            f'fill="none" stroke="{P["muted"]}" stroke-width="1.3" stroke-dasharray="3 4"/>'
        )

    svg.append("</svg>")
    return "\n".join(svg)


if __name__ == "__main__":
    out = build()
    with open("llm_token_diagram.svg", "w") as f:
        f.write(out)
    print("wrote llm_token_diagram.svg  (%d bytes)" % len(out))
