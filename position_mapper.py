"""
position_mapper.py — Convert player position strings using docs/position_map.json.
"""

import json
from pathlib import Path

_MAP_PATH = Path(__file__).parent / "docs" / "position_map.json"

_POSITION_FIELDS = ("Position", "Second Position")

DEFAULT_PLATFORM = "B11"


def load_map(path: str = None, platform: str = DEFAULT_PLATFORM) -> dict:
    """Load position map for a given platform from the JSON file."""
    with open(path or _MAP_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if platform not in data:
        available = list(data.keys())
        raise KeyError(f"Platform '{platform}' not found. Available: {available}")
    return data[platform]


def list_platforms(path: str = None) -> list:
    """Return all platform names defined in the map file."""
    with open(path or _MAP_PATH, encoding="utf-8") as f:
        return list(json.load(f).keys())


def convert_position(position: str, position_map: dict) -> str:
    """Convert a single position string. Returns original value if not found in map."""
    if not position:
        return position
    return position_map.get(position, position)


def convert_fields(data: dict, position_map: dict = None, platform: str = DEFAULT_PLATFORM) -> dict:
    """
    Return a copy of data with Position and Second Position converted.
    Loads the default platform map if position_map is not provided.
    """
    if position_map is None:
        position_map = load_map(platform=platform)
    result = dict(data)
    for field in _POSITION_FIELDS:
        if result.get(field):
            result[field] = convert_position(result[field], position_map)
    return result
