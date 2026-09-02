#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) Open Astro Technologies, USA.
# Modified by Sundar Sundaresan, USA. carnaticmusicguru2015@comcast.net
# Downloaded from https://github.com/naturalstupid/PyJHora

# This file is part of the "PyJHora" Python library
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
    Release History:
    V4.8.6 - Moved hardcoded settings from this file to factory/user settings
"""
from __future__ import annotations

import copy
import json
import os
from typing import Any, Dict, List, Optional

from jhora import const


# ============================================================
# FILE PATHS
# ============================================================
CONFIG_DIR = const._DATA_DIR
FACTORY_SETTINGS_FILE = const.FACTORY_SETTINGS_FILE
USER_SETTINGS_FILE = const.USER_SETTINGS_FILE


# ============================================================
# STATE
# ============================================================
_FACTORY: Dict[str, Dict[str, Any]] = {}
_USER: Dict[str, Any] = {}
_SETTINGS_LOADED = False


# ============================================================
# HELPERS
# ============================================================
def _ensure_config_dir() -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)


def _deepcopy(value: Any) -> Any:
    return copy.deepcopy(value)


def _load_json(path: str, default: Any) -> Any:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return _deepcopy(default)


def _save_json(path: str, data: Any) -> None:
    _ensure_config_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "on", "y", "t"):
        return True
    if text in ("0", "false", "no", "off", "n", "f"):
        return False
    return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _coerce_value(meta: Dict[str, Any], value: Any) -> Any:
    """
    Coerce user value to the type declared in factory_settings.json
    """
    type_ = str(meta.get("type", "string")).strip().lower()
    default = meta.get("default")
    nullable = bool(meta.get("nullable", False))

    if value is None and nullable:
        return None

    if type_ == "bool":
        return _to_bool(value, default=bool(default))
    if type_ == "int":
        return _to_int(value, default=int(default if default is not None else 0))
    if type_ == "float":
        return _to_float(value, default=float(default if default is not None else 0.0))
    if type_ == "string":
        if value is None:
            return "" if not nullable else None
        return str(value)
    if type_ == "choice":
        return value
    if type_ == "int_list":
        if isinstance(value, list):
            result = []
            for item in value:
                try:
                    result.append(int(item))
                except Exception:
                    pass
            return result
        return list(default or [])
    return value


def _validate_choice(meta: Dict[str, Any], value: Any) -> Any:
    if str(meta.get("type", "")).lower() != "choice":
        return value

    choices = meta.get("choices", [])
    valid_values = [choice[0] if isinstance(choice, (list, tuple)) and len(choice) == 2 else choice for choice in choices]

    if value in valid_values:
        return value

    # fallback to default if invalid
    return meta.get("default")


def _normalize_value(meta: Dict[str, Any], value: Any) -> Any:
    value = _coerce_value(meta, value)
    value = _validate_choice(meta, value)
    return value


# ============================================================
# LOAD / SAVE
# ============================================================
def load_all_settings(*, create_if_missing: bool = True, apply: bool = True) -> Dict[str, Dict[str, Any]]:
    """
    Load factory metadata and user values.
    Factory file is authoritative for schema/defaults/UI metadata.
    User file contains only actual current values.
    """
    global _FACTORY, _USER

    _ensure_config_dir()

    _FACTORY = _load_json(FACTORY_SETTINGS_FILE, default={})
    _USER = _load_json(USER_SETTINGS_FILE, default={})

    # normalize user values against factory schema
    clean_user: Dict[str, Any] = {}
    for key, meta in _FACTORY.items():
        if key in _USER:
            clean_user[key] = _normalize_value(meta, _USER[key])
    _USER = clean_user

    if create_if_missing:
        if not os.path.exists(USER_SETTINGS_FILE):
            save_all_settings()

    if apply:
        apply_all_settings()

    return get_all_setting_defs()


def save_all_settings() -> None:
    _save_json(USER_SETTINGS_FILE, _USER)

def save_settings() -> None:
    save_all_settings()


# ============================================================
# ACCESSORS
# ============================================================
def has_setting(key: str) -> bool:
    return key in _FACTORY


def get_setting_def(key: str) -> Optional[Dict[str, Any]]:
    if key not in _FACTORY:
        return None
    meta = _deepcopy(_FACTORY[key])
    meta["key"] = key
    meta["value"] = get_value(key)
    return meta


def get_all_setting_defs() -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for key in _FACTORY:
        meta = _deepcopy(_FACTORY[key])
        meta["key"] = key
        meta["value"] = get_value(key)
        result[key] = meta
    return result


def get_value(key: str, fallback: Any = None) -> Any:
    meta = _FACTORY.get(key)
    if not meta:
        return fallback
    if key in _USER:
        return _deepcopy(_USER[key])
    return _deepcopy(meta.get("default", fallback))


def snapshot_values() -> Dict[str, Any]:
    return {key: get_value(key) for key in _FACTORY.keys()}


# ============================================================
# MUTATORS
# ============================================================
def set_value(key: str, value: Any, *, apply: bool = True, save: bool = False) -> Any:
    meta = _FACTORY.get(key)
    if not meta:
        raise KeyError(f"Unknown setting: {key}")

    normalized = _normalize_value(meta, value)
    _USER[key] = normalized

    if apply:
        apply_setting(key)
    if save:
        save_all_settings()

    return normalized


def set_values(values_by_key: Dict[str, Any], *, apply: bool = True, save: bool = False) -> None:
    for key, value in values_by_key.items():
        if key in _FACTORY:
            _USER[key] = _normalize_value(_FACTORY[key], value)

    if apply:
        apply_all_settings()
    if save:
        save_all_settings()


def reset_setting(key: str, *, apply: bool = True, save: bool = False) -> Any:
    if key not in _FACTORY:
        raise KeyError(f"Unknown setting: {key}")

    if key in _USER:
        del _USER[key]

    value = get_value(key)

    if apply:
        apply_setting(key)
    if save:
        save_all_settings()

    return value


def reset_all(*, apply: bool = True, save: bool = False) -> Dict[str, Any]:
    _USER.clear()

    if apply:
        apply_all_settings()
    if save:
        save_all_settings()

    return snapshot_values()


def reset_to_defaults(*, apply: bool = True, save: bool = False) -> Dict[str, Any]:
    return reset_all(apply=apply, save=save)


# ============================================================
# APPLY TO CONST
# ============================================================
def apply_setting(key: str) -> None:
    meta = _FACTORY.get(key)
    if not meta:
        return
    set_planet_list_keys = ["use_true_nodes_for_rahu_ketu", "include_uranus_to_pluto"]
    set_planet_flag_keys = ["planet_position_reference_frame","planet_position_type","use_aberration_of_light",
                            "use_gravitational_deflection","use_nutation","rise_set_use_refraction",
                            "rise_set_use_disc_center_for_rising","rise_set_hindu_rising"]
    value = get_value(key)

    setter_name = meta.get("setter")
    if setter_name:
        setter = getattr(const, setter_name, None)
        if callable(setter):
            setter(value)
        else:
            return
    else:
        const_name = meta.get("const_name")
        if const_name:
            setattr(const, const_name, value)
        else:
            return

    # Keep process-global Swiss Ephemeris state and imported caches in sync.
    if key == "default_ayanamsa_mode":
        from jhora.panchanga import drik
        drik.set_ayanamsa_mode(value)
    elif key in set_planet_list_keys:
        from jhora.panchanga import drik
        drik.set_planet_list(
            set_rahu_ketu_as_true_nodes=const._use_true_nodes_for_rahu_ketu,
            include_western_planets=const._INCLUDE_URANUS_TO_PLUTO
        )
    elif key in set_planet_flag_keys:
        from jhora.panchanga import drik
        drik.refresh_planet_flags()


def apply_all_settings() -> None:
    for key in _FACTORY.keys():
        apply_setting(key)


# ============================================================
# UI MODEL
# ============================================================
def get_ui_model(*, tab: Optional[str] = None, visible_only: bool = True) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    for key, meta in _FACTORY.items():
        visible = bool(meta.get("visible", True))
        tab_name = str(meta.get("tab", "User"))

        if visible_only and not visible:
            continue
        if tab is not None and tab_name.lower() != str(tab).lower():
            continue

        item = _deepcopy(meta)
        item["key"] = key
        item["value"] = get_value(key)
        items.append(item)

    items.sort(key=lambda x: (
        str(x.get("tab", "")),
        str(x.get("section", "")),
        int(x.get("order", 0)),
        str(x.get("label", ""))
    ))
    return items


def get_ui_tabs() -> List[str]:
    tabs: List[str] = []
    for meta in _FACTORY.values():
        tab = str(meta.get("tab", "")).strip()
        if tab and tab not in tabs:
            tabs.append(tab)
    return tabs


def get_ui_sections(tab: Optional[str] = None, *, visible_only: bool = True) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for item in get_ui_model(tab=tab, visible_only=visible_only):
        section = str(item.get("section", "general"))
        grouped.setdefault(section, []).append(item)
    return grouped


# ============================================================
# INIT
# ============================================================
def initialize_runtime(*, force_reload: bool = False, create_if_missing: bool = True, silent: bool = True):
    global _SETTINGS_LOADED

    if _SETTINGS_LOADED and not force_reload:
        return None

    try:
        data = load_all_settings(create_if_missing=create_if_missing, apply=True)
        _SETTINGS_LOADED = True
        return data
    except Exception:
        if silent:
            return None
        raise


def get_settings_dict() -> Dict[str, Dict[str, Any]]:
    return get_all_setting_defs()


def get_current_settings() -> Dict[str, Dict[str, Any]]:
    return get_all_setting_defs()

def validate_const_synchronization():
    """
    Validates that hardcoded const fallbacks match factory_settings.json defaults.
    Loops through all configurations using PyJHora's native normalization engine
    and dynamically resolves 'enum_class' structural mappings.
    """
    with open(FACTORY_SETTINGS_FILE, "r", encoding="utf-8") as f:
        factory_data = json.load(f)

    for setting_key, metadata in factory_data.items():
        const_name = metadata.get("const_name")
        if not const_name or not hasattr(const, const_name):
            continue

        raw_json_default = metadata["default"]
        const_value = getattr(const, const_name)

        # 1. Normalize the raw JSON value to its primary data type
        normalized_json_default = _normalize_value(metadata, raw_json_default)

        # 2. Resolve Enum/Class mappings if designated in metadata
        enum_class_name = metadata.get("enum_class")
        if enum_class_name and hasattr(const, enum_class_name):
            try:
                enum_class = getattr(const, enum_class_name)
                
                # Case A: JSON value is a string (e.g., "SAV_SIGN" or "NONE")
                if isinstance(normalized_json_default, str):
                    if hasattr(enum_class, normalized_json_default):
                        normalized_json_default = getattr(enum_class, normalized_json_default)
                    elif hasattr(enum_class, '__getitem__'):
                        try:
                            normalized_json_default = enum_class[normalized_json_default]
                        except Exception:
                            pass
                
                # Case B: JSON value is an index integer (e.g., 0, 1, 2)
                elif isinstance(normalized_json_default, (int, float)) and not isinstance(normalized_json_default, bool):
                    # Check if the class can be called like a standard Enum class(value)
                    try:
                        normalized_json_default = enum_class(normalized_json_default)
                    except (ValueError, TypeError):
                        # Fall back to checking raw static class properties matching the integer
                        for attr in dir(enum_class):
                            if not attr.startswith("_") and getattr(enum_class, attr) == normalized_json_default:
                                normalized_json_default = getattr(enum_class, attr)
                                break
            except Exception:
                pass

        # 3. Core matching verification
        is_match = (const_value == normalized_json_default) or (str(const_value) == str(normalized_json_default))

        # 4. Fallback checks for stringified None values or edge cases
        if not is_match:
            const_str = str(const_value).strip().lower()
            json_str = str(normalized_json_default).strip().lower()
            if const_str == json_str:
                is_match = True
            elif (const_value is None and json_str == "none") or (const_str == "none" and normalized_json_default is None):
                is_match = True

        # Handle optional string matching ("" vs None)
        if not is_match and metadata.get("nullable"):
            if (const_value is None and normalized_json_default == "") or (const_value == "" and normalized_json_default is None):
                is_match = True

        # Perform the actual safety assert
        assert is_match, \
            f"Configuration Drift Error for '{setting_key}'!\n" \
            f"  const.{const_name} = {const_value} (type: {type(const_value).__name__})\n" \
            f"  JSON default = {raw_json_default} (normalized/resolved to: {normalized_json_default})"
    print("✅ Validation Success: All hardcoded const fallbacks are perfectly synchronized with factory_settings.json!")
# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    validate_const_synchronization()
    exit()
    print("Loading settings...")
    load_all_settings(create_if_missing=True, apply=True)
    print("Loaded successfully.")
    print(snapshot_values())
