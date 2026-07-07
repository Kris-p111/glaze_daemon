from __future__ import annotations

import colorsys
import io
import math
from collections import Counter
from typing import Any

from PIL import Image, ImageStat

_RESAMPLE_FILTER = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
_QUANTIZE_METHOD = Image.Quantize.MEDIANCUT if hasattr(Image, "Quantize") else Image.MEDIANCUT


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        normalized = item.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_items.append(normalized)
    return unique_items


def _rgb_to_luminance(pixel: tuple[int, int, int]) -> float:
    r, g, b = pixel
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _pivot_rgb(value: float) -> float:
    value = value / 255
    if value > 0.04045:
        return ((value + 0.055) / 1.055) ** 2.4
    return value / 12.92


def _pivot_xyz(value: float) -> float:
    if value > 0.008856:
        return value ** (1 / 3)
    return (7.787 * value) + (16 / 116)


def _rgb_to_lab(r: float, g: float, b: float) -> list[float]:
    r_linear = _pivot_rgb(r)
    g_linear = _pivot_rgb(g)
    b_linear = _pivot_rgb(b)

    x = (r_linear * 0.4124 + g_linear * 0.3576 + b_linear * 0.1805) / 0.95047
    y = (r_linear * 0.2126 + g_linear * 0.7152 + b_linear * 0.0722) / 1.0
    z = (r_linear * 0.0193 + g_linear * 0.1192 + b_linear * 0.9505) / 1.08883

    fx = _pivot_xyz(x)
    fy = _pivot_xyz(y)
    fz = _pivot_xyz(z)

    return [
        round((116 * fy) - 16, 3),
        round(500 * (fx - fy), 3),
        round(200 * (fy - fz), 3),
    ]


def _color_family(r: float, g: float, b: float) -> str:
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    hue = h * 360

    if v < 0.16:
        return "black"
    if s < 0.09 and v > 0.84:
        return "white"
    if s < 0.15:
        if r > b + 8 and g > b + 2:
            return "cream"
        return "gray"
    if 18 <= hue <= 55 and v < 0.72:
        return "brown"
    if 35 <= hue <= 68 and v > 0.72 and s < 0.45:
        return "cream"
    if hue < 15 or hue >= 345:
        return "red"
    if hue < 35:
        return "orange"
    if hue < 68:
        return "yellow"
    if hue < 165:
        return "green"
    if hue < 195:
        return "cyan"
    if hue < 255:
        return "blue"
    if hue < 292:
        return "purple"
    if hue < 345:
        return "pink"
    return "unknown"


def _tone(mean_luminance: float) -> str:
    if mean_luminance < 55:
        return "very dark"
    if mean_luminance < 95:
        return "dark"
    if mean_luminance > 220:
        return "very light"
    if mean_luminance > 178:
        return "light"
    return "mid tone"


def _temperature(r: float, g: float, b: float, family: str) -> str:
    if family in {"red", "orange", "yellow", "brown", "cream"} or r - b > 14:
        return "warm"
    if family in {"blue", "cyan", "green", "purple"} or b - r > 10:
        return "cool"
    return "neutral"


def _edge_density(image: Image.Image) -> float:
    small = image.resize((48, 48))
    pixels = small.load()
    width, height = small.size
    comparisons = 0
    strong_edges = 0

    for y in range(height - 1):
        for x in range(width - 1):
            here = _rgb_to_luminance(pixels[x, y])
            right = _rgb_to_luminance(pixels[x + 1, y])
            down = _rgb_to_luminance(pixels[x, y + 1])
            comparisons += 2
            if abs(here - right) > 30:
                strong_edges += 1
            if abs(here - down) > 30:
                strong_edges += 1

    return strong_edges / comparisons if comparisons else 0


def _accent_colors(pixels: list[tuple[int, int, int]], dominant_family: str) -> list[str]:
    families: Counter[str] = Counter()
    total = 0

    for r, g, b in pixels:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s < 0.28 or v < 0.18:
            continue
        family = _color_family(r, g, b)
        if family in {"unknown", dominant_family}:
            continue
        families[family] += 1
        total += 1

    if total == 0:
        return []

    accents: list[str] = []
    for family, count in families.most_common(3):
        if count / total >= 0.08:
            accents.append(f"{family} accent")
    return accents


def _inner_region(image: Image.Image, margin_ratio: float = 0.08) -> Image.Image:
    width, height = image.size
    if width <= 2 or height <= 2:
        return image.copy()

    left = int(width * margin_ratio)
    top = int(height * margin_ratio)
    right = max(left + 1, int(width * (1 - margin_ratio)))
    bottom = max(top + 1, int(height * (1 - margin_ratio)))
    return image.crop((left, top, right, bottom))


def _profile_accent_colors(color_profile: dict[str, float], primary_color: str) -> list[str]:
    accents: list[str] = []
    for family, percent in sorted(color_profile.items(), key=lambda item: item[1], reverse=True):
        if family in {"unknown", primary_color}:
            continue
        if percent >= 0.08:
            accents.append(f"{family} accent")
        if len(accents) >= 3:
            break
    return accents


def _dominant_color_metadata(image: Image.Image) -> dict[str, Any]:
    color_region = _inner_region(image)
    color_region.thumbnail((128, 128), _RESAMPLE_FILTER)
    width, height = color_region.size
    total_pixels = width * height
    if total_pixels == 0:
        return {"primaryColor": "", "colorProfile": {}, "dominantColors": []}

    pixels = list(color_region.getdata())
    family_counts: Counter[str] = Counter(_color_family(r, g, b) for r, g, b in pixels)
    primary_color = family_counts.most_common(1)[0][0] if family_counts else ""
    color_profile = {
        family: round(count / total_pixels, 4)
        for family, count in sorted(family_counts.items(), key=lambda item: item[1], reverse=True)
    }

    try:
        quantized = color_region.quantize(colors=5, method=_QUANTIZE_METHOD)
    except Exception:
        quantized = color_region.convert("P", palette=Image.ADAPTIVE, colors=5)

    palette = quantized.getpalette() or []
    color_counts = quantized.getcolors(total_pixels) or []
    dominant_colors: list[dict[str, Any]] = []

    for count, palette_index in sorted(color_counts, reverse=True):
        offset = palette_index * 3
        rgb = palette[offset:offset + 3]
        if len(rgb) != 3:
            continue

        percent = count / total_pixels
        if percent < 0.015:
            continue

        r, g, b = [int(value) for value in rgb]
        dominant_colors.append({
            "rgb": [r, g, b],
            "lab": _rgb_to_lab(r, g, b),
            "percent": round(percent, 4),
            "family": _color_family(r, g, b),
        })

    if not dominant_colors:
        mean_r, mean_g, mean_b = ImageStat.Stat(color_region).mean[:3]
        rgb = [round(mean_r), round(mean_g), round(mean_b)]
        dominant_colors.append({
            "rgb": rgb,
            "lab": _rgb_to_lab(*rgb),
            "percent": 1.0,
            "family": _color_family(*rgb),
        })

    return {
        "primaryColor": primary_color,
        "colorProfile": color_profile,
        "dominantColors": dominant_colors,
    }


def analyze_tile_image(image_blob: bytes | None, annotation: dict[str, Any] | None = None) -> dict[str, Any]:
    if not image_blob:
        return {
            "tags": [],
            "keywords": "",
            "primaryColor": "",
            "colorProfile": {},
            "dominantColors": [],
        }

    annotation = annotation or {}

    with Image.open(io.BytesIO(image_blob)) as opened:
        image = opened.convert("RGB")

    image.thumbnail((96, 96))
    width, height = image.size
    if width == 0 or height == 0:
        return {
            "tags": [],
            "keywords": "",
            "primaryColor": "",
            "colorProfile": {},
            "dominantColors": [],
        }

    # Keep legacy mean-color metrics centered so borders/shadows matter less.
    left = int(width * 0.2)
    top = int(height * 0.2)
    right = max(left + 1, int(width * 0.8))
    bottom = max(top + 1, int(height * 0.8))
    center = image.crop((left, top, right, bottom))

    mean_r, mean_g, mean_b = ImageStat.Stat(center).mean[:3]
    mean_luminance = _rgb_to_luminance((int(mean_r), int(mean_g), int(mean_b)))
    dominant_metadata = _dominant_color_metadata(image)
    family = dominant_metadata.get("primaryColor") or _color_family(mean_r, mean_g, mean_b)
    temperature = _temperature(mean_r, mean_g, mean_b, family)
    tone = _tone(mean_luminance)

    pixels = list(image.getdata())
    luminances = [_rgb_to_luminance(pixel) for pixel in pixels]
    avg_luminance = sum(luminances) / len(luminances)
    variance = sum((lum - avg_luminance) ** 2 for lum in luminances) / len(luminances)
    contrast = math.sqrt(variance) / 255

    saturations = [
        colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[1]
        for r, g, b in pixels
    ]
    avg_saturation = sum(saturations) / len(saturations)
    highlight_ratio = sum(1 for lum in luminances if lum > 232) / len(luminances)
    shadow_ratio = sum(1 for lum in luminances if lum < 45) / len(luminances)
    edge_density = _edge_density(image)

    tags = [
        family,
        tone,
        temperature,
        "vivid" if avg_saturation > 0.38 else "muted",
    ]

    if contrast > 0.19:
        tags.append("high contrast")
    elif contrast < 0.075:
        tags.append("low contrast")
    else:
        tags.append("medium contrast")

    if highlight_ratio > 0.025:
        tags.extend(["glossy", "highlighted"])
    elif contrast < 0.11 and edge_density < 0.08:
        tags.append("matte")

    if edge_density > 0.16 and contrast > 0.10:
        tags.extend(["speckled", "rough"])
    elif edge_density > 0.10 or contrast > 0.16:
        tags.append("variegated")
    else:
        tags.append("smooth")

    if shadow_ratio > 0.08:
        tags.append("deep shadows")

    tags.extend(_profile_accent_colors(dominant_metadata.get("colorProfile", {}), family))
    tags.extend(_accent_colors(pixels, family))

    # Include existing known fields as searchable keywords when users filled them in.
    for key in ("GlazeType", "SurfaceCondition", "FiringType", "SoilType"):
        value = str(annotation.get(key, "")).strip().lower()
        if value:
            tags.append(value)

    tags = _unique(tags)
    keyword_tags = tags[:10]

    return {
        "tags": tags,
        "keywords": " ".join(keyword_tags + ["ceramic", "tile"]),
        "primaryColor": dominant_metadata.get("primaryColor", ""),
        "colorProfile": dominant_metadata.get("colorProfile", {}),
        "dominantColors": dominant_metadata.get("dominantColors", []),
        "metrics": {
            "meanRgb": [round(mean_r), round(mean_g), round(mean_b)],
            "contrast": round(_clamp(contrast), 4),
            "saturation": round(_clamp(avg_saturation), 4),
            "edgeDensity": round(_clamp(edge_density), 4),
            "highlightRatio": round(_clamp(highlight_ratio), 4),
        },
    }
