from __future__ import annotations

import importlib
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

for module_name in (
    "gkmas_errors",
    "gkmas_models",
    "gkmas_defaults",
    "gkmas_repository",
    "gkmas_expression",
    "gkmas_renderer",
    "gkmas_commands",
):
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from gkmas_commands import GkmasCommandService
from gkmas_errors import GkmasDiceError
from gkmas_expression import ExpressionParser
from gkmas_renderer import DiceImageRenderer
from gkmas_repository import GkmasRepository

PLUGIN_NAME = "astrbot_plugin_gkmasdice"


@register(PLUGIN_NAME, "Azenix", "学园偶像大师掷骰图生成插件 MVP", "0.1.0")
class GkmasDicePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.base_dir = BASE_DIR
        self.repo = GkmasRepository(self.base_dir)
        self.parser = ExpressionParser(self.repo)
        self.renderer = DiceImageRenderer(self.repo, self.base_dir / "data" / "generated")
        self.commands = GkmasCommandService(self.repo, self.parser)

    async def initialize(self):
        self.repo.load()
        logger.info("gkmasdice initialized")

    @filter.command("gkmasdice", alias={"gk骰", "学马骰"})
    async def gkmasdice(self, event: AstrMessageEvent):
        """学园偶像大师掷骰图生成。用法：/gkmasdice 掷骰图生成 saki+tmr --shuffle --seed 1"""
        try:
            args = self.commands.extract_args(event.message_str)
            if not args or args[0] in {"help", "帮助", "-h", "--help"}:
                yield event.plain_result(self.commands.help_text())
                return

            subcmd = args[0]
            if subcmd in {"掷骰图生成", "生成", "dice", "image", "图生成"}:
                options, entries = self.commands.handle_generate_args(args[1:])
                result = self.renderer.render(entries, options)
                image_path = getattr(result, "image_path", str(result))
                font_info = getattr(result, "font_info", "未知（请重载插件以刷新渲染模块）")
                names = "、".join(self.repo.characters[cid].name_full for cid in entries)
                shuffle_text = "已打乱" if options.shuffle else "未打乱"
                seed_text = f"，seed={options.seed}" if options.seed is not None else ""
                yield event.plain_result(
                    f"生成完成：{len(entries)} 个条目，{options.columns} 列，{shuffle_text}{seed_text}\n"
                    # f"字体：{font_info}\n"
                    f"{names}"
                )
                yield event.image_result(image_path)
                return

            if subcmd in {"角色列表", "chars", "characters"}:
                yield event.plain_result(self.commands.characters_text())
                return

            if subcmd in {"组合列表", "groups"}:
                yield event.plain_result(self.commands.groups_text())
                return

            raise GkmasDiceError(f"未知子指令：{subcmd}\n发送 /gkmasdice help 查看帮助。")
        except GkmasDiceError as exc:
            yield event.plain_result(f"gkmasdice 错误：{exc}")
        except Exception as exc:
            logger.exception("gkmasdice unexpected error")
            yield event.plain_result(f"gkmasdice 内部错误：{exc}")

    async def terminate(self):
        logger.info("gkmasdice terminated")
