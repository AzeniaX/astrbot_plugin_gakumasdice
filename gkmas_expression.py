from __future__ import annotations

import re

from gkmas_errors import GkmasDiceError
from gkmas_repository import GkmasRepository


class ExpressionParser:
    """解析 `saki+tmr-组合A*2` 形式的角色表达式。"""

    TOKEN_RE = re.compile(r"[^+\-*\s]+|[+\-*]")

    def __init__(self, repo: GkmasRepository):
        self.repo = repo

    def parse(self, expression: str) -> list[str]:
        expression = expression.strip()
        if not expression:
            raise GkmasDiceError("角色表达式为空。")
        result = self._parse_expression(expression, stack=[])
        if not result:
            raise GkmasDiceError("表达式解析后的角色列表为空。")
        return result

    def _parse_expression(self, expression: str, stack: list[str]) -> list[str]:
        tokens = self.TOKEN_RE.findall(expression)
        if not tokens:
            raise GkmasDiceError("角色表达式为空或格式错误。")

        result: list[str] = []
        op = "+"
        i = 0
        expect_atom = True

        while i < len(tokens):
            token = tokens[i]
            if token in {"+", "-"}:
                if expect_atom:
                    raise GkmasDiceError(f"运算符位置错误：{token}")
                op = token
                expect_atom = True
                i += 1
                continue
            if token == "*":
                raise GkmasDiceError("乘号左侧缺少角色或组合。")

            atom = token
            count = 1
            i += 1
            if i < len(tokens) and tokens[i] == "*":
                if i + 1 >= len(tokens):
                    raise GkmasDiceError("乘号后缺少重复次数。")
                raw_count = tokens[i + 1]
                if not raw_count.isdigit() or int(raw_count) <= 0:
                    raise GkmasDiceError(f"重复次数必须是正整数：{raw_count}")
                count = int(raw_count)
                i += 2

            entries = self._expand_atom(atom, stack) * count
            if op == "+":
                result.extend(entries)
            elif op == "-":
                for entry in entries:
                    try:
                        result.remove(entry)
                    except ValueError:
                        pass
            else:
                raise GkmasDiceError(f"未知运算符：{op}")
            expect_atom = False

        if expect_atom:
            raise GkmasDiceError("表达式不能以运算符结尾。")
        return result

    def _expand_atom(self, atom: str, stack: list[str]) -> list[str]:
        ch = self.repo.resolve_character(atom)
        if ch:
            return [ch.id]

        group = self.repo.resolve_group(atom)
        if group:
            if group.id in stack:
                cycle = " -> ".join([*stack, group.id])
                raise GkmasDiceError(f"组合定义存在循环引用：{cycle}")
            return self._parse_expression(group.expression, [*stack, group.id])

        raise GkmasDiceError(f"无法识别角色或组合：{atom}")
