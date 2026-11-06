#!/usr/bin/env python3
"""
Clean-Room Procedural Map & WAD Builder for Counter-Strike: Condition Zero
Map: de_raid (Bomb Defusal)
Layout inspiration: CoD4 custom map mp_bo2raid3 by Hugo (remake of Black Ops 2 "Raid").
ZERO CoD4 / Activision assets (.ff, .iwd, models, textures, sounds) are read or used.

Generates:
  1. czero/de_raid.wad          (16 original 8-bit WAD3 textures with 4 mip levels)
  2. maps/de_raid.map           (Valve 220 GoldSrc brush geometry + CS/CZ entities)
  3. czero/overviews/de_raid.tga (1024x768 24-bit GoldSrc radar overview image)
  4. czero/overviews/de_raid.bmp (1024x768 8-bit fallback radar overview image)
  5. czero/overviews/de_raid.txt (GoldSrc overview calibration file)
  6. czero/maps/de_raid.txt      (Map briefing & clean-room attribution)
  7. czero/maps/de_raid.res      (Server fast-download / VPN resource manifest)
"""

from __future__ import annotations

import math
import os
import struct
from typing import Dict, List, Optional, Tuple

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# ============================================================================
# PART 1: ORIGINAL 8-BIT WAD3 TEXTURE GENERATOR (czero/de_raid.wad)
# ============================================================================

BITMAP_FONT_5X7: Dict[str, List[str]] = {
    "A": [
        " 111 ",
        "1   1",
        "1   1",
        "11111",
        "1   1",
        "1   1",
        "1   1",
    ],
    "B": [
        "1111 ",
        "1   1",
        "1   1",
        "1111 ",
        "1   1",
        "1   1",
        "1111 ",
    ],
    "S": [
        " 1111",
        "1    ",
        "1    ",
        " 111 ",
        "    1",
        "    1",
        "1111 ",
    ],
    "I": [
        "11111",
        "  1  ",
        "  1  ",
        "  1  ",
        "  1  ",
        "  1  ",
        "11111",
    ],
    "T": [
        "11111",
        "  1  ",
        "  1  ",
        "  1  ",
        "  1  ",
        "  1  ",
        "  1  ",
    ],
    "E": [
        "11111",
        "1    ",
        "1    ",
        "1111 ",
        "1    ",
        "1    ",
        "11111",
    ],
}


def _hash2d(x: int, y: int, seed: int = 1337) -> int:
    n = (x * 374761393 + y * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n ^ (n >> 16)) & 0xFF


def _clamp(v: int) -> int:
    return 0 if v < 0 else (255 if v > 255 else v)


def _draw_glyph(
    grid: List[List[int]],
    ch: str,
    ox: int,
    oy: int,
    scale: int,
    color_idx: int,
) -> None:
    rows = BITMAP_FONT_5X7.get(ch)
    if not rows:
        return
    h = len(grid)
    w = len(grid[0])
    for ry, row in enumerate(rows):
        for rx, bit in enumerate(row):
            if bit == "1":
                for sy in range(scale):
                    for sx in range(scale):
                        py = oy + ry * scale + sy
                        px = ox + rx * scale + sx
                        if 0 <= py < h and 0 <= px < w:
                            grid[py][px] = color_idx


def _pack_miptex(
    name: str,
    width: int,
    height: int,
    palette: List[Tuple[int, int, int]],
    indices_2d: List[List[int]],
) -> bytes:
    """Pack an 8-bit indexed image into a valid GoldSrc WAD3 miptex (type 0x43)."""
    assert len(name) <= 15, f"Texture name too long: {name}"
    assert width % 16 == 0 and height % 16 == 0
    assert len(palette) <= 256
    pal = list(palette) + [(0, 0, 0)] * (256 - len(palette))
    # Ensure index 255 is non-transparent blue only if '{' prefix is not used
    pal_bytes = b"".join(struct.pack("BBB", r, g, b) for (r, g, b) in pal)

    mips: List[bytes] = []
    for level in range(4):
        step = 1 << level
        mw = width // step
        mh = height // step
        buf = bytearray(mw * mh)
        pos = 0
        for y in range(mh):
            src_row = indices_2d[y * step]
            for x in range(mw):
                buf[pos] = src_row[x * step]
                pos += 1
        mips.append(bytes(buf))

    header_size = 40  # 16s + II + 4I
    off0 = header_size
    off1 = off0 + len(mips[0])
    off2 = off1 + len(mips[1])
    off3 = off2 + len(mips[2])

    name_bytes = name.encode("ascii")[:15].ljust(16, b"\x00")
    hdr = struct.pack("<16sIIIIII", name_bytes, width, height, off0, off1, off2, off3)
    # WAD3 miptex footer: uint16 palette_count (256), 768 bytes RGB, uint16 padding
    footer = struct.pack("<H", 256) + pal_bytes + struct.pack("<H", 0)
    return hdr + b"".join(mips) + footer


def build_custom_wad(wad_path: str) -> List[str]:
    """Create czero/de_raid.wad with 16 clean original 8-bit textures."""
    textures: List[Tuple[str, bytes]] = []

    # 1. RAID_STUCCOW (128x128) - Crisp white modern architectural stucco with reveal grooves
    pal_stucco = [(_clamp(226 + i - 16), _clamp(224 + i - 16), _clamp(218 + i - 16)) for i in range(32)]
    pal_stucco.append((182, 180, 174))  # idx 32: architectural reveal groove
    g = [[(_hash2d(x, y, 11) % 14) + 10 for x in range(128)] for y in range(128)]
    for y in (0, 63, 64, 127):
        for x in range(128):
            g[y][x] = 32
    textures.append(("RAID_STUCCOW", _pack_miptex("RAID_STUCCOW", 128, 128, pal_stucco, g)))

    # 2. RAID_WOODPNL (128x128) - Warm modern horizontal cedar slat siding
    pal_wood = []
    for i in range(32):
        pal_wood.append((_clamp(142 + i * 2), _clamp(88 + int(i * 1.3)), _clamp(46 + i)))
    pal_wood.append((58, 36, 20))  # idx 32: dark shadow gap between slats
    g = [[0] * 128 for _ in range(128)]
    for y in range(128):
        slat = y // 16
        in_slat = y % 16
        if in_slat in (0, 15):
            for x in range(128):
                g[y][x] = 32
        else:
            plank_tone = ((slat * 7) % 10) + 6
            for x in range(128):
                grain = (_hash2d(x // 4, y + slat * 19, 23) % 8) - 4
                g[y][x] = max(0, min(31, plank_tone + grain))
    textures.append(("RAID_WOODPNL", _pack_miptex("RAID_WOODPNL", 128, 128, pal_wood, g)))

    # 3. RAID_TRAVERT (128x128) - Warm cream courtyard travertine stone pavers (64x64 grid)
    pal_trav = [(_clamp(204 + i), _clamp(192 + i), _clamp(168 + i)) for i in range(28)]
    pal_trav.append((150, 140, 122))  # idx 28: grout line
    g = [[0] * 128 for _ in range(128)]
    for y in range(128):
        for x in range(128):
            ox = x + (32 if (y // 64) % 2 == 1 else 0)
            if y % 64 in (0, 63) or ox % 64 in (0, 63):
                g[y][x] = 28
            else:
                vein = (_hash2d(x // 2, y, 37) % 14) + ((ox // 64 + y // 64) * 3 % 8)
                g[y][x] = min(27, vein)
    textures.append(("RAID_TRAVERT", _pack_miptex("RAID_TRAVERT", 128, 128, pal_trav, g)))

    # 4. RAID_MARBLE (128x128) - Polished luxury light-charcoal/pearl interior marble tile
    pal_marb = [(_clamp(198 + i * 2), _clamp(202 + i * 2), _clamp(208 + i * 2)) for i in range(24)]
    pal_marb.append((126, 132, 140))  # 24: subtle grey marble vein
    pal_marb.append((96, 102, 110))   # 25: tile seam
    g = [[0] * 128 for _ in range(128)]
    for y in range(128):
        for x in range(128):
            if x % 64 == 0 or y % 64 == 0:
                g[y][x] = 25
            else:
                wave = int(8 + 6 * math.sin((x + y * 1.4) * 0.11) + (_hash2d(x, y, 51) % 6))
                g[y][x] = 24 if wave > 17 else max(0, min(23, wave))
    textures.append(("RAID_MARBLE", _pack_miptex("RAID_MARBLE", 128, 128, pal_marb, g)))

    # 5. RAID_GARFLR (128x128) - Epoxy coated luxury garage floor with yellow bay line
    pal_gar = [(_clamp(88 + i * 2), _clamp(92 + i * 2), _clamp(98 + i * 2)) for i in range(20)]
    pal_gar.append((68, 72, 78))     # 20: expansion joint
    pal_gar.append((218, 180, 42))   # 21: yellow bay stripe
    g = [[(_hash2d(x, y, 67) % 10) + 4 for x in range(128)] for y in range(128)]
    for y in range(128):
        for x in range(128):
            if x in (0, 127) or y in (0, 127):
                g[y][x] = 20
            elif x in (3, 4, 5):
                g[y][x] = 21
    textures.append(("RAID_GARFLR", _pack_miptex("RAID_GARFLR", 128, 128, pal_gar, g)))

    # 6. RAID_COURT (128x128) - Royal-blue painted basketball court surface + crisp white lines
    pal_crt = [(_clamp(28 + i), _clamp(76 + i * 2), _clamp(138 + i * 2)) for i in range(20)]
    pal_crt.append((242, 244, 246))  # 20: crisp white boundary line
    g = [[(_hash2d(x, y, 79) % 10) + 5 for x in range(128)] for y in range(128)]
    for i in range(128):
        for t in (0, 1, 2):
            g[t][i] = 20
            g[i][t] = 20
    textures.append(("RAID_COURT", _pack_miptex("RAID_COURT", 128, 128, pal_crt, g)))

    # 7. RAID_COURTKEY (128x128) - Forest-green painted basketball key lane + white stripe
    pal_key = [(_clamp(34 + i), _clamp(108 + i * 2), _clamp(68 + i)) for i in range(20)]
    pal_key.append((242, 244, 246))  # 20: crisp white lane line
    g = [[(_hash2d(x, y, 83) % 10) + 5 for x in range(128)] for y in range(128)]
    for i in range(128):
        for t in (0, 1, 2, 125, 126, 127):
            g[t][i] = 20
            g[i][t] = 20
    textures.append(("RAID_COURTKEY", _pack_miptex("RAID_COURTKEY", 128, 128, pal_key, g)))

    # 8. RAID_BKBOARD (128x64) - Basketball backboard with orange border & shooter's square
    pal_bb = [
        (238, 242, 246),  # 0: white tempered glass board
        (224, 230, 236),  # 1: subtle glass sheen
        (230, 74, 25),    # 2: bright orange target markings
        (54, 60, 68),     # 3: dark outer aluminum frame
    ]
    g = [[1 if ((x + y) % 16 < 4) else 0 for x in range(128)] for y in range(64)]
    for y in range(64):
        for x in range(128):
            if x < 3 or x >= 125 or y < 3 or y >= 61:
                g[y][x] = 3
            elif x in (4, 5, 122, 123) or y in (4, 5, 58, 59):
                g[y][x] = 2
            # Shooter's target box centered horizontally (x: 44..84, y: 26..52)
            elif (44 <= x <= 84 and y in (26, 27, 28, 50, 51, 52)) or (
                26 <= y <= 52 and x in (44, 45, 46, 82, 83, 84)
            ):
                g[y][x] = 2
    textures.append(("RAID_BKBOARD", _pack_miptex("RAID_BKBOARD", 128, 64, pal_bb, g)))

    # 9. RAID_HOOPORG (64x64) - Bright orange basketball rim metal
    pal_hoop = [(_clamp(215 + i * 2), _clamp(72 + i * 2), _clamp(18 + i)) for i in range(16)]
    g = [[(_hash2d(x, y, 97) % 12) + 2 for x in range(64)] for y in range(64)]
    textures.append(("RAID_HOOPORG", _pack_miptex("RAID_HOOPORG", 64, 64, pal_hoop, g)))

    # 10. !RAID_WATER (64x64) - Sunlit turquoise swimming pool water ('!' = animated liquid)
    pal_wat = []
    for i in range(32):
        pal_wat.append((_clamp(18 + i * 3), _clamp(155 + i * 3), _clamp(205 + int(i * 1.5))))
    g = [[0] * 64 for _ in range(64)]
    for y in range(64):
        for x in range(64):
            caustic = int(
                14
                + 8 * math.sin(x * math.pi / 16.0) * math.cos(y * math.pi / 16.0)
                + 5 * math.sin((x + y) * math.pi / 16.0)
            )
            g[y][x] = max(0, min(31, caustic))
    textures.append(("!RAID_WATER", _pack_miptex("!RAID_WATER", 64, 64, pal_wat, g)))

    # 11. RAID_POOLTIL (64x64) - Mosaic cobalt & aqua ceramic pool tile
    pal_pt = [
        (24, 118, 186),
        (36, 142, 208),
        (58, 168, 224),
        (18, 96, 160),
        (195, 232, 248),  # 4: light grout
    ]
    g = [[0] * 64 for _ in range(64)]
    for y in range(64):
        for x in range(64):
            if x % 8 == 0 or y % 8 == 0:
                g[y][x] = 4
            else:
                g[y][x] = _hash2d(x // 8, y // 8, 113) % 4
    textures.append(("RAID_POOLTIL", _pack_miptex("RAID_POOLTIL", 64, 64, pal_pt, g)))

    # 12 & 13. RAID_SIGN_A / RAID_SIGN_B (128x64) - Architectural Bombsite A & B plaques
    for letter in ("A", "B"):
        pal_sign = [
            (32, 36, 42),     # 0: brushed dark slate background
            (44, 48, 56),     # 1: slate texture variation
            (228, 62, 42),    # 2: high-visibility crimson-orange emblem
            (244, 244, 240),  # 3: crisp white text/border
        ]
        g = [[_hash2d(x, y, 131) % 2 for x in range(128)] for y in range(64)]
        # Outer white/red accent frame
        for y in range(64):
            for x in range(128):
                if x in (2, 3, 124, 125) or y in (2, 3, 60, 61):
                    g[y][x] = 2
                elif x in (6, 121) or y in (6, 57):
                    g[y][x] = 3
        # Draw "SITE A" / "SITE B"
        text = f"SITE {letter}"
        ox = 14
        for ch in text:
            if ch != " ":
                col = 2 if ch == letter else 3
                _draw_glyph(g, ch, ox, 14, 5, col)
            ox += 18 if ch != " " else 10
        tname = f"RAID_SIGN_{letter}"
        textures.append((tname, _pack_miptex(tname, 128, 64, pal_sign, g)))

    # 14 & 15. RAID_CAR_RED / RAID_CAR_BLU (128x64) - Glossy luxury sports car body panels
    for cname, base_rgb in (("RAID_CAR_RED", (186, 26, 34)), ("RAID_CAR_BLU", (28, 68, 156))):
        br, bg, bb = base_rgb
        pal_car = [
            (br, bg, bb),
            (_clamp(br + 28), _clamp(bg + 28), _clamp(bb + 28)),  # metallic highlight
            (_clamp(br - 32), _clamp(bg - 20), _clamp(bb - 20)),  # lower rocker shade
            (28, 32, 38),                                         # dark trim / wheel arch strip
            (210, 218, 226),                                      # chrome trim line
        ]
        g = [[0] * 128 for _ in range(64)]
        for y in range(64):
            for x in range(128):
                if y < 6 or y >= 56:
                    g[y][x] = 3
                elif y in (20, 21):
                    g[y][x] = 4
                elif 8 <= y <= 18:
                    g[y][x] = 1
                elif y >= 42:
                    g[y][x] = 2
                else:
                    g[y][x] = 0
        textures.append((cname, _pack_miptex(cname, 128, 64, pal_car, g)))

    # 16. RAID_GOLD (64x64) - Brushed bronze/gold courtyard statue relief
    pal_gold = [(_clamp(168 + i * 4), _clamp(132 + i * 3), _clamp(48 + i * 2)) for i in range(20)]
    g = [[(_hash2d(x, y, 149) % 14) + (4 if (x % 16 in (0, 15) or y % 16 in (0, 15)) else 0) for x in range(64)] for y in range(64)]
    textures.append(("RAID_GOLD", _pack_miptex("RAID_GOLD", 64, 64, pal_gold, g)))

    # Assemble WAD3 file
    os.makedirs(os.path.dirname(wad_path), exist_ok=True)
    num_tex = len(textures)
    chunks = bytearray()
    dir_entries = bytearray()
    offset = 12  # WAD3 header is 12 bytes
    for tname, blob in textures:
        pad = (4 - (len(blob) % 4)) % 4
        padded = blob + (b"\x00" * pad)
        chunks.extend(padded)
        name16 = tname.encode("ascii")[:15].ljust(16, b"\x00")
        dir_entries.extend(
            struct.pack("<IIIbbH16s", offset, len(blob), len(blob), 0x43, 0, 0, name16)
        )
        offset += len(padded)

    wad_hdr = struct.pack("<4sII", b"WAD3", num_tex, offset)
    with open(wad_path, "wb") as wf:
        wf.write(wad_hdr)
        wf.write(chunks)
        wf.write(dir_entries)

    return [t[0] for t in textures]


# ============================================================================
# PART 2: VALVE 220 .MAP GEOMETRY & ENTITY BUILDER (maps/de_raid.map)
# ============================================================================

class MapBuilder:
    def __init__(self) -> None:
        self.world_brushes: List[str] = []
        self.entities: List[str] = []
        # Store floor/wall/water/site rectangles for rendering exact 2D radar overview
        self.radar_floors: List[Tuple[int, int, int, int, Tuple[int, int, int]]] = []
        self.radar_walls: List[Tuple[int, int, int, int, Tuple[int, int, int]]] = []
        self.radar_water: List[Tuple[int, int, int, int]] = []
        self.radar_props: List[Tuple[int, int, int, int, Tuple[int, int, int]]] = []

    @staticmethod
    def make_box(
        x1: int,
        y1: int,
        z1: int,
        x2: int,
        y2: int,
        z2: int,
        tex: str = "RAID_STUCCOW",
        face_tex: Optional[Dict[str, str]] = None,
        scale: float = 1.0,
    ) -> str:
        assert x1 < x2 and y1 < y2 and z1 < z2, f"Invalid brush bounds: {(x1,y1,z1)}..{(x2,y2,z2)}"
        ft = face_tex or {}
        t_top = ft.get("top", tex)
        t_bot = ft.get("bottom", tex)
        t_west = ft.get("west", tex)
        t_east = ft.get("east", tex)
        t_north = ft.get("north", tex)
        t_south = ft.get("south", tex)
        s = f"{scale:g}"

        lines = [
            "{",
            # Top (+Z)
            f"( {x1} {y2} {z2} ) ( {x2} {y2} {z2} ) ( {x2} {y1} {z2} ) {t_top} [ 1 0 0 0 ] [ 0 -1 0 0 ] 0 {s} {s}",
            # Bottom (-Z)
            f"( {x1} {y1} {z1} ) ( {x2} {y1} {z1} ) ( {x2} {y2} {z1} ) {t_bot} [ 1 0 0 0 ] [ 0 -1 0 0 ] 0 {s} {s}",
            # West (-X)
            f"( {x1} {y2} {z2} ) ( {x1} {y1} {z2} ) ( {x1} {y1} {z1} ) {t_west} [ 0 1 0 0 ] [ 0 0 -1 0 ] 0 {s} {s}",
            # East (+X)
            f"( {x2} {y1} {z2} ) ( {x2} {y2} {z2} ) ( {x2} {y2} {z1} ) {t_east} [ 0 1 0 0 ] [ 0 0 -1 0 ] 0 {s} {s}",
            # North (+Y)
            f"( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) ( {x1} {y2} {z1} ) {t_north} [ 1 0 0 0 ] [ 0 0 -1 0 ] 0 {s} {s}",
            # South (-Y)
            f"( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) ( {x2} {y1} {z1} ) {t_south} [ 1 0 0 0 ] [ 0 0 -1 0 ] 0 {s} {s}",
            "}",
        ]
        return "\n".join(lines)

    def add_world_box(
        self,
        x1: int,
        y1: int,
        z1: int,
        x2: int,
        y2: int,
        z2: int,
        tex: str = "RAID_STUCCOW",
        face_tex: Optional[Dict[str, str]] = None,
        scale: float = 1.0,
        radar_kind: Optional[str] = None,
        radar_rgb: Optional[Tuple[int, int, int]] = None,
    ) -> None:
        self.world_brushes.append(self.make_box(x1, y1, z1, x2, y2, z2, tex, face_tex, scale))
        if radar_kind == "floor" and radar_rgb:
            self.radar_floors.append((x1, y1, x2, y2, radar_rgb))
        elif radar_kind == "wall":
            self.radar_walls.append((x1, y1, x2, y2, radar_rgb or (225, 228, 232)))
        elif radar_kind == "prop" and radar_rgb:
            self.radar_props.append((x1, y1, x2, y2, radar_rgb))

    def add_wall_with_doors(
        self,
        axis: str,
        fixed_min: int,
        fixed_max: int,
        span_min: int,
        span_max: int,
        z_bottom: int,
        z_top: int,
        doors: List[Tuple[int, int, int]],
        tex: str = "RAID_STUCCOW",
        header_tex: Optional[str] = None,
    ) -> None:
        """
        Build a solid VIS-blocking axial wall along 'x' (fixed X thickness, spanning Y)
        or 'y' (fixed Y thickness, spanning X), carving clean upright doorways (d_start, d_end, d_ztop).
        """
        doors_sorted = sorted(doors, key=lambda d: d[0])
        cursor = span_min
        htex = header_tex or tex
        for d0, d1, dz in doors_sorted:
            if d0 > cursor:
                if axis == "x":
                    self.add_world_box(fixed_min, cursor, z_bottom, fixed_max, d0, z_top, tex, radar_kind="wall")
                else:
                    self.add_world_box(cursor, fixed_min, z_bottom, d0, fixed_max, z_top, tex, radar_kind="wall")
            if dz < z_top:
                if axis == "x":
                    self.add_world_box(fixed_min, d0, dz, fixed_max, d1, z_top, htex)
                else:
                    self.add_world_box(d0, fixed_min, dz, d1, fixed_max, z_top, htex)
            cursor = d1
        if cursor < span_max:
            if axis == "x":
                self.add_world_box(fixed_min, cursor, z_bottom, fixed_max, span_max, z_top, tex, radar_kind="wall")
            else:
                self.add_world_box(cursor, fixed_min, z_bottom, span_max, fixed_max, z_top, tex, radar_kind="wall")

    def add_point_entity(self, classname: str, kv: Dict[str, str]) -> None:
        lines = ["{", f'"classname" "{classname}"']
        for k, v in kv.items():
            lines.append(f'"{k}" "{v}"')
        lines.append("}")
        self.entities.append("\n".join(lines))

    def add_brush_entity(self, classname: str, kv: Dict[str, str], brushes: List[str]) -> None:
        lines = ["{", f'"classname" "{classname}"']
        for k, v in kv.items():
            lines.append(f'"{k}" "{v}"')
        lines.extend(brushes)
        lines.append("}")
        self.entities.append("\n".join(lines))

    def add_func_wall_box(
        self,
        x1: int,
        y1: int,
        z1: int,
        x2: int,
        y2: int,
        z2: int,
        tex: str,
        face_tex: Optional[Dict[str, str]] = None,
        scale: float = 1.0,
        extra_kv: Optional[Dict[str, str]] = None,
        radar_rgb: Optional[Tuple[int, int, int]] = None,
    ) -> None:
        kv = dict(extra_kv or {})
        self.add_brush_entity("func_wall", kv, [self.make_box(x1, y1, z1, x2, y2, z2, tex, face_tex, scale)])
        if radar_rgb:
            self.radar_props.append((x1, y1, x2, y2, radar_rgb))

    def export_map(self, map_path: str, wad_paths: List[str]) -> None:
        os.makedirs(os.path.dirname(map_path), exist_ok=True)
        wad_str = ";".join(wad_paths) + ";"
        out = [
            "{",
            '"classname" "worldspawn"',
            '"mapversion" "220"',
            '"skyname" "sienna"',
            '"MaxRange" "8192"',
            '"message" "Raid - Hillside Mansion (de_raid)"',
            f'"wad" "{wad_str}"',
        ]
        out.extend(self.world_brushes)
        out.append("}")
        out.extend(self.entities)
        with open(map_path, "w", encoding="ascii", newline="\n") as mf:
            mf.write("\n".join(out) + "\n")


def construct_de_raid(wad_paths: List[str], map_path: str) -> MapBuilder:
    mb = MapBuilder()

    # ========================================================================
    # 1. WATERTIGHT OUTER SKYBOX & SUB-BASE SEAL
    #    Playable X: -1664..+1664 | Playable Y: -1984..+1984 | Z: -64..+416
    # ========================================================================
    # Sub-floor bedrock slab sealing entire footprint underneath (Z: -128..-64)
    mb.add_world_box(-1728, -2048, -128, 1728, 2048, -64, "NULL")
    # Sky ceiling slab (Z: +416..+448)
    mb.add_world_box(-1728, -2048, 416, 1728, 2048, 448, "SKY")

    # Outer architectural boundary walls (lower stucco/wood Z: -64..192, upper SKY Z: 192..416)
    # West perimeter (X: -1728..-1664)
    mb.add_world_box(-1728, -2048, -64, -1664, 2048, 224, "RAID_STUCCOW", radar_kind="wall")
    mb.add_world_box(-1728, -2048, 224, -1664, 2048, 416, "SKY")
    # East perimeter (X: +1664..+1728)
    mb.add_world_box(1664, -2048, -64, 1728, 2048, 192, "RAID_WOODPNL", radar_kind="wall")
    mb.add_world_box(1664, -2048, 192, 1728, 2048, 416, "SKY")
    # North perimeter (Y: +1984..+2048)
    mb.add_world_box(-1664, 1984, -64, 1664, 2048, 192, "RAID_STUCCOW", radar_kind="wall")
    mb.add_world_box(-1664, 1984, 192, 1664, 2048, 416, "SKY")
    # South perimeter (Y: -2048..-1984)
    mb.add_world_box(-1664, -2048, -64, 1664, -1984, 192, "RAID_WOODPNL", radar_kind="wall")
    mb.add_world_box(-1664, -2048, 192, 1664, -1984, 416, "SKY")

    # ========================================================================
    # 2. ZONE FLOORS (Z = 0 standard ground; Pool basin sunken to Z = -32)
    # ========================================================================
    # North T Spawn: Driveway (X: -1664..+1664, Y: +1280..+1984)
    mb.add_world_box(-1664, 1280, -64, 1664, 1984, 0, "SandRoad", radar_kind="floor", radar_rgb=(78, 82, 88))

    # South CT Spawn: Basketball Court & Back Patio (X: -1664..+1664, Y: -1984..-1280)
    mb.add_world_box(-1664, -1984, -64, -640, -1280, 0, "djWalk1", radar_kind="floor", radar_rgb=(132, 126, 114))
    mb.add_world_box(640, -1984, -64, 1664, -1280, 0, "djWalk1", radar_kind="floor", radar_rgb=(132, 126, 114))
    mb.add_world_box(-640, -1536, -64, 640, -1280, 0, "RAID_COURT", radar_kind="floor", radar_rgb=(38, 88, 152))
    mb.add_world_box(-640, -1984, -64, -192, -1536, 0, "RAID_COURT", radar_kind="floor", radar_rgb=(38, 88, 152))
    mb.add_world_box(192, -1984, -64, 640, -1536, 0, "RAID_COURT", radar_kind="floor", radar_rgb=(38, 88, 152))
    mb.add_world_box(-192, -1984, -64, 192, -1536, 0, "RAID_COURTKEY", radar_kind="floor", radar_rgb=(44, 118, 76))

    # West Lane: Garage (Bombsite B) (X: -1664..-896, Y: -128..+1280) with Bombsite B floor inlay
    mb.add_world_box(-1664, -128, -64, -1408, 1280, 0, "RAID_GARFLR", radar_kind="floor", radar_rgb=(96, 100, 108))
    mb.add_world_box(-1152, -128, -64, -896, 1280, 0, "RAID_GARFLR", radar_kind="floor", radar_rgb=(96, 100, 108))
    mb.add_world_box(-1408, -128, -64, -1152, 320, 0, "RAID_GARFLR", radar_kind="floor", radar_rgb=(96, 100, 108))
    mb.add_world_box(-1408, 576, -64, -1152, 1280, 0, "RAID_GARFLR", radar_kind="floor", radar_rgb=(96, 100, 108))
    mb.add_world_box(-1408, 320, -64, -1152, 576, 0, "djWalkBombB", radar_kind="floor", radar_rgb=(176, 68, 56))

    # West Lane: Laundry (X: -1664..-960, Y: -1280..-128)
    mb.add_world_box(-1664, -1280, -64, -960, -128, 0, "CSTRIKE_CH3TILE", radar_kind="floor", radar_rgb=(116, 122, 128))

    # West-Mid: Kitchen (-960..-384, Y: -896..-128) & South Alcove (-960..-384, Y: -1280..-896)
    mb.add_world_box(-960, -896, -64, -384, -128, 0, "RAID_MARBLE", radar_kind="floor", radar_rgb=(162, 166, 174))
    mb.add_world_box(-960, -1280, -64, -384, -896, 0, "djWalk1", radar_kind="floor", radar_rgb=(132, 126, 114))

    # Mid-West: Mansion Lounge (-896..-256, Y: -128..+640) & Vault (-896..-256, Y: +640..+1280)
    mb.add_world_box(-896, -128, -64, -256, 640, 0, "RAID_MARBLE", radar_kind="floor", radar_rgb=(172, 176, 184))
    mb.add_world_box(-896, 640, -64, -256, 1280, 0, "RAID_MARBLE", radar_kind="floor", radar_rgb=(156, 162, 170))

    # Center: Courtyard ("Ring"), North Courtyard Plaza & Patio Steps
    mb.add_world_box(-256, -640, -64, 640, 1280, 0, "RAID_TRAVERT", radar_kind="floor", radar_rgb=(188, 176, 152))
    mb.add_world_box(-384, -1280, -64, 640, -640, 0, "RAID_TRAVERT", radar_kind="floor", radar_rgb=(180, 168, 146))

    # Mid-East Connector: Cutout & adjacent courtyard pockets (X: 640..896, Y: -1280..+640)
    mb.add_world_box(640, -1280, -64, 896, 640, 0, "RAID_TRAVERT", radar_kind="floor", radar_rgb=(174, 162, 140))

    # East Lane: Garden (X: 640..1664, Y: +640..+1280)
    mb.add_world_box(640, 640, -64, 1664, 1280, 0, "djWalk1", radar_kind="floor", radar_rgb=(146, 140, 124))

    # East Lane: Pool Deck & Sunken Shallow Walkable Pool (X: 896..1664, Y: -256..+640)
    # Dry Pool Decks surrounding the water basin (basin = X: 1120..1504, Y: -128..+512)
    mb.add_world_box(896, -256, -64, 1120, 640, 0, "RAID_TRAVERT", radar_kind="floor", radar_rgb=(188, 176, 152))
    mb.add_world_box(1504, -256, -64, 1664, 640, 0, "RAID_TRAVERT", radar_kind="floor", radar_rgb=(188, 176, 152))
    mb.add_world_box(1120, -256, -64, 1504, -128, 0, "RAID_TRAVERT", radar_kind="floor", radar_rgb=(188, 176, 152))
    mb.add_world_box(1120, 512, -64, 1504, 640, 0, "RAID_TRAVERT", radar_kind="floor", radar_rgb=(188, 176, 152))

    # Sunken Pool Floor (Z: -64..-32, 32 units deep -> shallow knee-deep so bots never drown!)
    mb.add_world_box(1120, -128, -64, 1504, 512, -32, "RAID_POOLTIL", radar_kind="floor", radar_rgb=(36, 148, 212))
    mb.radar_water.append((1120, -128, 1504, 512))
    # Smooth 8-unit walk-out pool steps on North, South, and West pool edges so bots exit effortlessly
    for idx, ztop in enumerate((-24, -16, -8)):
        # North pool steps (Y: +512 down into pool)
        mb.add_world_box(1120, 496 - idx * 16, -32, 1504, 512 - idx * 16, ztop, "RAID_POOLTIL")
        # South pool steps (Y: -128 up into pool)
        mb.add_world_box(1120, -128 + idx * 16, -32, 1504, -112 + idx * 16, ztop, "RAID_POOLTIL")
    # Translucent animated water brush entity inside Pool basin (Z: -32..-4)
    mb.add_brush_entity(
        "func_water",
        {
            "skin": "-3",
            "rendermode": "2",
            "renderamt": "135",
            "rendercolor": "0 0 0",
            "WaveHeight": "1.2",
            "speed": "100",
            "wait": "4",
            "angles": "0 0 0",
        },
        [mb.make_box(1120, -128, -32, 1504, 512, -4, "!RAID_WATER")],
    )

    # East Lane: Gazebo (Bombsite A) (X: 896..1664, Y: -1280..-256) with Bombsite A floor inlay
    mb.add_world_box(896, -1280, -64, 1152, -256, 0, "djWalk1", radar_kind="floor", radar_rgb=(146, 140, 124))
    mb.add_world_box(1408, -1280, -64, 1664, -256, 0, "djWalk1", radar_kind="floor", radar_rgb=(146, 140, 124))
    mb.add_world_box(1152, -1280, -64, 1408, -832, 0, "djWalk1", radar_kind="floor", radar_rgb=(146, 140, 124))
    mb.add_world_box(1152, -576, -64, 1408, -256, 0, "djWalk1", radar_kind="floor", radar_rgb=(146, 140, 124))
    mb.add_world_box(1152, -832, -64, 1408, -576, 0, "djWalkBombA", radar_kind="floor", radar_rgb=(186, 74, 58))

    # ========================================================================
    # 3. STRUCTURAL VIS-BLOCKING WALLS, CHOKEPOINTS & ROOFS
    # ========================================================================
    # --- North Spawn Divider Wall (Y = +1280..+1312) ---
    # Four clean lane entries from T Driveway:
    #   1) Choke 1 Garage Bay Doors: X -1472..-1024 (448w, z=176)
    #   2) Vault Office Entry:       X -704..-480  (224w, z=160)
    #   3) Mid North Colonnade Arch: X -160..+352  (512w, z=192)
    #   4) East Garden Path:         X +896..+1408 (512w, z=192)
    mb.add_wall_with_doors(
        axis="y",
        fixed_min=1280,
        fixed_max=1312,
        span_min=-1664,
        span_max=1664,
        z_bottom=0,
        z_top=224,
        doors=[
            (-1472, -1024, 176),
            (-704, -480, 160),
            (-160, 352, 192),
            (896, 1408, 192),
        ],
        tex="RAID_STUCCOW",
        header_tex="RAID_WOODPNL",
    )

    # --- South Spawn Divider Wall (Y = -1312..-1280) ---
    # Three clean lane entries from CT Basketball Court:
    #   1) Laundry West Connector:   X -1472..-1152 (320w, z=160)
    #   2) Patio Steps Mid Arch:     X -256..+384   (640w, z=192)
    #   3) Gazebo / Bombsite A Deck: X +1024..+1472 (448w, z=192)
    mb.add_wall_with_doors(
        axis="y",
        fixed_min=-1312,
        fixed_max=-1280,
        span_min=-1664,
        span_max=1664,
        z_bottom=0,
        z_top=224,
        doors=[
            (-1472, -1152, 160),
            (-256, 384, 192),
            (1024, 1472, 192),
        ],
        tex="RAID_STUCCOW",
        header_tex="RAID_WOODPNL",
    )

    # --- Garage <-> Mansion Wall (X = -928..-896, Y: -128..+1280) ---
    # Wide double door between Garage (Site B) and Mansion Lounge at Y: +256..+480
    mb.add_wall_with_doors(
        axis="x",
        fixed_min=-928,
        fixed_max=-896,
        span_min=-128,
        span_max=1280,
        z_bottom=0,
        z_top=256,
        doors=[(256, 480, 160)],
        tex="RAID_STUCCOW",
        header_tex="conc33",
    )

    # --- Garage / Mansion South Divider (Y = -160..-128, X: -1664..-256) ---
    # Connects Garage <-> Laundry (X: -1472..-1152) and Mansion <-> Kitchen (X: -768..-512)
    mb.add_wall_with_doors(
        axis="y",
        fixed_min=-160,
        fixed_max=-128,
        span_min=-1664,
        span_max=-256,
        z_bottom=0,
        z_top=256,
        doors=[
            (-1472, -1152, 160),
            (-768, -512, 160),
        ],
        tex="RAID_STUCCOW",
    )

    # --- Laundry <-> Kitchen Wall (X = -992..-960, Y: -1280..-160) ---
    # Choke 2 West entry: Laundry <-> Kitchen doorway at Y: -640..-384
    mb.add_wall_with_doors(
        axis="x",
        fixed_min=-992,
        fixed_max=-960,
        span_min=-1280,
        span_max=-160,
        z_bottom=0,
        z_top=224,
        doors=[(-640, -384, 160)],
        tex="RAID_STUCCOW",
    )

    # --- Kitchen South Wall (Y = -928..-896, X: -960..-384) ---
    mb.add_world_box(-960, -928, 0, -384, -896, 224, "RAID_STUCCOW", radar_kind="wall")

    # --- Kitchen East Wall to Patio / Courtyard (X = -416..-384, Y: -928..-160) ---
    # Choke 2 East exit: Kitchen <-> Courtyard / Patio Steps at Y: -640..-384
    mb.add_wall_with_doors(
        axis="x",
        fixed_min=-416,
        fixed_max=-384,
        span_min=-928,
        span_max=-160,
        z_bottom=0,
        z_top=224,
        doors=[(-640, -384, 160)],
        tex="RAID_WOODPNL",
    )

    # --- Vault <-> Mansion Divider Wall (Y = +640..+672, X: -896..-256) ---
    mb.add_wall_with_doors(
        axis="y",
        fixed_min=640,
        fixed_max=672,
        span_min=-896,
        span_max=-256,
        z_bottom=0,
        z_top=256,
        doors=[(-704, -448, 160)],
        tex="RAID_STUCCOW",
    )

    # --- Mansion / Vault East Facade to Courtyard (X = -288..-256, Y: -160..+1280) ---
    # Ground doorways clearly separated from Balcony stairs (Y: -320..+384):
    #   - Mansion North Courtyard Door: Y +416..+608 (192w, z=160)
    #   - Vault East Plaza Door:        Y +832..+1088 (256w, z=160)
    #   - Upper Balcony Doorway:        Y -96..+128 (Z: +96..+208 -> carved separately!)
    mb.add_wall_with_doors(
        axis="x",
        fixed_min=-288,
        fixed_max=-256,
        span_min=-160,
        span_max=1280,
        z_bottom=0,
        z_top=256,
        doors=[
            (416, 608, 160),
            (832, 1088, 160),
        ],
        tex="RAID_STUCCOW",
        header_tex="RAID_WOODPNL",
    )

    # --- Courtyard <-> East Lane Wall & Choke 3 "Cutout" ---
    # West wall of Cutout/East Wing (X = +640..+672, Y: -1280..+1280):
    #   - North Courtyard <-> Garden arch: Y +832..+1088 (256w, z=176)
    #   - Choke 3 Cutout West breach:      Y -160..+160  (320w, z=160)
    #   - South Patio <-> Gazebo arch:     Y -960..-704  (256w, z=176)
    mb.add_wall_with_doors(
        axis="x",
        fixed_min=640,
        fixed_max=672,
        span_min=-1280,
        span_max=1280,
        z_bottom=0,
        z_top=224,
        doors=[
            (-960, -704, 176),
            (-160, 160, 160),
            (832, 1088, 176),
        ],
        tex="RAID_STUCCOW",
        header_tex="RAID_WOODPNL",
    )

    # East wall of Cutout onto Pool Deck (X = +864..+896, Y: -640..+640):
    #   - Choke 3 Cutout East exit onto Pool Deck: Y -160..+160 (320w, z=160)
    mb.add_wall_with_doors(
        axis="x",
        fixed_min=864,
        fixed_max=896,
        span_min=-640,
        span_max=640,
        z_bottom=0,
        z_top=224,
        doors=[(-160, 160, 160)],
        tex="RAID_WOODPNL",
    )
    # Side walls sealing Cutout corridor (Y = -352..-320 and Y = +320..+352, X: +672..+864)
    mb.add_world_box(672, -352, 0, 864, -320, 224, "RAID_STUCCOW", radar_kind="wall")
    mb.add_world_box(672, 320, 0, 864, 352, 224, "RAID_STUCCOW", radar_kind="wall")

    # --- INDOOR ROOFS (solid ceilings for VIS occlusion & realistic indoor lighting) ---
    # Garage Roof (X: -1664..-896, Y: -160..+1312, Z: 256..288)
    mb.add_world_box(-1664, -160, 256, -896, 1312, 288, "conc33")
    # Mansion & Vault Roof (X: -896..-256, Y: -160..+1312, Z: 256..288)
    mb.add_world_box(-896, -160, 256, -256, 1312, 288, "conc33")
    # Laundry Roof (X: -1664..-960, Y: -1312..-160, Z: 224..256)
    mb.add_world_box(-1664, -1312, 224, -960, -160, 256, "conc33")
    # Kitchen Roof (X: -960..-384, Y: -928..-160, Z: 224..256)
    mb.add_world_box(-960, -928, 224, -384, -160, 256, "conc33")
    # Cutout Breezeway Roof (X: +640..+896, Y: -352..+352, Z: 224..256)
    mb.add_world_box(640, -352, 224, 896, 352, 256, "conc33")

    # ========================================================================
    # 4. ELEVATED BALCONY & SMOOTH BOT-FRIENDLY STAIRS (Mid Courtyard Overlook)
    # ========================================================================
    # Balcony elevated platform along West Courtyard (X: -256..-128, Y: -128..+192, Z: 0..+96)
    mb.add_world_box(
        -256,
        -128,
        0,
        -128,
        192,
        96,
        "RAID_STUCCOW",
        face_tex={"top": "RAID_TRAVERT"},
        radar_kind="floor",
        radar_rgb=(208, 196, 172),
    )
    # Low protective Balcony parapet overlooking Courtyard (X: -144..-128, Y: -112..+176, Z: 96..132)
    mb.add_func_wall_box(-144, -112, 96, -128, 176, 132, "RAID_WOODPNL", radar_rgb=(156, 104, 58))

    # North Balcony Staircase (12 steps of 8u rise x 16u run, 128u wide: Y +384 down to +192)
    for s in range(12):
        z_step = (s + 1) * 8
        y_hi = 384 - s * 16
        y_lo = y_hi - 16
        mb.add_world_box(-256, y_lo, 0, -128, y_hi, z_step, "djSteps1")

    # South Balcony Staircase (12 steps of 8u rise x 16u run, 128u wide: Y -320 up to -128)
    for s in range(12):
        z_step = (s + 1) * 8
        y_lo = -320 + s * 16
        y_hi = y_lo + 16
        mb.add_world_box(-256, y_lo, 0, -128, y_hi, z_step, "djSteps1")

    # ========================================================================
    # 5. ICONIC LANDMARKS & FUNC_WALL DETAIL BRUSHES (Low wpoly, Bot-Safe!)
    # ========================================================================
    # --- A) COURTYARD ("RING"): 4 Corner Pillars + Lion Pedestal ---
    for px, py in ((-16, 224), (336, 224), (-16, -288), (336, -288)):
        mb.add_func_wall_box(px, py, 0, px + 64, py + 64, 224, "RAID_STUCCOW", radar_rgb=(230, 230, 230))
    # Centerpiece Lion / Guardian Statue Pedestal (X: 128..256, Y: -64..+64)
    mb.add_func_wall_box(128, -64, 0, 256, 64, 44, "djRock1", radar_rgb=(140, 132, 118))
    mb.add_func_wall_box(152, -40, 44, 232, 40, 124, "RAID_GOLD", radar_rgb=(204, 168, 68))

    # --- B) GAZEBO (BOMBSITE A): Covered Pavilion, Sign Plaques & Jacuzzi Cover ---
    for gx, gy in ((1056, -928), (1456, -928), (1056, -528), (1456, -528)):
        mb.add_func_wall_box(gx, gy, 0, gx + 48, gy + 48, 192, "RAID_WOODPNL", radar_rgb=(156, 104, 58))
    # Gazebo Pergola Roof (Z: 192..224)
    mb.add_func_wall_box(
        1040,
        -944,
        192,
        1520,
        -464,
        224,
        "RAID_WOODPNL",
        face_tex={"top": "i_roof_tile1"},
    )
    # Bombsite A Plaques mounted on North and South Gazebo fascia beams
    mb.add_func_wall_box(
        1216,
        -464,
        160,
        1344,
        -456,
        224,
        "RAID_STUCCOW",
        face_tex={"north": "RAID_SIGN_A", "south": "RAID_SIGN_A"},
    )
    mb.add_func_wall_box(
        1216,
        -952,
        160,
        1344,
        -944,
        224,
        "RAID_STUCCOW",
        face_tex={"north": "RAID_SIGN_A", "south": "RAID_SIGN_A"},
    )
    # Waist-high Poolside Planter / Spa Cover Box at Center of Site A (walkable 150u+ all around)
    mb.add_func_wall_box(
        1216,
        -752,
        0,
        1344,
        -656,
        44,
        "RAID_WOODPNL",
        face_tex={"top": "RAID_POOLTIL"},
        radar_rgb=(58, 168, 224),
    )

    # --- C) GARAGE (BOMBSITE B): Two Brush Luxury Sports Sedans & Site B Plaques ---
    # Car 1 (Crimson Sedan, West Bay: X -1552..-1408, Y +640..+928) -> leaves >=144u clearance
    mb.add_func_wall_box(-1552, 640, 0, -1408, 928, 44, "RAID_CAR_RED", radar_rgb=(186, 36, 42))
    mb.add_func_wall_box(
        -1536,
        704,
        44,
        -1424,
        856,
        76,
        "GLASSBLUE2",
        face_tex={"top": "RAID_CAR_RED"},
    )
    # Car 2 (Midnight-Blue Coupe, East Bay: X -1120..-976, Y +64..+352)
    mb.add_func_wall_box(-1120, 64, 0, -976, 352, 44, "RAID_CAR_BLU", radar_rgb=(42, 82, 168))
    mb.add_func_wall_box(
        -1104,
        128,
        44,
        -992,
        280,
        76,
        "GLASSBLUE2",
        face_tex={"top": "RAID_CAR_BLU"},
    )
    # Bombsite B Plaques on Garage North & West walls
    mb.add_func_wall_box(
        -1664,
        384,
        96,
        -1656,
        512,
        160,
        "RAID_STUCCOW",
        face_tex={"east": "RAID_SIGN_B"},
    )
    mb.add_func_wall_box(
        -1344,
        1272,
        112,
        -1216,
        1280,
        176,
        "RAID_STUCCOW",
        face_tex={"south": "RAID_SIGN_B"},
    )

    # --- D) COURT (CT SPAWN): Decorative Basketball Hoop (func_wall) ---
    # Support post at south boundary (X: -12..+12, Y: -1984..-1956, Z: 0..164)
    mb.add_func_wall_box(-12, -1984, 0, 12, -1956, 164, "conc33", radar_rgb=(180, 180, 185))
    # Gooseneck extension arm (Z: 140..156, above player head height!)
    mb.add_func_wall_box(-10, -1956, 140, 10, -1920, 156, "conc33")
    # Tempered-style backboard (X: -64..+64, Y: -1920..-1912, Z: 108..172)
    mb.add_func_wall_box(
        -64,
        -1920,
        108,
        64,
        -1912,
        172,
        "conc33",
        face_tex={"north": "RAID_BKBOARD"},
        radar_rgb=(235, 238, 242),
    )
    # Bright Orange Rim at Z: 114..120 (well above 72u player height so zero head-snag!)
    mb.add_func_wall_box(-20, -1912, 114, -14, -1876, 120, "RAID_HOOPORG", radar_rgb=(230, 74, 25))
    mb.add_func_wall_box(14, -1912, 114, 20, -1876, 120, "RAID_HOOPORG", radar_rgb=(230, 74, 25))
    mb.add_func_wall_box(-20, -1882, 114, 20, -1876, 120, "RAID_HOOPORG", radar_rgb=(230, 74, 25))

    # --- E) MANSION ART HALL, KITCHEN ISLAND, DRIVEWAY PLANTER & GARDEN PLANTER ---
    # 4 Gallery Paintings along Mansion Lounge West Wall (X: -896..-890)
    for idx, (py, ptex, pw) in enumerate(
        (
            (-32, "painting01", 128),
            (128, "painting02", 128),
            (512, "painting04", 128),
        )
    ):
        mb.add_func_wall_box(
            -896,
            py,
            64,
            -890,
            py + pw,
            192,
            "RAID_WOODPNL",
            face_tex={"east": ptex},
        )
    # Kitchen Island Counter (chest-high tactical cover, >=192u clear path all around)
    mb.add_func_wall_box(
        -752,
        -592,
        0,
        -608,
        -432,
        42,
        "RAID_WOODPNL",
        face_tex={"top": "RAID_MARBLE"},
        radar_rgb=(142, 96, 54),
    )
    # Driveway Roundabout Island Planter (North T Spawn)
    mb.add_func_wall_box(
        -224,
        1568,
        0,
        224,
        1760,
        36,
        "djRock1",
        face_tex={"top": "djGrass1"},
        radar_rgb=(68, 128, 62),
    )
    mb.add_func_wall_box(-32, 1632, 36, 32, 1696, 148, "RAID_WOODPNL", radar_rgb=(156, 104, 58))
    # East Garden Raised Planter Strip along outer East wall
    mb.add_func_wall_box(
        1552,
        704,
        0,
        1664,
        1216,
        40,
        "djRock1",
        face_tex={"top": "djGrass1"},
        radar_rgb=(68, 128, 62),
    )

    # ========================================================================
    # 6. GAMEPLAY ENTITIES (Spawns, Buyzones, Bomb Targets, Lights, Ambience)
    # ========================================================================
    # Map Parameters (both teams can buy, standard 500 bomb radius)
    mb.add_point_entity(
        "info_map_parameters",
        {
            "origin": "0 0 128",
            "buying": "0",
            "bombradius": "500",
        },
    )

    # 16 Terrorist Spawns (info_player_deathmatch) in North Driveway facing South (270 deg)
    t_xs = [-1280, -960, -640, -384, 384, 640, 960, 1280]
    for sy in (1856, 1424):
        for sx in t_xs:
            mb.add_point_entity(
                "info_player_deathmatch",
                {
                    "origin": f"{sx} {sy} 36",
                    "angles": "0 270 0",
                },
            )

    # 16 Counter-Terrorist Spawns (info_player_start) in South Court facing North (90 deg)
    ct_xs = [-1280, -960, -640, -320, 320, 640, 960, 1280]
    for sy in (-1824, -1440):
        for sx in ct_xs:
            mb.add_point_entity(
                "info_player_start",
                {
                    "origin": f"{sx} {sy} 36",
                    "angles": "0 90 0",
                },
            )

    # Buyzones (team 1 = Terrorist, team 2 = Counter-Terrorist)
    mb.add_brush_entity(
        "func_buyzone",
        {"team": "1"},
        [mb.make_box(-1472, 1328, 0, 1472, 1952, 160, "AAATRIGGER")],
    )
    mb.add_brush_entity(
        "func_buyzone",
        {"team": "2"},
        [mb.make_box(-1472, -1952, 0, 1472, -1328, 160, "AAATRIGGER")],
    )

    # Bombsite A (Gazebo / Pool Deck)
    mb.add_point_entity("info_target", {"targetname": "tgt_a", "origin": "1280 -704 36"})
    mb.add_brush_entity(
        "func_bomb_target",
        {"target": "tgt_a"},
        [mb.make_box(1072, -912, 0, 1488, -496, 128, "AAATRIGGER")],
    )

    # Bombsite B (Garage)
    mb.add_point_entity("info_target", {"targetname": "tgt_b", "origin": "-1280 448 36"})
    mb.add_brush_entity(
        "func_bomb_target",
        {"target": "tgt_b"},
        [mb.make_box(-1456, 224, 0, -1104, 672, 128, "AAATRIGGER")],
    )

    # Sunlight & Sky Illumination (Warm California Hillside Sun + Crisp Sky Bounce)
    mb.add_point_entity(
        "light_environment",
        {
            "origin": "0 0 360",
            "angles": "0 48 0",
            "pitch": "-62",
            "_light": "252 242 212 220",
            "_diffuse_light": "168 188 242 175",
        },
    )

    # Indoor & Accent Point Lights (eliminates dark corners inside Garage, Mansion, Vault, Laundry, Kitchen, Cutout, Gazebo)
    indoor_lights = [
        # Garage (Bombsite B)
        (-1280, 960, 216, "245 245 255 240"),
        (-1280, 448, 216, "255 235 215 260"),
        (-1280, 32, 216, "245 245 255 230"),
        # Laundry
        (-1312, -448, 192, "235 242 255 210"),
        (-1312, -960, 192, "235 242 255 210"),
        # Kitchen
        (-672, -512, 192, "255 244 224 240"),
        # Mansion Lounge & Art Hall
        (-576, 64, 224, "255 242 218 250"),
        (-576, 448, 224, "255 242 218 250"),
        # Vault Office
        (-576, 960, 208, "240 246 255 230"),
        # Cutout Breezeway
        (768, 0, 192, "255 244 224 220"),
        # Gazebo Pavilion under-roof warm glow (Bombsite A)
        (1280, -704, 176, "255 232 196 220"),
        # Underwater subtle pool glow
        (1312, 192, 48, "180 235 255 150"),
    ]
    for lx, ly, lz, lcol in indoor_lights:
        mb.add_point_entity("light", {"origin": f"{lx} {ly} {lz}", "_light": lcol})

    # Spectator Overview Camera
    mb.add_point_entity(
        "trigger_camera",
        {
            "origin": "480 -560 280",
            "angles": "24 135 0",
            "wait": "10",
        },
    )

    # Ambient Soundscapes (100% stock CZ/CS sounds verified on disk)
    ambients = [
        ("1312 192 64", "ambience/waterfall4.wav", "5"),       # Poolside water circulation
        ("192 0 128", "ambience/wind_litegust.wav", "5"),      # Central Courtyard breeze
        ("0 1664 112", "ambience/dist_traffic1.wav", "5"),     # Distant LA valley traffic at Driveway
        ("1280 960 112", "ambience/Birds2.wav", "5"),          # Hillside garden birds
        ("0 -1664 112", "ambience/wind_litegust.wav", "4"),    # South Court patio breeze
    ]
    for a_orig, a_wav, a_vol in ambients:
        mb.add_point_entity(
            "ambient_generic",
            {
                "origin": a_orig,
                "message": a_wav,
                "health": a_vol,
                "preset": "0",
                "volstart": a_vol,
                "pitch": "100",
                "pitchstart": "100",
                "spawnflags": "4",
            },
        )

    mb.export_map(map_path, wad_paths)
    return mb


# ============================================================================
# PART 3: RADAR OVERVIEW (.tga + .bmp + .txt), BRIEFING (.txt) & .RES MANIFEST
# ============================================================================

def write_radar_overview(mb: MapBuilder, tga_path: str, bmp_path: str, txt_path: str) -> None:
    """
    Render a crisp 1024x768 top-down radar image directly from our map geometry.
    GoldSrc overview projection (ROTATED = 0, ORIGIN = 0 0 0, ZOOM = 1.45):
      x_span = 8192 / ZOOM = 5649.655 units (-2824.8 .. +2824.8)
      y_span = 6144 / ZOOM = 4237.241 units (-2118.6 .. +2118.6)
    Pure green RGB (0, 255, 0) is GoldSrc's transparent radar key color.
    """
    W, H = 1024, 768
    ZOOM = 1.45
    x_span = 8192.0 / ZOOM
    y_span = x_span * (H / W)

    # Palette index 0 = transparent pure green (0, 255, 0)
    rgb_buf = [[(0, 255, 0) for _ in range(W)] for _ in range(H)]

    def world_rect_to_px(wx1: int, wy1: int, wx2: int, wy2: int) -> Tuple[int, int, int, int]:
        # In GoldSrc ROTATED 0: screen X left->right = world X min->max; screen Y top->bottom = world Y max->min
        px1 = int(round((wx1 + x_span * 0.5) / x_span * W))
        px2 = int(round((wx2 + x_span * 0.5) / x_span * W))
        py1 = int(round((y_span * 0.5 - wy2) / y_span * H))
        py2 = int(round((y_span * 0.5 - wy1) / y_span * H))
        return max(0, px1), max(0, py1), min(W, px2), min(H, py2)

    def fill_rect(wx1: int, wy1: int, wx2: int, wy2: int, col: Tuple[int, int, int]) -> None:
        px1, py1, px2, py2 = world_rect_to_px(wx1, wy1, wx2, wy2)
        for py in range(py1, py2):
            row = rgb_buf[py]
            for px in range(px1, px2):
                row[px] = col

    for x1, y1, x2, y2, col in mb.radar_floors:
        fill_rect(x1, y1, x2, y2, col)
    for x1, y1, x2, y2 in mb.radar_water:
        fill_rect(x1, y1, x2, y2, (36, 158, 224))
    for x1, y1, x2, y2, col in mb.radar_props:
        fill_rect(x1, y1, x2, y2, col)
    for x1, y1, x2, y2, col in mb.radar_walls:
        fill_rect(x1, y1, x2, y2, col)

    # Stamp clean bright Bombsite 'A' and 'B' markers on the radar
    for letter, wx, wy in (("A", 1280, -704), ("B", -1280, 448)):
        px, py, _, _ = world_rect_to_px(wx, wy, wx + 1, wy + 1)
        rows = BITMAP_FONT_5X7[letter]
        for ry, rstr in enumerate(rows):
            for rx, bit in enumerate(rstr):
                if bit == "1":
                    for sy in range(3):
                        for sx in range(3):
                            yy = py - 10 + ry * 3 + sy
                            xx = px - 7 + rx * 3 + sx
                            if 0 <= yy < H and 0 <= xx < W:
                                rgb_buf[yy][xx] = (255, 228, 56)

    os.makedirs(os.path.dirname(tga_path), exist_ok=True)
    # 1) Write uncompressed 24-bit TGA (bottom-to-top rows, BGR byte order)
    tga_hdr = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, W, H, 24, 0)
    tga_pixels = bytearray(W * H * 3)
    pos = 0
    for py in range(H - 1, -1, -1):
        row = rgb_buf[py]
        for px in range(W):
            r, g, b = row[px]
            tga_pixels[pos] = b
            tga_pixels[pos + 1] = g
            tga_pixels[pos + 2] = r
            pos += 3
    with open(tga_path, "wb") as tf:
        tf.write(tga_hdr)
        tf.write(tga_pixels)

    # 2) Write 8-bit indexed BMP (1024x768) for full GoldSrc software/OpenGL overview compatibility
    palette_map: Dict[Tuple[int, int, int], int] = {(0, 255, 0): 0}
    pal_list: List[Tuple[int, int, int]] = [(0, 255, 0)]
    idx_rows: List[bytes] = []
    for py in range(H - 1, -1, -1):
        b_row = bytearray(W)
        row = rgb_buf[py]
        for px in range(W):
            col = row[px]
            idx = palette_map.get(col)
            if idx is None:
                if len(pal_list) < 256:
                    idx = len(pal_list)
                    palette_map[col] = idx
                    pal_list.append(col)
                else:
                    idx = 1
            b_row[px] = idx
        idx_rows.append(bytes(b_row))
    pal_list.extend([(0, 0, 0)] * (256 - len(pal_list)))
    bmp_pal = b"".join(struct.pack("BBBB", b, g, r, 0) for (r, g, b) in pal_list)
    pixel_data = b"".join(idx_rows)
    file_size = 14 + 40 + 1024 + len(pixel_data)
    bmp_hdr = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, 14 + 40 + 1024)
    dib_hdr = struct.pack("<IiiHHIIiiII", 40, W, H, 1, 8, 0, len(pixel_data), 2835, 2835, 256, 256)
    with open(bmp_path, "wb") as bf:
        bf.write(bmp_hdr + dib_hdr + bmp_pal + pixel_data)

    # 3) Write overviews/de_raid.txt referencing de_raid.tga
    overview_txt = """// overview description file for de_raid.bsp

global 
{
\tZOOM\t1.45
\tORIGIN\t0\t0\t128
\tROTATED\t0
}

layer 
{
\tIMAGE\t"overviews/de_raid.tga"
\tHEIGHT\t-32
}
"""
    with open(txt_path, "w", encoding="ascii", newline="\r\n") as of:
        of.write(overview_txt)


def write_briefing_and_res(briefing_path: str, res_path: str) -> None:
    os.makedirs(os.path.dirname(briefing_path), exist_ok=True)
    briefing = """Raid - Hillside Mansion (Bomb Defusal)

Clean-room GoldSrc build for Counter-Strike: Condition Zero.
Credits: Layout inspired by the CoD4 custom map mp_bo2raid3 by Hugo,
which is a remake of Black Ops 2 Raid.
All GoldSrc brushwork and 8-bit WAD textures created from scratch.

Counter-Terrorists: Defend the Hillside Mansion's Poolside Gazebo
(Bombsite A) and Luxury Multi-Car Garage (Bombsite B) from demolition.
Defuse any planted C4 charges.

Terrorists: Breach through the Garage, Mansion Courtyard (Ring), or
Poolside Garden and detonate C4 at either Bombsite A or Bombsite B.

Other Notes: There are 2 bomb targets in this mission (Gazebo A, Garage B).
"""
    with open(briefing_path, "w", encoding="ascii", newline="\r\n") as bf:
        bf.write(briefing)

    res_content = """// de_raid.res - Custom resource manifest for VPN / LAN server downloads
de_raid.wad
maps/de_raid.bsp
maps/de_raid.nav
maps/de_raid.txt
maps/de_raid.res
overviews/de_raid.txt
overviews/de_raid.tga
overviews/de_raid.bmp
gfx/env/siennaup.tga
gfx/env/siennadn.tga
gfx/env/siennalf.tga
gfx/env/siennart.tga
gfx/env/siennaft.tga
gfx/env/siennabk.tga
"""
    with open(res_path, "w", encoding="ascii", newline="\r\n") as rf:
        rf.write(res_content)


def main() -> None:
    wad_out = os.path.join(ROOT, "czero", "de_raid.wad")
    map_out = os.path.join(ROOT, "maps", "de_raid.map")
    tga_out = os.path.join(ROOT, "czero", "overviews", "de_raid.tga")
    bmp_out = os.path.join(ROOT, "czero", "overviews", "de_raid.bmp")
    ov_txt_out = os.path.join(ROOT, "czero", "overviews", "de_raid.txt")
    brief_out = os.path.join(ROOT, "czero", "maps", "de_raid.txt")
    res_out = os.path.join(ROOT, "czero", "maps", "de_raid.res")

    tex_names = build_custom_wad(wad_out)
    print(f"[OK] Built {wad_out} ({len(tex_names)} original 8-bit textures): {', '.join(tex_names)}")

    wad_paths = [
        os.path.join(ROOT, "czero", "de_raid.wad"),
        os.path.join(ROOT, "tools", "vhlt", "tools", "zhlt.wad"),
        os.path.join(ROOT, "valve", "halflife.wad"),
        os.path.join(ROOT, "cstrike", "cstrike.wad"),
        os.path.join(ROOT, "cstrike", "cs_dust.wad"),
        os.path.join(ROOT, "cstrike", "cs_office.wad"),
        os.path.join(ROOT, "czero", "czde_sienna.wad"),
    ]
    mb = construct_de_raid(wad_paths, map_out)
    print(
        f"[OK] Built {map_out} ({len(mb.world_brushes)} world brushes, {len(mb.entities)} entities)"
    )

    write_radar_overview(mb, tga_out, bmp_out, ov_txt_out)
    print(f"[OK] Built radar overviews: {tga_out}, {bmp_out}, {ov_txt_out}")

    write_briefing_and_res(brief_out, res_out)
    print(f"[OK] Built briefing & resource manifest: {brief_out}, {res_out}")


if __name__ == "__main__":
    main()

