from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import cadquery as cq


FONT_PATH_CANDIDATES = {
    "DejaVu Sans": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ],
    "Liberation Sans": [
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ],
    "Lato": [
        "/usr/share/fonts/truetype/lato/Lato-Regular.ttf",
        "/usr/share/fonts/lato/Lato-Regular.ttf",
    ],
}


def _resolve_font_path(font: str) -> str | None:
    """Return an installed TTF path for reliable CadQuery text on Linux.

    CadQuery/OCP font-name discovery can return a null FontName on headless
    Streamlit Linux hosts even when the font is installed. Passing fontPath
    bypasses that discovery layer and is much more reliable.
    """
    for candidate in FONT_PATH_CANDIDATES.get(font, []):
        if Path(candidate).is_file():
            return candidate

    # Always fall back to DejaVu Sans if the selected family is unavailable.
    for candidate in FONT_PATH_CANDIDATES["DejaVu Sans"]:
        if Path(candidate).is_file():
            return candidate
    return None


def _cq_text(text: str, size: float, depth: float, font: str) -> cq.Workplane:
    font_path = _resolve_font_path(font)
    kwargs = dict(halign="center", valign="center", combine=False)
    if font_path:
        return cq.Workplane("XY").text(text, size, depth, fontPath=font_path, **kwargs)
    # Last-resort fallback for non-Linux/local installs.
    return cq.Workplane("XY").text(text, size, depth, font=font or "Arial", **kwargs)


@dataclass
class OrganizerConfig:
    name: str = "Miss Parker"
    title: str = "Teacher"
    profession: str = "Teacher"
    width: float = 220.0
    depth: float = 100.0
    height: float = 78.0
    wall: float = 2.6
    floor: float = 3.0
    columns: int = 4
    rows: int = 1
    front_style: str = "Pencil"
    icon: str = "Apple"
    plate_height: float = 55.0
    plate_thickness: float = 2.2
    text_raise: float = 1.2
    corner_radius: float = 7.0
    font_name: str = "DejaVu Sans"
    show_title: bool = True
    add_second_icon: bool = True
    name_shape_border: float = 3.2


PROFESSION_PRESETS = {
    "Teacher": {"front_style": "Pencil", "icon": "Apple", "title": "Teacher"},
    "Registered Nurse": {"front_style": "Capsule", "icon": "Medical Cross", "title": "Registered Nurse"},
    "Early Childhood Educator": {"front_style": "Cloud", "icon": "Flower", "title": "Early Childhood Educator"},
    "Occupational Therapist": {"front_style": "Arch", "icon": "Heart", "title": "Occupational Therapist"},
    "Physiotherapist": {"front_style": "Arch", "icon": "Heart", "title": "Physiotherapist"},
    "Doctor": {"front_style": "Capsule", "icon": "Medical Cross", "title": "Doctor"},
    "Dentist": {"front_style": "Capsule", "icon": "Tooth", "title": "Dentist"},
    "Veterinarian": {"front_style": "Capsule", "icon": "Paw", "title": "Veterinarian"},
    "Speech Pathologist": {"front_style": "Cloud", "icon": "Speech Bubble", "title": "Speech Pathologist"},
    "Reception / Admin": {"front_style": "Rounded", "icon": "Star", "title": "Reception"},
    "Hairdresser": {"front_style": "Rounded", "icon": "Scissors", "title": "Hairdresser"},
    "Beauty Therapist": {"front_style": "Arch", "icon": "Star", "title": "Beauty Therapist"},
}


def _rounded_box_xy(width: float, height: float, thickness: float, radius: float) -> cq.Workplane:
    radius = max(0.1, min(radius, width / 4, height / 4))
    solid = cq.Workplane("XY").box(width, height, thickness)
    try:
        return solid.edges("|Z").fillet(radius)
    except Exception:
        return solid


def _pencil_plate(width: float, height: float, thickness: float) -> cq.Workplane:
    body_w = width - height * 0.7
    body = _rounded_box_xy(body_w, height, thickness, min(5.0, height * 0.12)).translate((-height * 0.18, 0, 0))
    half_h = height / 2
    x0 = body_w / 2 - height * 0.18
    tip = cq.Workplane("XY").polyline([
        (x0, -half_h),
        (width / 2, 0),
        (x0, half_h),
    ]).close().extrude(thickness / 2, both=True)
    eraser = _rounded_box_xy(height * 0.26, height, thickness, min(4.0, height * 0.1)).translate((-width / 2 + height * 0.13, 0, 0))
    return body.union(tip).union(eraser)


def _cloud_plate(width: float, height: float, thickness: float) -> cq.Workplane:
    base = _rounded_box_xy(width * 0.88, height * 0.62, thickness, height * 0.16).translate((0, -height * 0.08, 0))
    bumps = cq.Workplane("XY")
    specs = [
        (-width * 0.32, height * 0.13, height * 0.22),
        (-width * 0.12, height * 0.23, height * 0.28),
        (width * 0.12, height * 0.24, height * 0.30),
        (width * 0.33, height * 0.13, height * 0.22),
    ]
    result = base
    for x, y, r in specs:
        result = result.union(cq.Workplane("XY").center(x, y).circle(r).extrude(thickness / 2, both=True))
    return result


def _arch_plate(width: float, height: float, thickness: float) -> cq.Workplane:
    lower = _rounded_box_xy(width, height * 0.72, thickness, height * 0.14).translate((0, -height * 0.13, 0))
    top = cq.Workplane("XY").ellipse(width / 2, height * 0.36).extrude(thickness / 2, both=True).translate((0, height * 0.14, 0))
    return lower.union(top)


def _capsule_plate(width: float, height: float, thickness: float) -> cq.Workplane:
    return _rounded_box_xy(width, height, thickness, height / 2.05)


def make_plate_base(style: str, width: float, height: float, thickness: float, radius: float) -> cq.Workplane:
    style = style.lower().strip()
    if style == "pencil":
        return _pencil_plate(width, height, thickness)
    if style == "cloud":
        return _cloud_plate(width, height, thickness)
    if style == "arch":
        return _arch_plate(width, height, thickness)
    if style == "capsule":
        return _capsule_plate(width, height, thickness)
    return _rounded_box_xy(width, height, thickness, radius)


def _heart_icon(size: float, depth: float) -> cq.Workplane:
    r = size * 0.22
    left = cq.Workplane("XY").center(-r, r * 0.55).circle(r).extrude(depth)
    right = cq.Workplane("XY").center(r, r * 0.55).circle(r).extrude(depth)
    tri = cq.Workplane("XY").polyline([(-size * 0.42, r * 0.55), (size * 0.42, r * 0.55), (0, -size * 0.47)]).close().extrude(depth)
    return left.union(right).union(tri)


def _medical_cross(size: float, depth: float) -> cq.Workplane:
    arm = size * 0.30
    a = cq.Workplane("XY").box(arm, size, depth).translate((0, 0, depth / 2))
    b = cq.Workplane("XY").box(size, arm, depth).translate((0, 0, depth / 2))
    return a.union(b)


def _flower_icon(size: float, depth: float) -> cq.Workplane:
    result = cq.Workplane("XY").circle(size * 0.17).extrude(depth)
    for dx, dy in [(0, 0.30), (0.30, 0), (0, -0.30), (-0.30, 0)]:
        result = result.union(cq.Workplane("XY").center(dx * size, dy * size).circle(size * 0.18).extrude(depth))
    return result


def _apple_icon(size: float, depth: float) -> cq.Workplane:
    body = cq.Workplane("XY").ellipse(size * 0.34, size * 0.30).extrude(depth).translate((0, -size * 0.03, 0))
    leaf = cq.Workplane("XY").ellipse(size * 0.16, size * 0.08).extrude(depth).rotate((0,0,0),(0,0,1),28).translate((size * 0.15, size * 0.28, 0))
    stem = cq.Workplane("XY").box(size * 0.08, size * 0.22, depth).translate((0, size * 0.30, depth / 2))
    return body.union(leaf).union(stem)


def _paw_icon(size: float, depth: float) -> cq.Workplane:
    result = cq.Workplane("XY").ellipse(size * 0.28, size * 0.23).extrude(depth).translate((0, -size * 0.12, 0))
    toe_specs = [(-0.27, 0.20), (-0.09, 0.31), (0.11, 0.31), (0.29, 0.18)]
    for dx, dy in toe_specs:
        result = result.union(cq.Workplane("XY").center(dx * size, dy * size).circle(size * 0.11).extrude(depth))
    return result


def _tooth_icon(size: float, depth: float) -> cq.Workplane:
    pts = [
        (-0.34, 0.30), (-0.18, 0.42), (0, 0.34), (0.18, 0.42), (0.34, 0.30),
        (0.30, 0.03), (0.20, -0.33), (0.07, -0.49), (0, -0.20), (-0.07, -0.49),
        (-0.20, -0.33), (-0.30, 0.03)
    ]
    pts = [(x * size, y * size) for x, y in pts]
    return cq.Workplane("XY").polyline(pts).close().extrude(depth)


def _star_icon(size: float, depth: float) -> cq.Workplane:
    import math
    pts = []
    for i in range(10):
        a = math.radians(90 + i * 36)
        r = size * (0.42 if i % 2 == 0 else 0.18)
        pts.append((r * math.cos(a), r * math.sin(a)))
    return cq.Workplane("XY").polyline(pts).close().extrude(depth)


def _speech_bubble(size: float, depth: float) -> cq.Workplane:
    bubble = _rounded_box_xy(size * 0.78, size * 0.52, depth, size * 0.12)
    tail = cq.Workplane("XY").polyline([(-size * 0.14, -size * 0.22), (size * 0.03, -size * 0.45), (size * 0.12, -size * 0.22)]).close().extrude(depth / 2, both=True)
    return bubble.union(tail)


def _scissors_icon(size: float, depth: float) -> cq.Workplane:
    r = size * 0.13
    left = cq.Workplane("XY").center(-size * 0.16, -size * 0.15).circle(r).extrude(depth)
    right = cq.Workplane("XY").center(size * 0.16, -size * 0.15).circle(r).extrude(depth)
    blade1 = cq.Workplane("XY").polyline([(-size*0.05,-size*0.04),(size*0.40,size*0.35),(size*0.10,size*0.05)]).close().extrude(depth)
    blade2 = cq.Workplane("XY").polyline([(size*0.05,-size*0.04),(-size*0.40,size*0.35),(-size*0.10,size*0.05)]).close().extrude(depth)
    return left.union(right).union(blade1).union(blade2)


def make_icon(icon: str, size: float, depth: float) -> cq.Workplane:
    icon = icon.lower().strip()
    if icon == "heart": return _heart_icon(size, depth)
    if icon == "medical cross": return _medical_cross(size, depth)
    if icon == "flower": return _flower_icon(size, depth)
    if icon == "apple": return _apple_icon(size, depth)
    if icon == "paw": return _paw_icon(size, depth)
    if icon == "tooth": return _tooth_icon(size, depth)
    if icon == "speech bubble": return _speech_bubble(size, depth)
    if icon == "scissors": return _scissors_icon(size, depth)
    return _star_icon(size, depth)


def _fitted_text(text: str, max_width: float, max_height: float, depth: float, font: str) -> cq.Workplane:
    text = (text or "").strip()
    if not text:
        return cq.Workplane("XY")
    lo, hi = 3.0, max_height * 1.25
    best = None
    for _ in range(14):
        mid = (lo + hi) / 2
        try:
            candidate = _cq_text(text, mid, depth, font)
            bb = candidate.val().BoundingBox()
            if bb.xlen <= max_width and bb.ylen <= max_height:
                best = candidate
                lo = mid
            else:
                hi = mid
        except Exception:
            hi = mid
    if best is None:
        best = _cq_text(text, max(3.0, max_height * 0.45), depth, font)
    return best


def _make_name_shape_frontplate(cfg: OrganizerConfig, plate_w: float, plate_h: float) -> Tuple[cq.Workplane, cq.Workplane, cq.Workplane]:
    """Create a word-shaped front similar to a layered personalised name sign.

    The backing is a slightly larger version of the name, joined by a slim
    rounded bridge so the backing exports as a practical printable piece.
    The customer's name sits raised on top.  When a job title is enabled, a
    small rounded title strip overlaps the lower edge of the name backing.
    """
    border = max(1.5, min(6.0, cfg.name_shape_border))
    z0 = cfg.plate_thickness / 2

    # Give the name most of the available height. The larger duplicate is the
    # visible border/backing; the smaller duplicate becomes the colour layer.
    if cfg.show_title and cfg.title.strip():
        backing_h = plate_h * 0.60
        name_y = plate_h * 0.11
    else:
        backing_h = plate_h * 0.82
        name_y = 0.0

    backing_w = plate_w - 6.0
    name_backing = _fitted_text(
        cfg.name, backing_w, backing_h, cfg.plate_thickness, cfg.font_name
    ).translate((0, name_y, -cfg.plate_thickness / 2))

    raised_name = _fitted_text(
        cfg.name,
        max(30.0, backing_w - 2.0 * border),
        max(10.0, backing_h - 2.0 * border),
        cfg.text_raise,
        cfg.font_name,
    ).translate((0, name_y, z0))

    # A slim bridge joins separate letters/dots into one robust backing while
    # still leaving the overall silhouette dominated by the name itself.
    bb = name_backing.val().BoundingBox()
    bridge_h = max(7.0, min(16.0, bb.ylen * 0.40))
    bridge_w = min(plate_w - 4.0, bb.xlen + border * 2.0)
    bridge = _rounded_box_xy(bridge_w, bridge_h, cfg.plate_thickness, bridge_h / 2.2)
    bridge = bridge.translate((0, (bb.ymin + bb.ymax) / 2.0, 0))

    base = name_backing.union(bridge)
    text_parts = raised_name

    if cfg.show_title and cfg.title.strip():
        title_h = max(11.0, min(16.0, plate_h * 0.23))
        # Overlap the title strip slightly with the lower name backing so the
        # complete base is a single connected piece.
        title_y = bb.ymin - title_h / 2.0 + 1.6
        title_w = min(plate_w - 4.0, max(90.0, plate_w * 0.84))
        title_strip = _rounded_box_xy(title_w, title_h, cfg.plate_thickness, title_h / 2.05)
        title_strip = title_strip.translate((0, title_y, 0))
        base = base.union(title_strip)

        icon_size = min(title_h * 0.72, 12.5) if cfg.icon.lower() != "none" else 0.0
        side_margin = icon_size * 1.30 if icon_size else 0.0
        title_text = _fitted_text(
            cfg.title,
            max(35.0, title_w - 2.0 * side_margin - 12.0),
            title_h * 0.56,
            cfg.text_raise,
            cfg.font_name,
        ).translate((0, title_y, z0))
        text_parts = text_parts.union(title_text)

        if cfg.icon.lower() != "none":
            icon_x = title_w / 2.0 - icon_size * 0.82
            left_icon = make_icon(cfg.icon, icon_size, cfg.text_raise).translate((-icon_x, title_y, z0))
            text_parts = text_parts.union(left_icon)
            if cfg.add_second_icon:
                right_icon = make_icon(cfg.icon, icon_size, cfg.text_raise).translate((icon_x, title_y, z0))
                text_parts = text_parts.union(right_icon)
    elif cfg.icon.lower() != "none":
        icon_size = min(plate_h * 0.25, 15.0)
        icon_x = min(plate_w / 2.0 - icon_size, bb.xmax + icon_size * 0.55)
        left_icon = make_icon(cfg.icon, icon_size, cfg.text_raise).translate((-icon_x, 0, z0))
        text_parts = text_parts.union(left_icon)
        if cfg.add_second_icon:
            right_icon = make_icon(cfg.icon, icon_size, cfg.text_raise).translate((icon_x, 0, z0))
            text_parts = text_parts.union(right_icon)

    complete = base.union(text_parts)
    return base, text_parts, complete


def make_frontplate(cfg: OrganizerConfig) -> Tuple[cq.Workplane, cq.Workplane, cq.Workplane]:
    plate_w = max(80.0, cfg.width * 0.91)
    plate_h = min(cfg.plate_height, cfg.height * 0.82)

    if cfg.front_style.lower().strip() == "name shape":
        return _make_name_shape_frontplate(cfg, plate_w, plate_h)

    base = make_plate_base(cfg.front_style, plate_w, plate_h, cfg.plate_thickness, cfg.corner_radius)

    z0 = cfg.plate_thickness / 2
    icon_size = min(plate_h * 0.34, 19.0)
    side_margin = icon_size * 1.15 if cfg.icon.lower() != "none" else 0

    if cfg.show_title and cfg.title.strip():
        name_y = plate_h * 0.13
        title_y = -plate_h * 0.28
        name_h = plate_h * 0.42
        title_h = plate_h * 0.20
    else:
        name_y = 0
        title_y = 0
        name_h = plate_h * 0.56
        title_h = 0

    name_text = _fitted_text(cfg.name, plate_w - 18.0, name_h, cfg.text_raise, cfg.font_name).translate((0, name_y, z0))
    text_parts = name_text

    if cfg.show_title and cfg.title.strip():
        title_max_w = plate_w - 2 * side_margin - 18.0
        title_text = _fitted_text(cfg.title, title_max_w, title_h, cfg.text_raise, cfg.font_name).translate((0, title_y, z0))
        text_parts = text_parts.union(title_text)

    if cfg.icon.lower() != "none":
        icon_depth = cfg.text_raise
        icon_x = plate_w / 2 - icon_size * 0.75
        icon_y = title_y if cfg.show_title and cfg.title.strip() else 0
        left_icon = make_icon(cfg.icon, icon_size, icon_depth).translate((-icon_x, icon_y, z0))
        text_parts = text_parts.union(left_icon)
        if cfg.add_second_icon:
            right_icon = make_icon(cfg.icon, icon_size, icon_depth).translate((icon_x, icon_y, z0))
            text_parts = text_parts.union(right_icon)

    complete = base.union(text_parts)
    return base, text_parts, complete


def make_organizer_body(cfg: OrganizerConfig) -> cq.Workplane:
    w, d, h = cfg.width, cfg.depth, cfg.height
    wall = max(1.8, cfg.wall)
    floor = max(1.8, cfg.floor)
    cols = max(1, int(cfg.columns))
    rows = max(1, int(cfg.rows))

    body = cq.Workplane("XY").box(w, d, floor).translate((0, 0, floor / 2))

    # Outer walls
    front = cq.Workplane("XY").box(w, wall, h).translate((0, -d/2 + wall/2, h/2))
    back = cq.Workplane("XY").box(w, wall, h).translate((0, d/2 - wall/2, h/2))
    left = cq.Workplane("XY").box(wall, d - 2*wall, h).translate((-w/2 + wall/2, 0, h/2))
    right = cq.Workplane("XY").box(wall, d - 2*wall, h).translate((w/2 - wall/2, 0, h/2))
    body = body.union(front).union(back).union(left).union(right)

    inner_w = w - 2*wall
    inner_d = d - 2*wall

    if cols > 1:
        cell_w = inner_w / cols
        for i in range(1, cols):
            x = -inner_w/2 + i*cell_w
            divider = cq.Workplane("XY").box(wall, inner_d, h * 0.86).translate((x, 0, (h*0.86)/2))
            body = body.union(divider)

    if rows > 1:
        cell_d = inner_d / rows
        for i in range(1, rows):
            y = -inner_d/2 + i*cell_d
            divider = cq.Workplane("XY").box(inner_w, wall, h * 0.74).translate((0, y, (h*0.74)/2))
            body = body.union(divider)

    # Slight feet / anti-rocking pads
    foot_h = 1.2
    foot_r = 5.5
    for x in (-w/2 + 12, w/2 - 12):
        for y in (-d/2 + 12, d/2 - 12):
            foot = cq.Workplane("XY").center(x, y).circle(foot_r).extrude(foot_h)
            body = body.union(foot)

    return body


def make_assembled_preview(cfg: OrganizerConfig, body: cq.Workplane, frontplate: cq.Workplane) -> cq.Workplane:
    # Flat frontplate is in XY with Z thickness. Rotate so its face points
    # toward -Y, then position its lowest point a few millimetres above the
    # desk. This also keeps the irregular Name Shape style centred correctly.
    bb = frontplate.val().BoundingBox()
    plate_vertical = frontplate.rotate((0,0,0),(1,0,0),90)
    z_shift = 4.0 - bb.ymin
    plate_vertical = plate_vertical.translate((0, -cfg.depth/2 - cfg.plate_thickness/2 + 0.02, z_shift))
    return body.union(plate_vertical)


def build_models(cfg: OrganizerConfig) -> Dict[str, cq.Workplane]:
    body = make_organizer_body(cfg)
    plate_base, plate_text, plate_complete = make_frontplate(cfg)
    assembled = make_assembled_preview(cfg, body, plate_complete)
    return {
        "organizer_body": body,
        "nameplate_base": plate_base,
        "nameplate_text_icons": plate_text,
        "nameplate_complete": plate_complete,
        "assembled_preview": assembled,
    }


def export_models(models: Dict[str, cq.Workplane], out_dir: str | Path) -> Dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key, model in models.items():
        p = out / f"{key}.stl"
        cq.exporters.export(model, str(p), tolerance=0.08, angularTolerance=0.15)
        paths[key] = p
    return paths
