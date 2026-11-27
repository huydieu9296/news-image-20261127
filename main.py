#!/usr/bin/env python3
"""The World in One Day -- Friday, 27 November 2026.

Draws a 1024x1024 newspaper front page summing up the day's world news
and writes it to /output/entry.png.

Reads nothing from disk except fonts, uses no network, no clock and no
randomness, so every run writes exactly the same bytes.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = "/output/entry.png"

PAPER = (247, 243, 234)   # warm newsprint
INK = (26, 26, 26)        # near-black ink
MUTED = (96, 89, 76)      # grey-brown for datelines and footers
RED = (185, 28, 28)       # masthead accent
NAVY = (30, 58, 95)       # deep blue for rules

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
BOLD = "DejaVuSans-Bold.ttf"
REG = "DejaVuSans.ttf"


def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(draw, text, fname, start, max_w, max_lines):
    """Largest font size (shrinking from start) whose wrap fits max_lines."""
    size = start
    while size > 12:
        fnt = font(fname, size)
        if len(wrap(draw, text, fnt, max_w)) <= max_lines:
            return fnt, wrap(draw, text, fnt, max_w)
        size -= 1
    fnt = font(fname, 12)
    return fnt, wrap(draw, text, fnt, max_w)


# ---------------------------------------------------------------- pictograms
# Small geometric marks drawn with plain shapes; they decorate the cards
# while the headlines and summaries carry the news.

def scale(d, x, y, s, color):
    """A balance scale: post, beam and two pans (tariffs / trade)."""
    cx = x + s // 2
    d.line([cx, y + s // 8, cx, y + 7 * s // 8], fill=color, width=6)
    d.line([x + s // 8, y + s // 4, x + 7 * s // 8, y + s // 4],
           fill=color, width=6)
    d.line([cx - s // 8, y + s // 8, cx + s // 8, y + s // 8],
           fill=color, width=6)
    for sx in (x + s // 8, x + 7 * s // 8):
        d.line([sx, y + s // 4, sx, y + s // 2], fill=color, width=4)
        d.polygon([(sx - s // 6, y + s // 2), (sx + s // 6, y + s // 2),
                   (sx, y + 5 * s // 8)], fill=color)
    d.line([cx - s // 6, y + 7 * s // 8, cx + s // 6, y + 7 * s // 8],
           fill=color, width=6)


def atom(d, x, y, s, color):
    """An atom: nucleus with three elliptical orbits (nuclear weapons)."""
    cx, cy = x + s // 2, y + s // 2
    d.ellipse([cx - s // 10, cy - s // 10, cx + s // 10, cy + s // 10],
              fill=color)
    d.ellipse([x + s // 12, y + s // 12, x + 11 * s // 12, y + 11 * s // 12],
              outline=color, width=4)
    d.ellipse([x + s // 6, y + s // 6, x + 5 * s // 6, y + 5 * s // 6],
              outline=color, width=4)
    d.ellipse([x + s // 3, y, x + 2 * s // 3, y + s],
              outline=color, width=4)
    d.ellipse([cx - s // 16, cy - s // 16, cx + s // 16, cy + s // 16],
              fill=(255, 255, 255))


def rocket(d, x, y, s, color):
    """A rocket lifting off: body, window, fins and flame."""
    cx = x + s // 2
    cy = y + s // 2
    d.polygon([(cx, y + 4), (cx + s // 6, y + s // 3),
               (cx + s // 6, y + 2 * s // 3), (cx - s // 6, y + 2 * s // 3),
               (cx - s // 6, y + s // 3)], fill=color)
    d.ellipse([cx - s // 14, cy - s // 6, cx + s // 14, cy - s // 24],
              fill=(255, 255, 255))
    d.polygon([(cx - s // 6, y + s // 2), (cx - s // 3, y + 5 * s // 6),
               (cx - s // 6, y + 5 * s // 6)], fill=color)
    d.polygon([(cx + s // 6, y + s // 2), (cx + s // 3, y + 5 * s // 6),
               (cx + s // 6, y + 5 * s // 6)], fill=color)
    d.polygon([(cx - s // 12, y + 2 * s // 3), (cx + s // 12, y + 2 * s // 3),
               (cx, y + s - 4)], fill=(230, 120, 30))


def flame(d, x, y, s, color):
    """A flame: round base, flickering tip, inner tongue (fires)."""
    cx = x + s // 2
    d.ellipse([x + s // 8, y + s // 3, x + 7 * s // 8, y + s - 2],
              fill=color)
    d.polygon([(cx - s // 6, y + s // 2), (cx + s // 8, y + 2),
               (cx + s // 4, y + s // 2)], fill=color)
    ix, iy, iw = cx, y + s // 2, s // 5
    d.polygon([(ix, iy), (ix + iw, iy + s // 4), (ix, iy + s // 3),
               (ix - iw, iy + s // 4)], fill=(255, 200, 60))


def refinery(d, x, y, s, color):
    """A refinery: two towers, a tank and a plume of smoke."""
    d.rectangle([x + s // 8, y + s // 3, x + s // 3, y + 5 * s // 6],
                fill=color)
    d.rectangle([x + s // 2, y + s // 6, x + 2 * s // 3, y + 5 * s // 6],
                fill=color)
    d.rectangle([x + 3 * s // 4, y + 3 * s // 5, x + s - 4, y + 5 * s // 6],
                fill=color)
    d.line([x + s // 8, y + 5 * s // 6, x + s - 4, y + 5 * s // 6],
           fill=color, width=5)
    d.ellipse([x + s // 2, y, x + 2 * s // 3 + 12, y + s // 6],
              fill=MUTED)
    d.ellipse([x + 5 * s // 8, y - 2, x + 3 * s // 4, y + s // 8],
              fill=MUTED)


def globe(d, x, y, s, color):
    """A globe: circle, meridians and parallels."""
    d.ellipse([x, y, x + s, y + s], outline=color, width=4)
    d.ellipse([x + s // 4, y, x + 3 * s // 4, y + s], outline=color, width=3)
    d.line([x, y + s // 2, x + s, y + s // 2], fill=color, width=3)
    d.arc([x, y + s // 6, x + s, y + 5 * s // 6], 0, 360, fill=color, width=3)


ICONS = {"scale": scale, "atom": atom, "rocket": rocket,
         "flame": flame, "refinery": refinery, "globe": globe}


# ------------------------------------------------------------------- stories
# Six stories from the Friday 27 November 2026 news cycle (Reuters,
# Associated Press via The Hindu / WHRO, USTR via Onmanorama / Shillong
# Times, Bangkok Post / AFP, Channel News Asia, Al Jazeera). Headlines are
# short on purpose so they survive wrapping.

STORIES = [
    {
        "kicker": "TRADE  •  UNITED STATES",
        "color": (124, 58, 237),
        "icon": "scale",
        "headline": "US proposes 25% tariffs on Indian goods",
        "summary": "The trade representative unveiled duties of up to 25% — "
                   "17% if Delhi signs a deal — after a probe of excess "
                   "capacity in 16 economies.",
    },
    {
        "kicker": "NUCLEAR  •  NORTH KOREA",
        "color": (185, 28, 28),
        "icon": "atom",
        "headline": "Kim vows to build more nuclear weapons",
        "summary": "Kim Jong Un toured nuclear plants and called the "
                   "arsenal irreversible, spurning Trump.",
    },
    {
        "kicker": "SPACE  •  UNITED STATES",
        "color": (30, 58, 95),
        "icon": "rocket",
        "headline": "Musk: two SpaceX shares for every US child",
        "summary": "One share from SpaceX, one from Musk himself — a "
                   "pledge worth about $18bn.",
    },
    {
        "kicker": "DISASTER  •  EGYPT",
        "color": (185, 28, 28),
        "icon": "flame",
        "headline": "Cairo tanker fire kills 31 on ring road",
        "summary": "A fuel tanker overturned on a packed highway and burst "
                   "into flames; 31 dead, 21 hurt.",
    },
    {
        "kicker": "DISASTER  •  THAILAND",
        "color": (15, 118, 110),
        "icon": "refinery",
        "headline": "Blast and fire shut Bangkok refinery",
        "summary": "Blast at Bangchak's Phra Khanong plant hurt seven, "
                   "four critically; all units halted.",
    },
    {
        "kicker": "EUROPE  •  UKRAINE",
        "color": (30, 58, 95),
        "icon": "globe",
        "headline": "EU leaders split over budget and $49bn Ukraine loan",
        "summary": "Brussels debated a near-€1.6tn budget and a $49bn loan "
                   "for Kyiv as Russian strikes killed five in Ukraine.",
    },
]


# -------------------------------------------------------------------- cards

def draw_card(d, box, story, lead=False, compact=False):
    """One news card: kicker, headline, summary, pictogram at right.

    The summary is fitted to the vertical space left in the card, so no
    line ever spills past the card's bottom edge. Compact cards are
    single-line strips with no pictogram.
    """
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=10, fill=(255, 255, 255),
                        outline=(210, 202, 184), width=2)
    pad = 16 if compact else 24
    if compact:
        text_w = (x1 - x0) - 2 * pad
    else:
        icon_s = 150 if lead else 104
        ix = x1 - pad - icon_s
        iy = y0 + (y1 - y0 - icon_s) // 2
        text_w = ix - 14 - (x0 + pad)

    ky = y0 + pad
    kf = font(BOLD, 17 if compact else (20 if lead else 18))
    d.text((x0 + pad, ky), story["kicker"], font=kf, fill=story["color"])
    ky += 26 if compact else (30 if lead else 28)

    hf, hlines = fit(d, story["headline"], BOLD,
                     26 if compact else (40 if lead else 30),
                     text_w, 2)
    for line in hlines:
        d.text((x0 + pad, ky), line, font=hf, fill=INK)
        ky += int(hf.size * 1.18)

    ky += 6
    avail = (y1 - 8) - ky
    max_lines = 1 if compact else 2
    size = 19 if compact else 21
    while size > 12:
        sf = font(REG, size)
        slines = wrap(d, story["summary"], sf, text_w)
        if len(slines) <= max_lines and \
                len(slines) * int(size * 1.28) <= avail:
            break
        size -= 1
    sf = font(REG, size)
    slines = wrap(d, story["summary"], sf, text_w)[:max_lines]
    for line in slines:
        d.text((x0 + pad, ky), line, font=sf, fill=MUTED)
        ky += int(sf.size * 1.28)

    if not compact:
        ICONS[story["icon"]](d, ix, iy, icon_s, story["color"])


def draw_masthead(d):
    """Title, rules and dateline across the top of the page."""
    d.line([40, 30, W - 40, 30], fill=INK, width=4)
    title = "THE WORLD IN ONE DAY"
    tf = font(BOLD, 62)
    tw = d.textlength(title, font=tf)
    d.text(((W - tw) / 2, 44), title, font=tf, fill=INK)
    d.line([40, 128, W - 40, 128], fill=RED, width=3)
    date = "FRIDAY, 27 NOVEMBER 2026  •  SIX STORIES THAT DEFINED THE DAY"
    dsize = 23
    while dsize > 12:
        df = font(BOLD, dsize)
        if d.textlength(date, font=df) <= W - 80:
            break
        dsize -= 1
    df = font(BOLD, dsize)
    dw = d.textlength(date, font=df)
    d.text(((W - dw) / 2, 140), date, font=df, fill=MUTED)
    d.line([40, 176, W - 40, 176], fill=INK, width=4)


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    draw_masthead(d)

    mx = 40
    cw = W - 2 * mx
    # Lead story, full width.
    draw_card(d, (mx, 192, W - mx, 424), STORIES[0], lead=True)
    # Four stories in a 2x2 grid.
    gy0, gh, gap = 440, 192, 16
    gw = (cw - gap) // 2
    for i, story in enumerate(STORIES[1:5]):
        col, row = i % 2, i // 2
        x0 = mx + col * (gw + gap)
        y0 = gy0 + row * (gh + gap)
        draw_card(d, (x0, y0, x0 + gw, y0 + gh), story)
    # Last story, full width, compact single-line strip.
    draw_card(d, (mx, 848, W - mx, 960), STORIES[5], compact=True)
    # Footer.
    foot = "Sources: Reuters  •  Associated Press  •  USTR  •  " \
           "Bangkok Post / AFP  •  Channel News Asia  •  Al Jazeera — 27 November 2026"
    fsize = 17
    while fsize > 12:
        ff = font(REG, fsize)
        if d.textlength(foot, font=ff) <= W - 80:
            break
        fsize -= 1
    ff = font(REG, fsize)
    fw = d.textlength(foot, font=ff)
    d.text(((W - fw) / 2, 972), foot, font=ff, fill=MUTED)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, format="PNG")


if __name__ == "__main__":
    main()
