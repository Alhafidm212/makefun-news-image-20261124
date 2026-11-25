#!/usr/bin/env python3
"""The World — Tuesday 24 November 2026.

One-page newspaper front page, drawn from scratch with the Python
standard library only (no PIL, no network, no fonts on disk).
Renders entry.png (1024x1024) from the day's verified headlines.

Run:  python3 main.py            # writes entry.png to $MAKEFUN_OUTPUT_DIR
                                 # (default /output; the grader mounts /bot read-only)
"""
import hashlib
import os
import struct
import sys
import zlib

W, H = 1024, 1024
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK = (32, 32, 32)

# ---------------------------------------------------------------- 5x7 font
# Every glyph: 7 rows of 5 pixels ('#' = ink). Written out by hand for
# this page; only capitals, digits and the punctuation the copy needs.
FONT = {
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
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
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
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
}
for _g, _rows in FONT.items():
    assert len(_rows) == 7 and all(len(r) == 5 for r in _rows), _g

CHAR_W = 6  # 5 px glyph + 1 px gap, before scaling


def text_width(text, scale):
    return len(text) * CHAR_W * scale - scale


def wrap(text, max_chars):
    """Greedy word wrap; returns list of lines, each <= max_chars."""
    lines, cur = [], ""
    for word in text.split(" "):
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= max_chars:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Page:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.px = bytearray(WHITE * w * h)

    def rect(self, x, y, w, h, color):
        for yy in range(max(0, y), min(self.h, y + h)):
            base = (yy * self.w + max(0, x)) * 3
            for xx in range(max(0, x), min(self.w, x + w)):
                i = (yy * self.w + xx) * 3
                self.px[i:i + 3] = bytes(color)

    def rule(self, x, y, w, thick=2):
        self.rect(x, y, w, thick, BLACK)

    def draw_text(self, x, y, text, scale, color=BLACK):
        cx = x
        for ch in text:
            glyph = FONT.get(ch)
            if glyph is None:
                raise ValueError("no glyph for %r" % ch)
            for row_i, row in enumerate(glyph):
                for col_i, bit in enumerate(row):
                    if bit == "1":
                        self.rect(cx + col_i * scale, y + row_i * scale,
                                  scale, scale, color)
            cx += CHAR_W * scale
        return cx

    def text_block(self, x, y, text, scale, max_chars, color=BLACK,
                   line_gap=None):
        """Draw wrapped text; returns y just below the last line."""
        if line_gap is None:
            line_gap = scale * 2
        for line in wrap(text, max_chars):
            self.draw_text(x, y, line, scale, color)
            y += 7 * scale + line_gap
        return y

    def centered(self, y, text, scale, color=BLACK):
        x = (self.w - text_width(text, scale)) // 2
        self.draw_text(x, y, text, scale, color)
        return y + 7 * scale


# ---------------------------------------------------------------- content
MASTHEAD = "THE WORLD"
DATE_LINE = "TUESDAY 24 NOVEMBER 2026"
KICKER = "LEAKED ROSSTAT DATA"
LEAD_HEAD = "RUSSIAN WAR DEAD NEAR 700,000, LEAKED DATA SHOWS"
LEAD_BODY = (
    "HACKED FIGURES FROM RUSSIA'S OWN STATISTICS AGENCY, STUDIED BY MEDUZA, "
    "MEDIAZONA AND BBC RUSSIAN, PUT CONFIRMED MILITARY DEATHS AT ABOUT 490,000 "
    "- AND ABOUT 700,000 ONCE MISSING TROOPS ARE COUNTED. IT IS THE MOST "
    "COMPLETE TOLL OF THE WAR YET."
)
STORIES = [
    ("UKRAINE SINKS RUSSIAN WARSHIP OFF LIBYA",
     "KYIV SAYS SEA DRONES SANK THE NEW CORVETTE MERKURY IN BENGHAZI PORT ON "
     "SUNDAY AND HIT THE CARGO SHIP MV ANGARA. ZELENSKY CONFIRMED THE RAID "
     "ON MONDAY."),
    ("TRUMP WARNS IRAN TANKERS: TO THE BOTTOM",
     "THE US PRESIDENT SAID IRANIAN TANKERS TRYING TO BREAK THE NAVAL "
     "BLOCKADE WOULD END UP ON THE SEA FLOOR, AND HINTED AT BIG STRIKES "
     "AFTER THE NEW YEAR IF TALKS FAIL."),
    ("COP31 COLLAPSES IN ANTALYA",
     "THE UN CLIMATE SUMMIT ENDED ON SUNDAY WITHOUT A DEAL AFTER A RECORD "
     "TWO WEEKS OF TALKS. THE DRAFT NEVER MENTIONED FOSSIL FUELS; THE EU, "
     "BRITAIN AND NORWAY REJECTED IT."),
    ("NVIDIA SOARS 31.5% AS HUANG RETURNS",
     "SHARES JUMPED ON MONDAY, THE BIGGEST ONE-DAY RISE IN 23 YEARS, "
     "ADDING NEARLY $1 TRILLION IN VALUE. ASIAN MARKETS FOLLOWED ON "
     "TUESDAY, WITH THE NIKKEI UP 4.5%."),
    ("DEMOCRATS TAKE BIGGEST HOUSE EDGE SINCE 1992",
     "THE PARTY SECURED AT LEAST 258 OF 435 SEATS AFTER A RECOUNTED NORTH "
     "CAROLINA RACE WAS WON BY ABOUT 330 VOTES. DEMOCRATS ALSO TOOK THE "
     "SENATE."),
    ("CIKANDE FACTORY FIRE: 24 DEAD, DOZENS MISSING",
     "THE BLAZE AT A CANDY FACTORY IN SERANG, BANTEN, KILLED AT LEAST 24 "
     "PEOPLE ON SATURDAY. BY TUESDAY 26 BODY BAGS WERE FOUND AND 28 "
     "WORKERS REMAINED MISSING."),
]
FOOTER = "THE WORLD  -  TUESDAY 24 NOVEMBER 2026  -  PAGE 1"


def render():
    p = Page()
    mx = 36                      # side margin
    cw = W - 2 * mx              # content width

    y = 28
    y = p.centered(y, MASTHEAD, 10) + 12
    p.rule(mx, y, cw, 4)
    y += 14
    y = p.centered(y, DATE_LINE, 2) + 10
    p.rule(mx, y, cw, 2)
    y += 16
    y = p.centered(y, KICKER, 2, DARK) + 8

    # Lead headline, scale 4, centered lines.
    for line in wrap(LEAD_HEAD, 40):
        y = p.centered(y, line, 4) + 6
    y += 6
    y = p.text_block(mx, y, LEAD_BODY, 2, 78, DARK)
    y += 6
    p.rule(mx, y, cw, 2)
    y += 16
    y = p.centered(y, "MORE FROM THE WORLD", 2) + 6
    p.rule(mx, y, cw, 2)
    y += 18

    # Six stories: two columns, three rows.
    col_w = (cw - 24) // 2
    col_x = [mx, mx + col_w + 24]
    row_y = y
    row_h = 0
    for i, (head, body) in enumerate(STORIES):
        col = i % 2
        x = col_x[col]
        if col == 0 and i > 0:
            row_y += row_h + 30
            row_h = 0
        top = row_y
        yy = p.text_block(x, top, head, 2, col_w // 12)
        yy += 4
        yy = p.text_block(x, yy, body, 2, col_w // 12, DARK)
        row_h = max(row_h, yy - top)
    y = row_y + row_h + 26
    # Anchor the footer near the bottom edge instead of floating after
    # the last story, so the page reads as one finished sheet.
    fy = max(y, 952)
    p.rule(mx, fy, cw, 2)
    p.centered(fy + 12, FOOTER, 1, DARK)
    return p


# ---------------------------------------------------------------- PNG out
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def save_png(page, path):
    raw = bytearray()
    stride = page.w * 3
    for row in range(page.h):
        raw.append(0)  # filter: none
        raw += page.px[row * stride:(row + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", page.w, page.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    page = render()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    path = os.path.join(out_dir, "entry.png")
    n = save_png(page, path)
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print("entry.png %dx%d %d bytes sha256 %s" % (W, H, n, digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
