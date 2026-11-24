#!/usr/bin/env python3
"""Draw "The World in One Day - Monday, 23 November 2026".

A 1024x1024 newspaper front page, drawn with the Python standard library
only (zlib + struct for the PNG encoder, math for geometry). No network, no
timestamps, no randomness: the same input always produces the same bytes.

Run:  python3 draw.py [output-path]     (default: entry.png)
"""

import math
import struct
import sys
import zlib
from hashlib import sha256

W, H = 1024, 1024

# Palette: warm newsprint, restrained ink + one red accent.
PAPER = (248, 244, 232)
INK = (20, 20, 20)
RED = (178, 34, 24)
BLUE = (29, 78, 137)
GREEN = (23, 114, 69)
LIGHT_GREEN = (205, 235, 214)
GOLD = (201, 162, 39)
GRAY = (107, 100, 85)
TINT = (238, 233, 219)
WHITE = (255, 255, 255)
LIGHT_GRAY = (190, 184, 170)

# 5x7 bitmap font, uppercase + digits + punctuation. Each glyph is 7 rows of
# 5 characters ('#' = ink, '.' = empty). Written for this entry.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
}


def text_width(s, scale):
    """Pixel width of s at the given integer scale (6 px advance per char)."""
    return len(s) * 6 * scale - scale if s else 0


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            if 0 <= yy < self.h:
                x0, x1 = max(x, 0), min(x + w, self.w)
                for xx in range(x0, x1):
                    i = (yy * self.w + xx) * 3
                    self.px[i:i + 3] = bytes(color)

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        """Bresenham line, with a square brush of side `thick`."""
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.rect(x0 - thick // 2, y0 - thick // 2, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            dx = int(math.sqrt(max(r * r - (yy - cy) ** 2, 0)))
            self.rect(cx - dx, yy, 2 * dx + 1, 1, color)

    def polygon(self, points, color):
        """Scanline fill for a simple polygon (list of (x, y))."""
        if not points:
            return
        ys = [p[1] for p in points]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(int(math.ceil(xs[i])), y,
                          int(math.floor(xs[i + 1])) - int(math.ceil(xs[i])) + 1,
                          1, color)

    def text(self, x, y, s, scale, color):
        for ci, ch in enumerate(s):
            glyph = FONT.get(ch)
            if glyph is None:
                continue
            ox = x + ci * 6 * scale
            for row, bits in enumerate(glyph):
                for col, bit in enumerate(bits):
                    if bit == '1':
                        self.rect(ox + col * scale, y + row * scale,
                                  scale, scale, color)
        return x + text_width(s, scale)

    def text_center(self, cx, y, s, scale, color):
        return self.text(cx - text_width(s, scale) // 2, y, s, scale, color)

    def text_right(self, x, y, s, scale, color):
        return self.text(x - text_width(s, scale), y, s, scale, color)


def wrap(s, max_width, scale):
    """Greedy word wrap; returns a list of lines fitting max_width px."""
    words, lines, cur = s.split(' '), [], ''
    for word in words:
        trial = word if not cur else cur + ' ' + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def png_bytes(canvas):
    """Encode the canvas as a deterministic PNG (filter 0, zlib level 9)."""
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        out = struct.pack('>I', len(data)) + kind + data
        return out + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)

    ihdr = struct.pack('>IIBBBBB', canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', comp) + chunk(b'IEND', b''))


# ---------------------------------------------------------------- illustrations
def draw_ship(c, x, y, w):
    """Warship silhouette on waves (story 2, Libya). Local origin top-left."""
    c.rect(x, y, w, 80, TINT)
    # hull + superstructure + mast + flag
    c.polygon([(x + 30, y + 34), (x + 210, y + 34), (x + 195, y + 56),
               (x + 45, y + 56)], INK)
    c.rect(x + 95, y + 18, 46, 16, INK)
    c.rect(x + 150, y + 20, 14, 14, INK)
    c.vline(x + 118, y + 4, 15, INK, 2)
    c.polygon([(x + 118, y + 4), (x + 136, y + 8), (x + 118, y + 12)], RED)
    # naval drones overhead
    c.circle(x + 238, y + 12, 3, BLUE)
    c.circle(x + 258, y + 22, 3, BLUE)
    c.line(x + 238, y + 15, x + 250, y + 20, BLUE, 1)
    # waves
    for yy, off in ((y + 64, 0), (y + 70, 24), (y + 76, 8)):
        xx = x + 16 + off
        while xx < x + w - 30:
            c.hline(xx, yy, 18, BLUE, 2)
            xx += 34


def draw_tanker(c, x, y, w):
    """Oil tanker under a drone (story 3, Hormuz). Local origin top-left."""
    c.rect(x, y, w, 80, TINT)
    c.circle(x + 252, y + 18, 10, RED)          # low sun
    c.circle(x + 62, y + 12, 3, INK)            # drone
    c.line(x + 62, y + 15, x + 62, y + 22, INK, 1)
    c.rect(x + 24, y + 40, 220, 18, INK)        # hull
    c.polygon([(x + 244, y + 40), (x + 268, y + 49), (x + 244, y + 58)], INK)
    c.rect(x + 196, y + 18, 26, 22, INK)        # bridge tower
    c.rect(x + 60, y + 30, 30, 10, INK)         # deckhouse
    for yy, off in ((y + 64, 0), (y + 70, 30), (y + 76, 12)):
        xx = x + 16 + off
        while xx < x + w - 30:
            c.hline(xx, yy, 18, BLUE, 2)
            xx += 34


def draw_awacs(c, x, y, w):
    """AWACS jet with its radar dome (story 4, NATO). Local origin top-left."""
    c.rect(x, y, w, 80, TINT)
    # clouds
    c.circle(x + 36, y + 16, 7, WHITE)
    c.circle(x + 48, y + 14, 9, WHITE)
    c.circle(x + 262, y + 62, 7, WHITE)
    c.circle(x + 274, y + 60, 9, WHITE)
    # tail fin rising from the rear of the fuselage
    c.polygon([(x + 54, y + 36), (x + 46, y + 14), (x + 60, y + 14),
               (x + 70, y + 36)], INK)
    # fuselage + nose cone
    c.rect(x + 54, y + 36, 166, 12, INK)
    c.polygon([(x + 220, y + 36), (x + 246, y + 42), (x + 220, y + 48)], INK)
    # radar dome: a blue disc sitting on top of the fuselage
    c.circle(x + 136, y + 34, 12, BLUE)
    c.circle(x + 136, y + 34, 12, INK)
    c.circle(x + 136, y + 34, 9, BLUE)
    # swept wing below the fuselage
    c.polygon([(x + 118, y + 48), (x + 150, y + 66), (x + 162, y + 66),
               (x + 140, y + 48)], INK)
    c.hline(x + 16, y + 72, w - 32, LIGHT_GRAY, 1)


def draw_eu(c, x, y, w):
    """EU columns + flag disc with 22 (story 5, sanctions)."""
    c.rect(x, y, w, 80, TINT)
    c.polygon([(x + 40, y + 26), (x + 118, y + 8), (x + 196, y + 26)], INK)
    for cx in (x + 52, x + 108, x + 164):
        c.rect(cx, y + 28, 16, 30, INK)
    c.rect(x + 40, y + 58, 172, 8, INK)
    # blue disc with 12 gold stars and the number 22
    c.circle(x + 256, y + 26, 20, BLUE)
    for k in range(12):
        a = 2 * math.pi * k / 12 - math.pi / 2
        c.circle(int(x + 256 + 14 * math.cos(a)),
                 int(y + 26 + 14 * math.sin(a)), 2, GOLD)
    c.text_center(x + 256, y + 19, '22', 2, WHITE)


def draw_mountains(c, x, y, w):
    """Himalayan peaks + sun (story 6, Nepal). Local origin top-left."""
    c.rect(x, y, w, 80, TINT)
    c.circle(x + 258, y + 16, 9, GOLD)          # sun
    c.polygon([(x + 16, y + 70), (x + 70, y + 16), (x + 124, y + 70)], BLUE)
    c.polygon([(x + 58, y + 28), (x + 70, y + 16), (x + 82, y + 28)], WHITE)
    c.polygon([(x + 92, y + 70), (x + 152, y + 8), (x + 212, y + 70)], INK)
    c.polygon([(x + 138, y + 22), (x + 152, y + 8), (x + 166, y + 22)], WHITE)
    c.polygon([(x + 176, y + 70), (x + 224, y + 24), (x + 272, y + 70)], GRAY)
    c.polygon([(x + 214, y + 34), (x + 224, y + 24), (x + 234, y + 34)], WHITE)
    c.hline(x + 16, y + 70, w - 32, INK, 2)


def draw_chart(c, x, y, w, h):
    """Nvidia one-day chart panel (lead visual). Origin top-left of panel."""
    c.rect(x, y, w, h, WHITE)
    c.rect(x, y, w, 2, INK)
    c.rect(x, y + h - 2, w, 2, INK)
    c.rect(x, y, 2, h, INK)
    c.rect(x + w - 2, y, 2, h, INK)
    c.text(x + 14, y + 12, 'NVIDIA (NVDA)', 1, INK)
    c.text_right(x + w - 14, y + 12, '+31.5% IN ONE DAY', 2, GREEN)
    # plot area
    px0, px1 = x + 20, x + w - 20
    py0, py1 = y + 44, y + h - 64
    for gy in range(5):
        yy = py0 + (py1 - py0) * gy // 4
        c.hline(px0, yy, px1 - px0, LIGHT_GRAY, 1)
    # rising line, 12 Nov (low) -> 23 Nov (high)
    pts = [(0.00, 0.10), (0.14, 0.16), (0.28, 0.08), (0.42, 0.26),
           (0.56, 0.20), (0.70, 0.44), (0.84, 0.66), (1.00, 0.92)]
    xy = [(px0 + t * (px1 - px0), py1 - v * (py1 - py0)) for t, v in pts]
    area = [(px0, py1)] + xy + [(px1, py1)]
    c.polygon([(int(a), int(b)) for a, b in area], LIGHT_GREEN)
    for i in range(len(xy) - 1):
        x0, y0 = xy[i]
        x1, y1 = xy[i + 1]
        c.line(int(x0), int(y0), int(x1), int(y1), GREEN, 3)
    c.circle(int(xy[-1][0]), int(xy[-1][1]), 5, GREEN)
    c.text(px0, py1 + 10, 'NOV 12', 1, GRAY)
    c.text_right(px1, py1 + 10, 'NOV 23', 1, GRAY)
    c.text_center(x + w // 2, y + h - 26, 'NASDAQ +6%   S&P 500 +4%', 1, INK)


# ---------------------------------------------------------------- page layout
def story_cell(c, x, y, w, art, kicker, headline, deck):
    art(c, x, y, w)
    c.text(x, y + 88, kicker, 1, RED)
    c.text(x, y + 108, headline, 2, INK)
    yy = y + 134
    for line in wrap(deck, w, 1):
        c.text(x, yy, line, 1, INK)
        yy += 11


def numbers_box(c, x, y, w, h):
    c.rect(x, y, w, h, INK)
    c.text(x + 12, y + 12, 'THE DAY IN NUMBERS', 1, GOLD)
    rows = [('NVIDIA', '+31.5%', GREEN), ('NASDAQ', '+6%', GREEN),
            ('S&P 500', '+4%', GREEN), ('NEPAL AID', '$1.62BN', GOLD),
            ('EU BANKS CUT', '60', WHITE)]
    yy = y + 44
    for label, value, vcolor in rows:
        c.text(x + 12, yy, label, 2, WHITE)
        c.text_right(x + w - 12, yy, value, 2, vcolor)
        yy += 30


def draw_newspaper():
    c = Canvas(W, H, PAPER)
    # masthead
    c.hline(32, 28, 960, RED, 3)
    c.text_center(512, 40, 'THE WORLD IN ONE DAY', 6, INK)
    c.text_center(512, 92, 'MONDAY, 23 NOVEMBER 2026', 2, INK)
    c.text_center(512, 118, 'SIX STORIES THAT DEFINED THE DAY', 1, GRAY)
    c.hline(32, 140, 960, INK, 3)
    c.hline(32, 145, 960, INK, 1)

    # ---- lead story: Nvidia
    c.text(32, 160, 'MARKETS - NEW YORK', 1, RED)
    c.text(32, 184, 'HUANG IS BACK', 5, INK)
    c.text(32, 224, 'SHARES SOAR 31%', 5, INK)
    yy = 278
    deck = ('NVIDIA REINSTATES ITS FOUNDER-CEO 11 DAYS AFTER HIS SHOCK EXIT. '
            'THE STOCK JUMPS 31%, ADDING $952 BILLION IN A SINGLE DAY.')
    for line in wrap(deck, 560, 2):
        c.text(32, yy, line, 2, INK)
        yy += 19
    c.hline(32, 352, 560, LIGHT_GRAY, 1)
    c.text(32, 366, 'MARKET SNAPSHOT', 1, RED)
    snap = [('NASDAQ', '+6%'), ('S&P 500', '+4%'), ('NVIDIA', '+31.5%')]
    yy = 388
    for label, value in snap:
        c.text(32, yy, label, 2, INK)
        c.text_right(592, yy, value, 2, GREEN)
        yy += 26
    draw_chart(c, 620, 158, 372, 300)

    # ---- divider + grid of five stories + numbers box
    c.hline(32, 474, 960, INK, 2)
    cols = [32, 359, 686]
    rows = [488, 716]
    c.vline(353, 488, 444, LIGHT_GRAY, 1)
    c.vline(680, 488, 444, LIGHT_GRAY, 1)
    c.hline(32, 710, 960, LIGHT_GRAY, 1)

    story_cell(c, cols[0], rows[0], 306, draw_ship, 'WAR AT SEA - LIBYA',
               'WAR SPREADS TO LIBYA',
               'UKRAINE SAYS IT SANK THE RUSSIAN CORVETTE MERKURY OFF '
               'BENGHAZI WITH SEVEN NAVAL DRONES.')
    story_cell(c, cols[1], rows[0], 306, draw_tanker, 'MIDDLE EAST',
               'HORMUZ ON EDGE',
               'IRAN VOWS TO FIGHT THE US NAVAL BLOCKADE AND SAYS IT '
               'DOWNED A US DRONE.')
    story_cell(c, cols[2], rows[0], 306, draw_awacs, 'EUROPE - SECURITY',
               'NATO WATCHES POLAND',
               'AWACS EARLY-WARNING JETS HEAD EAST AFTER THREE RUSSIAN '
               'MISSILES LANDED IN POLAND.')
    story_cell(c, cols[0], rows[1], 306, draw_eu, 'BRUSSELS',
               'EU TURNS THE SCREWS',
               '22ND SANCTIONS PACKAGE HITS 60 BANKS, CRYPTO NETWORKS AND '
               "THE SHADOW FLEET.")
    story_cell(c, cols[1], rows[1], 306, draw_mountains, 'SOUTH ASIA',
               'A LIFELINE FOR NEPAL',
               "INDIA PLEDGES $1.62 BILLION TO REBUILD AFTER AUGUST'S "
               'GLACIER FLOOD KILLED 1,500.')
    numbers_box(c, cols[2], rows[1], 306, 216)

    # ---- footer
    c.hline(32, 946, 960, INK, 2)
    c.text_center(512, 958,
                  'SOURCES: REUTERS, CNN, THE WALL STREET JOURNAL, '
                  'ASSOCIATED PRESS, EUROPEAN COMMISSION', 1, GRAY)
    c.text_center(512, 974,
                  'ALL EVENTS FIRST REPORTED MONDAY, 23 NOVEMBER 2026',
                  1, GRAY)
    return c


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'entry.png'
    data = png_bytes(draw_newspaper())
    with open(out, 'wb') as f:
        f.write(data)
    print(f'wrote {out}: {len(data)} bytes  sha256={sha256(data).hexdigest()}')


if __name__ == '__main__':
    main()
