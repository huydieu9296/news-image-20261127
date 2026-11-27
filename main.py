"""News image: world news of Friday, 27 November 2026.

Draws a one-page newspaper front page using only the Python standard
library: a hand-made 5x7 bitmap font, rectangle / circle / triangle
primitives, and a small PNG writer built on zlib and struct. There is
no network access, no clock, and no randomness anywhere, so running
the program twice writes byte-identical files.

Layout, top to bottom: a masthead with the date, a lead story on the
proposed US tariffs on Indian goods with a bar pictogram, two stories
(Kim's nuclear vow; Musk's SpaceX shares for US children), then three
stories (Cairo tanker fire, Bangkok refinery blast, the EU budget and
Ukraine loan split), and a sources footer.
"""

import os
import struct
import zlib
from binascii import crc32

WIDTH = 1024
HEIGHT = 1024

PAPER = (247, 243, 232)
INK = (20, 20, 20)
RED = (176, 42, 30)
BLUE = (29, 78, 137)
GOLD = (192, 138, 26)
GREY = (110, 108, 100)
LIGHT = (232, 226, 210)

# ---------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is 7 rows of 5 bits, "1" = ink. Only the
# characters the page needs are defined; anything else renders blank.
# ---------------------------------------------------------------------------
GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "00000", "00000", "00000", "01100", "00000"),
    ";": ("00000", "01100", "00000", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
}

BLANK = ("00000", "00000", "00000", "00000", "00000", "00000", "00000")


def normalise(text):
    """Fold the page's text into what the bitmap font can draw."""
    return (
        text.upper()
        .replace("\u2019", "'")
        .replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2022", "-")
    )


# ---------------------------------------------------------------------------
# Canvas: a plain RGB framebuffer with small drawing primitives.
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, width, height, background):
        self.width = width
        self.height = height
        self.pixels = bytearray(bytes(background) * (width * height))

    def set_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i] = color[0]
            self.pixels[i + 1] = color[1]
            self.pixels[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(x, 0)
        y0 = max(y, 0)
        x1 = min(x + w, self.width)
        y1 = min(y + h, self.height)
        for yy in range(y0, y1):
            i = (yy * self.width + x0) * 3
            row = bytes(color) * (x1 - x0)
            self.pixels[i:i + len(row)] = row

    def outline_rect(self, x, y, w, h, color, thickness=2):
        self.fill_rect(x, y, w, thickness, color)
        self.fill_rect(x, y + h - thickness, w, thickness, color)
        self.fill_rect(x, y, thickness, h, color)
        self.fill_rect(x + w - thickness, y, thickness, h, color)

    def hline(self, x, y, w, color, thickness=1):
        self.fill_rect(x, y, w, thickness, color)

    def vline(self, x, y, h, color, thickness=1):
        self.fill_rect(x, y, thickness, h, color)

    def line(self, x0, y0, x1, y1, color):
        """Bresenham line between two points."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.set_pixel(x, y, color)
            if x == x1 and y == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, color):
        """Filled circle centred on (cx, cy) with radius r."""
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, yy, 2 * dx + 1, 1, color)

    def ring(self, cx, cy, r, color, thickness=3):
        self.disc(cx, cy, r, color)
        self.disc(cx, cy, r - thickness, PAPER)

    def fill_triangle(self, p0, p1, p2, color):
        (x0, y0), (x1, y1), (x2, y2) = sorted(
            (p0, p1, p2), key=lambda p: p[1]
        )

        def edge_x(xa, ya, xb, yb, y):
            if yb == ya:
                return float(xa)
            return xa + (xb - xa) * (y - ya) / (yb - ya)

        for y in range(y0, y2 + 1):
            if y < y1:
                xa = edge_x(x0, y0, x1, y1, y)
                xb = edge_x(x0, y0, x2, y2, y)
            else:
                xa = edge_x(x1, y1, x2, y2, y)
                xb = edge_x(x0, y0, x2, y2, y)
            lo, hi = sorted((int(xa), int(xb)))
            self.fill_rect(lo, y, hi - lo + 1, 1, color)

    def plus_star(self, cx, cy, r, color):
        """Small four-point star used for the EU circle of stars."""
        self.fill_rect(cx - r, cy - 1, 2 * r + 1, 3, color)
        self.fill_rect(cx - 1, cy - r, 3, 2 * r + 1, color)


# ---------------------------------------------------------------------------
# Text: measure, draw, and word-wrap with the bitmap font.
# ---------------------------------------------------------------------------
CHAR_ADVANCE = 6  # 5 glyph columns + 1 blank column, times the scale


def text_width(text, scale):
    return len(normalise(text)) * CHAR_ADVANCE * scale


def draw_text(cv, x, y, text, scale, color):
    cx = x
    for ch in normalise(text):
        glyph = GLYPHS.get(ch, BLANK)
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "1":
                    cv.fill_rect(
                        cx + col * scale,
                        y + row * scale,
                        scale,
                        scale,
                        color,
                    )
        cx += CHAR_ADVANCE * scale
    return cx


def draw_centred(cv, centre_x, y, text, scale, color):
    draw_text(cv, centre_x - text_width(text, scale) // 2, y, text, scale, color)


def wrap_lines(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    words = normalise(text).split(" ")
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_block(cv, x, y, text, scale, color, max_width, leading):
    """Draw wrapped text; returns the y just below the last line."""
    line_height = 7 * scale
    for line in wrap_lines(text, scale, max_width):
        draw_text(cv, x, y, line, scale, color)
        y += line_height + leading
    return y


def draw_kicker(cv, x, y, text, color=RED):
    """Small red tick followed by a red kicker line."""
    cv.fill_rect(x, y, 10, 7 * 2, color)
    draw_text(cv, x + 18, y, text, 2, color)
    return y + 7 * 2


# ---------------------------------------------------------------------------
# Pictograms: simple geometric drawings, one per story.
# ---------------------------------------------------------------------------
def draw_tariff_bars(cv, x0, baseline):
    """Three rising bars; the tallest, red, carries the 25% rate."""
    widths = (56, 56, 56)
    gaps = 24
    heights = (70, 120, 180)
    colours = (GREY, BLUE, RED)
    x = x0
    for w, h, colour in zip(widths, heights, colours):
        cv.fill_rect(x, baseline - h, w, h, colour)
        x += w + gaps
    cv.hline(x0 - 16, baseline, 3 * 56 + 2 * 24 + 32, INK, 3)
    draw_text(cv, x0 + 2 * (56 + 24) + 1, baseline - 180 + 12, "25%", 3, PAPER)
    draw_centred(cv, x0 + (3 * 56 + 2 * 24) // 2, baseline + 12, "TARIFF RATE", 2, GREY)


def draw_atom(cv, cx, cy):
    cv.ring(cx, cy, 36, BLUE, 3)
    cv.line(cx - 30, cy - 18, cx + 30, cy + 18, BLUE)
    cv.line(cx - 30, cy + 18, cx + 30, cy - 18, BLUE)
    cv.disc(cx, cy, 9, RED)
    cv.disc(cx - 30, cy - 18, 4, GOLD)
    cv.disc(cx + 30, cy + 18, 4, GOLD)


def draw_rocket(cv, cx, cy):
    cv.fill_triangle((cx - 9, cy + 24), (cx + 9, cy + 24), (cx, cy + 48), GOLD)
    cv.fill_triangle((cx - 6, cy + 24), (cx + 6, cy + 24), (cx, cy + 40), RED)
    cv.fill_rect(cx - 14, cy - 32, 28, 56, BLUE)
    cv.fill_triangle((cx, cy - 58), (cx - 14, cy - 32), (cx + 14, cy - 32), RED)
    cv.disc(cx, cy - 12, 6, PAPER)
    cv.fill_triangle((cx - 14, cy + 8), (cx - 30, cy + 26), (cx - 14, cy + 24), GOLD)
    cv.fill_triangle((cx + 14, cy + 8), (cx + 30, cy + 26), (cx + 14, cy + 24), GOLD)


def draw_flame(cv, cx, cy):
    cv.disc(cx, cy + 8, 20, RED)
    cv.fill_triangle((cx - 20, cy + 8), (cx + 20, cy + 8), (cx, cy - 34), RED)
    cv.disc(cx, cy + 12, 10, GOLD)
    cv.fill_triangle((cx - 10, cy + 12), (cx + 10, cy + 12), (cx, cy - 16), GOLD)


def draw_refinery(cv, cx, cy):
    cv.fill_rect(cx - 54, cy - 8, 26, 40, INK)
    cv.fill_rect(cx - 18, cy - 28, 26, 60, BLUE)
    cv.fill_rect(cx + 18, cy, 26, 32, INK)
    cv.fill_rect(cx + 48, cy - 18, 8, 50, GREY)
    cv.disc(cx - 5, cy - 36, 7, RED)
    cv.fill_triangle((cx - 12, cy - 34), (cx + 2, cy - 34), (cx - 5, cy - 50), GOLD)
    cv.hline(cx - 54, cy + 32, 108, INK, 3)


def draw_eu_stars(cv, cx, cy):
    import math

    for k in range(8):
        angle = math.pi * 2 * k / 8 - math.pi / 2
        sx = cx + int(30 * math.cos(angle))
        sy = cy + int(30 * math.sin(angle))
        cv.plus_star(sx, sy, 4, GOLD)
    draw_text(cv, cx - 12, cy - 7, "EU", 2, BLUE)


# ---------------------------------------------------------------------------
# Page layout.
# ---------------------------------------------------------------------------
MARGIN = 36
RIGHT = WIDTH - MARGIN


def build_page():
    cv = Canvas(WIDTH, HEIGHT, PAPER)
    cv.outline_rect(16, 16, WIDTH - 32, HEIGHT - 32, INK, 2)

    # Masthead.
    cv.fill_rect(MARGIN, 30, RIGHT - MARGIN, 5, RED)
    draw_centred(cv, WIDTH // 2, 46, "THE WORLD IN ONE DAY", 6, INK)
    draw_centred(cv, WIDTH // 2, 100, "FRIDAY, 27 NOVEMBER 2026", 3, INK)
    cv.fill_rect(258, 107, 8, 8, RED)
    cv.fill_rect(758, 107, 8, 8, RED)
    cv.hline(MARGIN, 132, RIGHT - MARGIN, INK, 3)

    # Lead story: US tariffs on Indian goods.
    draw_kicker(cv, MARGIN, 152, "TRADE - UNITED STATES / INDIA")
    draw_text(cv, MARGIN, 176, "US PLANS 25% TARIFFS", 5, INK)
    draw_text(cv, MARGIN, 218, "ON INDIAN GOODS", 5, INK)
    draw_block(
        cv,
        MARGIN,
        268,
        "THE UNITED STATES PROPOSES A 25 PERCENT TARIFF ON INDIAN "
        "GOODS, ACCORDING TO THE USTR.",
        2,
        INK,
        660,
        6,
    )
    draw_text(cv, MARGIN, 322, "SOURCE: USTR, VIA REUTERS", 2, GREY)
    draw_tariff_bars(cv, 740, 330)
    cv.hline(MARGIN, 372, RIGHT - MARGIN, INK, 3)

    # Middle row: two stories.
    mid_top = 392
    col_b_x = 520
    cv.vline(508, mid_top, 248, GREY, 2)
    draw_kicker(cv, MARGIN, mid_top, "NORTH KOREA")
    headline_end = draw_block(
        cv, MARGIN, mid_top + 24, "KIM VOWS MORE NUCLEAR WEAPONS", 3, INK, 468, 6
    )
    draw_block(
        cv,
        MARGIN,
        headline_end + 10,
        "KIM JONG UN VOWS TO BUILD MORE NUCLEAR WEAPONS.",
        2,
        INK,
        468,
        6,
    )
    draw_atom(cv, MARGIN + 234, 596)
    draw_kicker(cv, col_b_x, mid_top, "SPACE - UNITED STATES")
    headline_end = draw_block(
        cv,
        col_b_x,
        mid_top + 24,
        "TWO SPACEX SHARES FOR EVERY US CHILD",
        3,
        INK,
        468,
        6,
    )
    draw_block(
        cv,
        col_b_x,
        headline_end + 10,
        "ELON MUSK SAYS TWO SPACEX SHARES WOULD GO TO EVERY CHILD IN "
        "THE UNITED STATES, IN A PLAN WORTH ABOUT $18 BILLION.",
        2,
        INK,
        468,
        6,
    )
    draw_rocket(cv, col_b_x + 234, 596)
    cv.hline(MARGIN, 656, RIGHT - MARGIN, INK, 3)

    # Bottom row: three stories.
    bot_top = 676
    cols = (MARGIN, 358, 680)
    cv.vline(346, bot_top, 248, GREY, 2)
    cv.vline(668, bot_top, 248, GREY, 2)
    stories = [
        (
            "EGYPT",
            "CAIRO TANKER FIRE KILLS 31",
            "A FUEL TANKER FIRE IN CAIRO KILLS 31 PEOPLE, EGYPT'S "
            "HEALTH MINISTRY SAYS.",
            draw_flame,
        ),
        (
            "THAILAND",
            "BLAST SHUTS BANGKOK REFINERY",
            "AN EXPLOSION AND FIRE SHUT A BANGKOK REFINERY AND "
            "INJURE SEVEN PEOPLE.",
            draw_refinery,
        ),
        (
            "EUROPE",
            "EU SPLIT OVER $49BN UKRAINE LOAN",
            "LEADERS IN THE EU ARE SPLIT OVER THE BUDGET AND A $49 "
            "BILLION LOAN FOR UKRAINE.",
            draw_eu_stars,
        ),
    ]
    for x, (kicker, headline, body, picture) in zip(cols, stories):
        draw_kicker(cv, x, bot_top, kicker)
        headline_end = draw_block(cv, x, bot_top + 24, headline, 3, INK, 306, 6)
        draw_block(cv, x, headline_end + 10, body, 2, INK, 306, 6)
        picture(cv, x + 153, 892)

    # Footer.
    cv.hline(MARGIN, 940, RIGHT - MARGIN, INK, 3)
    draw_centred(
        cv,
        WIDTH // 2,
        956,
        "SOURCES: REUTERS - AP - AFP - AL JAZEERA - CNA - KCNA - USTR",
        2,
        GREY,
    )
    draw_centred(
        cv,
        WIDTH // 2,
        978,
        "ALL EVENTS FIRST REPORTED ON FRIDAY, 27 NOVEMBER 2026",
        2,
        GREY,
    )
    return cv


# ---------------------------------------------------------------------------
# PNG writer: filter byte 0 per scanline, one IDAT, fixed compression.
# ---------------------------------------------------------------------------
def png_chunk(kind, data):
    size = struct.pack(">I", len(data))
    crc = struct.pack(">I", crc32(kind + data) & 0xFFFFFFFF)
    return size + kind + data + crc


def write_png(path, cv):
    raw = bytearray()
    for y in range(cv.height):
        raw.append(0)
        start = y * cv.width * 3
        raw += cv.pixels[start:start + cv.width * 3]
    header = struct.pack(">IIBBBBB", cv.width, cv.height, 8, 2, 0, 0, 0)
    blob = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + png_chunk(b"IEND", b"")
    )
    with open(path, "wb") as handle:
        handle.write(blob)
    return len(blob)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(path, build_page())
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
