from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gkmas_defaults import DEFAULT_CHARACTERS, DEFAULT_DAILY_IDOL_CONFIG, DEFAULT_GROUPS
from gkmas_errors import GkmasDiceError
from gkmas_models import Character, GroupDef, PortraitLayout


class GkmasRepository:
    """读取角色配置、组合配置，并负责别名解析。"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.config_dir = base_dir / "config"
        self.assets_dir = base_dir / "assets" / "characters"
        self.characters_path = self.config_dir / "characters.json"
        self.groups_path = self.config_dir / "groups.json"
        self.daily_idol_path = self.config_dir / "daily_idol.json"
        self.characters: dict[str, Character] = {}
        self.groups: dict[str, GroupDef] = {}
        self.daily_idol_group = "hatsuboshi"
        self.char_alias: dict[str, str] = {}
        self.group_alias: dict[str, str] = {}

    def load(self) -> None:
        self._ensure_default_files()
        self._load_characters()
        self._load_groups()
        self._load_daily_idol_config()
        self._build_alias_maps()

    def _ensure_default_files(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        if not self.characters_path.exists():
            self.characters_path.write_text(
                json.dumps(DEFAULT_CHARACTERS, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        if not self.groups_path.exists():
            self.groups_path.write_text(
                json.dumps(DEFAULT_GROUPS, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        if not self.daily_idol_path.exists():
            self.daily_idol_path.write_text(
                json.dumps(DEFAULT_DAILY_IDOL_CONFIG, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def _load_json_list(self, path: Path, key: str) -> list[dict[str, Any]]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise GkmasDiceError(f"配置文件读取失败：{path.name}：{exc}") from exc

        if isinstance(data, dict):
            items = data.get(key, [])
        elif isinstance(data, list):
            items = data
        else:
            raise GkmasDiceError(f"配置文件格式错误：{path.name} 必须是数组或包含 {key} 的对象。")
        if not isinstance(items, list):
            raise GkmasDiceError(f"配置文件格式错误：{path.name} 的 {key} 必须是数组。")
        return items

    def _load_characters(self) -> None:
        self.characters.clear()
        items = self._load_json_list(self.characters_path, "characters")
        updated_config = False
        for raw in items:
            cid = str(raw.get("id", "")).strip()
            if not cid:
                raise GkmasDiceError("characters.json 中存在没有 id 的角色。")
            if cid in self.characters:
                raise GkmasDiceError(f"characters.json 中角色 id 重复：{cid}")
            name_full = str(raw.get("name_full") or raw.get("name") or cid).strip()
            name_short = str(raw.get("name_short") or name_full).strip()
            aliases = [str(x).strip() for x in raw.get("aliases", []) if str(x).strip()]
            image = str(raw.get("image", f"assets/characters/{cid}.png")).strip()
            color = str(raw.get("color", "#EAEAEA")).strip()
            portrait, portrait_updated = self._load_portrait(raw, cid)
            updated_config = updated_config or portrait_updated
            self.characters[cid] = Character(cid, name_full, name_short, aliases, image, color, portrait)

        if updated_config:
            self.characters_path.write_text(
                json.dumps({"characters": items}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def _load_portrait(self, raw: dict[str, Any], cid: str) -> tuple[PortraitLayout, bool]:
        default = PortraitLayout()
        portrait = raw.get("portrait")
        updated = False
        if not isinstance(portrait, dict):
            portrait = {}
            raw["portrait"] = portrait
            updated = True

        x, x_updated = self._portrait_int(portrait, "x", default.x, cid, positive=False)
        y, y_updated = self._portrait_int(portrait, "y", default.y, cid, positive=False)
        width, width_updated = self._portrait_int(portrait, "width", default.width, cid, positive=True)
        height, height_updated = self._portrait_int(portrait, "height", default.height, cid, positive=True)
        crop_bottom, crop_bottom_updated = self._portrait_int(
            portrait,
            "crop_bottom",
            default.crop_bottom,
            cid,
            positive=False,
            minimum=0,
        )
        updated = updated or x_updated or y_updated or width_updated or height_updated or crop_bottom_updated
        return PortraitLayout(x=x, y=y, width=width, height=height, crop_bottom=crop_bottom), updated

    @staticmethod
    def _portrait_int(
        portrait: dict[str, Any],
        key: str,
        default: int,
        cid: str,
        *,
        positive: bool,
        minimum: int | None = None,
    ) -> tuple[int, bool]:
        if key not in portrait:
            portrait[key] = default
            return default, True

        value = portrait[key]
        if isinstance(value, bool):
            raise GkmasDiceError(f"角色 {cid} 的 portrait.{key} 必须是整数。")
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise GkmasDiceError(f"角色 {cid} 的 portrait.{key} 必须是整数。") from exc
        if positive and parsed <= 0:
            raise GkmasDiceError(f"角色 {cid} 的 portrait.{key} 必须大于 0。")
        if minimum is not None and parsed < minimum:
            raise GkmasDiceError(f"角色 {cid} 的 portrait.{key} 必须大于等于 {minimum}。")
        if parsed != value:
            portrait[key] = parsed
            return parsed, True
        return parsed, False

    def _load_groups(self) -> None:
        self.groups.clear()
        for raw in self._load_json_list(self.groups_path, "groups"):
            gid = str(raw.get("id", "")).strip()
            if not gid:
                raise GkmasDiceError("groups.json 中存在没有 id 的组合。")
            if gid in self.groups:
                raise GkmasDiceError(f"groups.json 中组合 id 重复：{gid}")
            name = str(raw.get("name", gid)).strip()
            aliases = [str(x).strip() for x in raw.get("aliases", []) if str(x).strip()]
            expression = str(raw.get("expression", "")).strip()
            if not expression:
                raise GkmasDiceError(f"组合 {gid} 没有 expression。")
            self.groups[gid] = GroupDef(gid, name, aliases, expression)

    def _load_daily_idol_config(self) -> None:
        try:
            data = json.loads(self.daily_idol_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise GkmasDiceError(f"配置文件读取失败：{self.daily_idol_path.name}：{exc}") from exc

        if not isinstance(data, dict):
            raise GkmasDiceError(f"配置文件格式错误：{self.daily_idol_path.name} 必须是对象。")

        group = str(data.get("group") or data.get("expression") or "").strip()
        if not group:
            raise GkmasDiceError("daily_idol.json 中 group 不能为空。")
        self.daily_idol_group = group

    def _add_alias(self, alias_map: dict[str, str], alias: str, target: str, kind: str) -> None:
        key = self._norm(alias)
        if not key:
            return
        if key in alias_map and alias_map[key] != target:
            raise GkmasDiceError(f"{kind}别名冲突：{alias} 同时指向 {alias_map[key]} 和 {target}")
        alias_map[key] = target

    def _build_alias_maps(self) -> None:
        self.char_alias.clear()
        self.group_alias.clear()
        for cid, ch in self.characters.items():
            for alias in [cid, ch.name_short, ch.name_full, *ch.aliases]:
                self._add_alias(self.char_alias, alias, cid, "角色")

        for gid, group in self.groups.items():
            for alias in [gid, group.name, *group.aliases]:
                self._add_alias(self.group_alias, alias, gid, "组合")

    @staticmethod
    def _norm(text: str) -> str:
        return text.strip().lower()

    def resolve_character(self, token: str) -> Character | None:
        cid = self.char_alias.get(self._norm(token))
        return self.characters.get(cid) if cid else None

    def resolve_group(self, token: str) -> GroupDef | None:
        gid = self.group_alias.get(self._norm(token))
        return self.groups.get(gid) if gid else None

    def character_image_path(self, ch: Character) -> Path:
        path = Path(ch.image)
        if not path.is_absolute():
            path = self.base_dir / path
        return path
