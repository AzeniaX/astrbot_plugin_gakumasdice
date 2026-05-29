from __future__ import annotations

import math
import logging
import random
import re
import time
import urllib.request
from pathlib import Path

from gkmas_errors import GkmasDiceError
from gkmas_models import Character, RenderOptions, RenderResult
from gkmas_repository import GkmasRepository

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover
    Image = None
    ImageDraw = None
    ImageFont = None

logger = logging.getLogger(__name__)

CELL_WIDTH = 300
CELL_HEIGHT = 150
FONT_CACHE_DIR = Path(__file__).resolve().parent / "data" / "fonts"
FONT_DOWNLOADS = {
    False: (
        "SourceHanSansSC-Regular.otf",
        "https://raw.githubusercontent.com/adobe-fonts/source-han-sans/release/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf",
    ),
    True: (
        "SourceHanSansSC-Bold.otf",
        "https://raw.githubusercontent.com/adobe-fonts/source-han-sans/release/OTF/SimplifiedChinese/SourceHanSansSC-Bold.otf",
    ),
}
MANUAL_FONT_HINT = (
    "请手动下载 SourceHanSansSC-Regular.otf 和 SourceHanSansSC-Bold.otf，"
    f"放到插件目录的 {FONT_CACHE_DIR} 后重试。"
)


class LoadedFont:
    def __init__(self, font, path: Path):
        self.font = font
        self.path = path


class DiceImageRenderer:
    def __init__(self, repo: GkmasRepository, output_dir: Path):
        self.repo = repo
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render(self, entries: list[str], options: RenderOptions) -> RenderResult:
        if Image is None:
            raise GkmasDiceError("缺少 Pillow 依赖，请在 requirements.txt 中安装 pillow。")
        if options.columns <= 0:
            raise GkmasDiceError("列数必须是正整数。")
        if options.columns > 12:
            raise GkmasDiceError("列数过大，建议不超过 12。")
        if not entries:
            raise GkmasDiceError("没有可绘制的角色。")
        if len(entries) > 120:
            raise GkmasDiceError("单张图角色数量过多，当前限制为 120。")

        draw_entries = entries[:]
        if options.shuffle:
            rng = random.Random(options.seed)
            rng.shuffle(draw_entries)

        cell_w, cell_h = CELL_WIDTH, CELL_HEIGHT
        cols = options.columns
        rows = math.ceil(len(draw_entries) / cols)
        canvas = Image.new("RGB", (cell_w * cols, cell_h * rows), "#F5F5F5")
        font_num = self._load_font(52, bold=True)
        font_name = self._load_font(42, bold=True)
        font_small = self._load_font(24, bold=False)
        font_info = self._font_info(font_num.path, font_small.path)

        for idx, cid in enumerate(draw_entries, start=1):
            ch = self.repo.characters.get(cid)
            if ch is None:
                continue
            row = (idx - 1) // cols
            col = (idx - 1) % cols
            x0, y0 = col * cell_w, row * cell_h
            self._draw_cell(canvas, x0, y0, cell_w, cell_h, idx, ch, options.label_mode, font_num, font_name, font_small)

        suffix = f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        out = self.output_dir / f"gkmasdice_{suffix}.png"
        canvas.save(out)
        return RenderResult(image_path=str(out), font_info=font_info)

    def _draw_cell(self, canvas, x0, y0, w, h, idx, ch, label_mode, font_num, font_name, font_small) -> None:
        draw = ImageDraw.Draw(canvas)
        color = ch.color if re.fullmatch(r"#[0-9a-fA-F]{6}", ch.color) else "#EAEAEA"
        draw.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], fill=color)

        #draw.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], outline="#FFFFFF", width=2)

        label = self._label(ch, label_mode)
        draw.text((x0 + 18, y0 + 10), str(idx), font=font_num.font, fill="#000000")
        self._draw_fit_text(draw, label, x0 + 16, y0 + 76, 180, font_name.font, font_small.font)

        portrait_box = self._portrait_box(x0, y0, ch)
        image_path = self.repo.character_image_path(ch)
        if image_path.exists():
            try:
                with Image.open(image_path) as source:
                    portrait = source.convert("RGBA")
                portrait = self._crop_portrait_bottom(portrait, ch)
                portrait.thumbnail((portrait_box[2] - portrait_box[0], portrait_box[3] - portrait_box[1]), Image.LANCZOS)
                px = portrait_box[0] + (portrait_box[2] - portrait_box[0] - portrait.width) // 2
                py = portrait_box[3] - portrait.height
                self._paste_image(canvas, portrait, px, py)
                return
            except GkmasDiceError:
                raise
            except Exception as exc:
                logger.warning(f"角色图片读取失败 {image_path}: {exc}")

        self._draw_placeholder(draw, portrait_box, ch, font_num)

    @staticmethod
    def _crop_portrait_bottom(image, ch: Character):
        crop_bottom = ch.portrait.crop_bottom
        if crop_bottom <= 0:
            return image
        if crop_bottom >= image.height:
            raise GkmasDiceError(
                f"角色 {ch.id} 的 portrait.crop_bottom={crop_bottom} 不能大于等于图片高度 {image.height}。"
            )
        return image.crop((0, 0, image.width, image.height - crop_bottom))

    @staticmethod
    def _portrait_box(x0: int, y0: int, ch: Character) -> tuple[int, int, int, int]:
        portrait = ch.portrait
        return (
            x0 + portrait.x,
            y0 + portrait.y,
            x0 + portrait.x + portrait.width,
            y0 + portrait.y + portrait.height,
        )

    @staticmethod
    def _paste_image(canvas, image, x: int, y: int) -> None:
        left = max(0, -x)
        top = max(0, -y)
        right = min(image.width, canvas.width - x)
        bottom = min(image.height, canvas.height - y)
        if left >= right or top >= bottom:
            return

        cropped = image.crop((left, top, right, bottom))
        canvas.paste(cropped, (x + left, y + top), cropped)

    @staticmethod
    def _draw_placeholder(draw, portrait_box, ch: Character, font_num) -> None:
        cx = (portrait_box[0] + portrait_box[2]) // 2
        cy = (portrait_box[1] + portrait_box[3]) // 2
        r = min(portrait_box[2] - portrait_box[0], portrait_box[3] - portrait_box[1]) // 3
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#FFFFFF", outline="#000000", width=2)
        initial = ch.name_short[:1] or ch.id[:1].upper()
        bbox = draw.textbbox((0, 0), initial, font=font_num.font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((cx - tw / 2, cy - th / 2 - 3), initial, font=font_num.font, fill="#000000")

    @staticmethod
    def _label(ch: Character, mode: str) -> str:
        if mode == "full":
            return ch.name_full
        if mode == "id":
            return ch.id
        return ch.name_short

    @staticmethod
    def _load_font(size: int, bold: bool = False):
        for path in DiceImageRenderer._font_candidates(bold):
            try:
                if path.exists():
                    return LoadedFont(ImageFont.truetype(path, size), path)
            except Exception as exc:
                logger.warning(f"字体加载失败 {path}: {exc}")

        downloaded = DiceImageRenderer._ensure_downloaded_font(bold)
        if downloaded:
            try:
                return LoadedFont(ImageFont.truetype(downloaded, size), downloaded)
            except Exception as exc:
                logger.warning(f"下载字体加载失败 {downloaded}: {exc}")

        raise GkmasDiceError(f"找不到可用的思源黑体字体，并且自动下载失败。{MANUAL_FONT_HINT}")

    @staticmethod
    def _font_candidates(bold: bool) -> list[Path]:
        downloaded_name = FONT_DOWNLOADS[bold][0]
        return [
            FONT_CACHE_DIR / downloaded_name,
            Path("C:/Windows/Fonts/SourceHanSansSC-Bold.otf" if bold else "C:/Windows/Fonts/SourceHanSansSC-Regular.otf"),
            Path("C:/Windows/Fonts/SourceHanSansCN-Bold.otf" if bold else "C:/Windows/Fonts/SourceHanSansCN-Regular.otf"),
            Path("C:/Windows/Fonts/SourceHanSans-Bold.otf" if bold else "C:/Windows/Fonts/SourceHanSans-Regular.otf"),
            Path("/Library/Fonts/SourceHanSansSC-Bold.otf" if bold else "/Library/Fonts/SourceHanSansSC-Regular.otf"),
            Path("/Library/Fonts/SourceHanSansCN-Bold.otf" if bold else "/Library/Fonts/SourceHanSansCN-Regular.otf"),
            Path("/Library/Fonts/SourceHanSans-Bold.otf" if bold else "/Library/Fonts/SourceHanSans-Regular.otf"),
            Path("/usr/share/fonts/opentype/source-han-sans/SourceHanSansSC-Bold.otf" if bold else "/usr/share/fonts/opentype/source-han-sans/SourceHanSansSC-Regular.otf"),
            Path("/usr/share/fonts/opentype/source-han-sans/SourceHanSansCN-Bold.otf" if bold else "/usr/share/fonts/opentype/source-han-sans/SourceHanSansCN-Regular.otf"),
            Path("/usr/share/fonts/opentype/source-han-sans/SourceHanSans-Bold.otf" if bold else "/usr/share/fonts/opentype/source-han-sans/SourceHanSans-Regular.otf"),
        ]

    @staticmethod
    def _ensure_downloaded_font(bold: bool) -> Path | None:
        filename, url = FONT_DOWNLOADS[bold]
        target = FONT_CACHE_DIR / filename
        if target.exists():
            return target

        FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix(target.suffix + ".download")
        try:
            logger.info(f"未找到可用字体，正在下载 {filename}")
            with urllib.request.urlopen(url, timeout=30) as response:
                temp.write_bytes(response.read())
            temp.replace(target)
            return target
        except Exception as exc:
            logger.warning(f"字体下载失败 {url}: {exc}")
            try:
                if temp.exists():
                    temp.unlink()
            except Exception:
                pass
            return None

    @staticmethod
    def _font_info(bold_path: Path, regular_path: Path) -> str:
        if bold_path == regular_path:
            return f"思源黑体：{bold_path}"
        return f"思源黑体：Regular={regular_path}；Bold={bold_path}"

    @staticmethod
    def _draw_fit_text(draw, text: str, x: int, y: int, max_w: int, large_font, small_font) -> None:
        font = large_font
        if draw.textbbox((0, 0), text, font=font)[2] > max_w:
            font = small_font
        draw.text((x, y), text, font=font, fill="#000000")
