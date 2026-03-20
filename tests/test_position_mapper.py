"""Tests for position_mapper.py"""

import pytest

from position_mapper import convert_fields, convert_position, list_platforms, load_map

SAMPLE_MAP = {
    "Goalkeeper": "PT",
    "Sweeper": "DFC",
    "Centre Back": "DFD",
    "Striker": "DC",
    "Attacking Midfielder": "MP",
    "Right Winger": "ED",
}


# ── convert_position ──────────────────────────────────────────────────────────

def test_known_position_is_converted():
    assert convert_position("Goalkeeper", SAMPLE_MAP) == "PT"


def test_known_position_striker():
    assert convert_position("Striker", SAMPLE_MAP) == "DC"


def test_unknown_position_returns_original():
    assert convert_position("Unknown Position", SAMPLE_MAP) == "Unknown Position"


def test_empty_string_returns_empty():
    assert convert_position("", SAMPLE_MAP) == ""


def test_none_returns_none():
    assert convert_position(None, SAMPLE_MAP) is None


def test_case_sensitive_no_match():
    assert convert_position("goalkeeper", SAMPLE_MAP) == "goalkeeper"


# ── convert_fields ────────────────────────────────────────────────────────────

def test_converts_position_and_second_position():
    data = {"Name": "Test", "Position": "Goalkeeper", "Second Position": "Striker"}
    result = convert_fields(data, SAMPLE_MAP)
    assert result["Position"] == "PT"
    assert result["Second Position"] == "DC"


def test_unknown_field_value_unchanged():
    data = {"Position": "Unknown", "Second Position": None}
    result = convert_fields(data, SAMPLE_MAP)
    assert result["Position"] == "Unknown"
    assert result["Second Position"] is None


def test_missing_position_field_ignored():
    data = {"Name": "No Position Player"}
    result = convert_fields(data, SAMPLE_MAP)
    assert "Position" not in result


def test_does_not_mutate_input_dict():
    data = {"Position": "Goalkeeper", "Second Position": "Striker"}
    original = dict(data)
    convert_fields(data, SAMPLE_MAP)
    assert data == original


def test_other_fields_are_preserved():
    data = {
        "Name": "Player A",
        "Club": "Some Club",
        "Position": "Goalkeeper",
        "Second Position": "Striker",
    }
    result = convert_fields(data, SAMPLE_MAP)
    assert result["Name"] == "Player A"
    assert result["Club"] == "Some Club"


def test_uses_default_map_when_none_provided():
    data = {"Position": "Goalkeeper", "Second Position": "Striker"}
    result = convert_fields(data)
    assert result["Position"] == "PT"
    assert result["Second Position"] == "DC"


# ── load_map ──────────────────────────────────────────────────────────────────

def test_load_map_returns_dict():
    mapping = load_map()
    assert isinstance(mapping, dict)


def test_load_map_has_all_16_positions():
    mapping = load_map()
    assert len(mapping) == 16


def test_load_map_goalkeeper_maps_to_pt():
    mapping = load_map()
    assert mapping["Goalkeeper"] == "PT"


def test_load_map_striker_maps_to_dc():
    mapping = load_map()
    assert mapping["Striker"] == "DC"


def test_load_map_all_expected_sources_present():
    expected_sources = [
        "Goalkeeper", "Sweeper", "Centre Back", "Right Back", "Left Back",
        "Right Wing Back", "Left Wing Back", "Holding Midfielder",
        "Centre Midfielder", "Right Midfielder", "Left Midfielder",
        "Attacking Midfielder", "Right Winger", "Left Winger",
        "Second Striker", "Striker",
    ]
    mapping = load_map()
    for src in expected_sources:
        assert src in mapping, f"Missing source: {src}"


def test_load_map_all_destinations_are_our_codes():
    expected_destinations = {
        "PT", "DFC", "DFD", "LD", "LI", "CAD", "CAI",
        "MCD", "MC", "MD", "MI", "MP", "ED", "EI", "SD", "DC",
    }
    mapping = load_map()
    assert set(mapping.values()) == expected_destinations


def test_load_map_unknown_platform_raises():
    with pytest.raises(KeyError, match="Platform 'Unknown'"):
        load_map(platform="Unknown")


def test_list_platforms_includes_b11():
    platforms = list_platforms()
    assert "B11" in platforms


def test_list_platforms_returns_list():
    assert isinstance(list_platforms(), list)
