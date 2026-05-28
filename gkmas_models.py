from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PortraitLayout:
    x: int = 145
    y: int = 0
    width: int = 155
    height: int = 150


@dataclass(frozen=True)
class Character:
    id: str
    name_full: str
    name_short: str
    aliases: list[str]
    image: str = ""
    color: str = "#EAEAEA"
    portrait: PortraitLayout = PortraitLayout()


@dataclass(frozen=True)
class GroupDef:
    id: str
    name: str
    aliases: list[str]
    expression: str


@dataclass
class RenderOptions:
    columns: int = 3
    shuffle: bool = False
    seed: int | None = None
    label_mode: str = "short"  # short / full / id


@dataclass(frozen=True)
class RenderResult:
    image_path: str
    font_info: str
