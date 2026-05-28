from __future__ import annotations

import shlex

from gkmas_errors import GkmasDiceError
from gkmas_expression import ExpressionParser
from gkmas_models import RenderOptions
from gkmas_repository import GkmasRepository


class GkmasCommandService:
    def __init__(self, repo: GkmasRepository, parser: ExpressionParser):
        self.repo = repo
        self.parser = parser

    def extract_args(self, message: str) -> list[str]:
        text = message.strip()
        if text.startswith("/"):
            text = text[1:]
        parts = text.split(maxsplit=1)
        if not parts:
            return []
        if parts[0] in {"gkmasdice", "gk骰", "学马骰"}:
            rest = parts[1] if len(parts) > 1 else ""
        else:
            rest = text
        if not rest.strip():
            return []
        return shlex.split(rest)

    def handle_generate_args(self, args: list[str]) -> tuple[RenderOptions, list[str]]:
        if not args or args[0].startswith("--"):
            raise GkmasDiceError("用法：/gkmasdice 掷骰图生成 [列数] <表达式> [--shuffle] [--seed 数字]")
        if len(args) == 1:
            try:
                int(args[0])
            except ValueError:
                pass
            else:
                raise GkmasDiceError("缺少角色表达式。")

        columns = 3
        expression_index = 0
        if len(args) >= 2:
            try:
                columns = int(args[0])
                expression_index = 1
            except ValueError:
                pass
        if columns <= 0:
            raise GkmasDiceError("列数必须大于 0。")

        expression = args[expression_index]
        shuffle = False
        seed: int | None = None
        label_mode = "short"

        i = expression_index + 1
        while i < len(args):
            token = args[i]
            if token == "--shuffle":
                shuffle = True
                i += 1
            elif token == "--no-shuffle":
                shuffle = False
                i += 1
            elif token == "--seed":
                if i + 1 >= len(args):
                    raise GkmasDiceError("--seed 后需要一个整数。")
                try:
                    seed = int(args[i + 1])
                except ValueError as exc:
                    raise GkmasDiceError(f"seed 必须是整数：{args[i + 1]}") from exc
                i += 2
            elif token.startswith("--seed="):
                raw = token.split("=", 1)[1]
                try:
                    seed = int(raw)
                except ValueError as exc:
                    raise GkmasDiceError(f"seed 必须是整数：{raw}") from exc
                i += 1
            elif token == "--label":
                if i + 1 >= len(args):
                    raise GkmasDiceError("--label 后需要 short/full/id。")
                label_mode = args[i + 1]
                if label_mode not in {"short", "full", "id"}:
                    raise GkmasDiceError("--label 只支持 short、full、id。")
                i += 2
            elif token.startswith("--label="):
                label_mode = token.split("=", 1)[1]
                if label_mode not in {"short", "full", "id"}:
                    raise GkmasDiceError("--label 只支持 short、full、id。")
                i += 1
            else:
                raise GkmasDiceError(f"未知选项：{token}")

        entries = self.parser.parse(expression)
        options = RenderOptions(columns=columns, shuffle=shuffle, seed=seed, label_mode=label_mode)
        return options, entries

    @staticmethod
    def help_text() -> str:
        return (
            "gkmasdice MVP 帮助\n"
            "1. 生成掷骰图：\n"
            "   /gkmasdice 掷骰图生成 [列数] <表达式> [--shuffle] [--seed 数字] [--label short|full|id]\n"
            "   不写列数时默认 3 列；例如：/gkmasdice 生成 saki+tmr\n"
            "2. 表达式语法：\n"
            "   + 表示拼接，- 表示删除，* 表示重复；* 可用于角色和组合。\n"
            "   例：saki+tmr+ktn、初星全员-saki*2、组合S*2+mao\n"
            "3. 角色匹配：角色ID、短显示名、长显示名、别名均可使用。\n"
            "4. 组合匹配：组合ID、组合名、组合别名均可使用。\n"
            "5. 查看配置：\n"
            "   /gkmasdice 角色列表\n"
            "   /gkmasdice 组合列表\n"
            "\n当前 MVP 暂未实现抽取池。"
        )

    def characters_text(self) -> str:
        lines = ["当前角色："]
        for ch in self.repo.characters.values():
            aliases = "、".join(ch.aliases[:6])
            lines.append(f"- {ch.id}: {ch.name_full}（{ch.name_short}） 别名：{aliases}")
        return "\n".join(lines)

    def groups_text(self) -> str:
        lines = ["当前组合："]
        for group in self.repo.groups.values():
            aliases = "、".join(group.aliases)
            lines.append(f"- {group.id}: {group.name} 别名：{aliases} 表达式：{group.expression}")
        return "\n".join(lines)
