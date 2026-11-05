#!/usr/bin/env python3
"""
rpy2json.py — 把 Ren'Py 工程里的剧本（icancook/game/*.rpy）转成网页 Demo 用的 story.json

设计目标：
  * 唯一内容源：网页 Demo 和 exe 版读的是同一份 .rpy 剧本，不维护两套
  * 输出「扁平指令流」：每个 label 编译成数组，跳转全部变成指令下标，
    这样存档只需要记 (label, pc, 变量)，不需要序列化调用栈

支持的 Ren'Py 子集（本项目实际用到的全部语法）：
  label / say / menu / if-elif-else / jump / return / $ 赋值 /
  scene / show ... at ... / with Dissolve(x) / centered / call screen

用法：
  python3 tools/rpy2json.py icancook/game/script.rpy -o demo/story.json
"""

import argparse
import json
import re
import sys

WS = re.compile(r"^(\s*)")

# ---------------------------------------------------------------- 条件翻译

def translate_cond(expr: str) -> str:
    """把 Ren'Py/Python 条件翻译成 JS 表达式。只处理本项目出现的写法。"""
    e = expr.strip()
    e = re.sub(r"\bis\s+not\s+None\b", "!= null", e)
    e = re.sub(r"\bis\s+None\b", "== null", e)
    e = re.sub(r"\bTrue\b", "true", e)
    e = re.sub(r"\bFalse\b", "false", e)
    e = re.sub(r"\band\b", "&&", e)
    e = re.sub(r"\bor\b", "||", e)
    e = re.sub(r"\bnot\b", "!", e)
    return e


def translate_stmt(expr: str) -> str:
    """把 `$ trust += 1` 这类语句翻译成 JS。"""
    e = expr.strip()
    e = re.sub(r"\bTrue\b", "true", e)
    e = re.sub(r"\bFalse\b", "false", e)
    e = re.sub(r"\bNone\b", "null", e)
    return e


# ---------------------------------------------------------------- 词法小工具

def strip_comment(line: str) -> str:
    """去掉整行注释（本项目不含行尾注释，避免误伤字符串里的 #）。"""
    s = line.strip()
    if s.startswith("#"):
        return ""
    return line


def unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s


# ---------------------------------------------------------------- 编译器

class Compiler:
    def __init__(self):
        self.labels = {}
        self.defaults = {}
        self.screens = {}

    # ---- 入口
    def compile_file(self, path):
        with open(path, encoding="utf-8-sig") as f:
            raw = f.read()
        lines = []
        for ln in raw.split("\n"):
            ln = ln.replace("\t", "    ").rstrip()
            ln = strip_comment(ln)
            if not ln.strip():
                continue
            indent = len(WS.match(ln).group(1))
            lines.append((indent, ln.strip()))
        self.parse_toplevel(lines, path)

    # ---- 顶层：label / default / define / transform / screen
    def parse_toplevel(self, lines, path):
        i = 0
        n = len(lines)
        while i < n:
            indent, text = lines[i]
            if indent != 0:
                i += 1
                continue

            if text.startswith("label "):
                name = text[len("label "):].rstrip(":").strip()
                body, i = self.collect_block(lines, i + 1)
                self.labels[name] = self.emit(body)

            elif text.startswith("default "):
                m = re.match(r"default\s+(\w+)\s*=\s*(.+)", text)
                if m:
                    key, val = m.group(1), m.group(2).strip()
                    if val.startswith("set()"):
                        self.defaults[key] = {"__set__": True}
                    elif val.startswith('"') or val.startswith("'"):
                        self.defaults[key] = unquote(val)
                    elif val in ("True", "False"):
                        self.defaults[key] = (val == "True")
                    elif val == "None":
                        self.defaults[key] = None
                    else:
                        try:
                            self.defaults[key] = int(val)
                        except ValueError:
                            self.defaults[key] = 0
                i += 1

            elif text.startswith("screen "):
                name = re.match(r"screen\s+(\w+)", text).group(1)
                body, i = self.collect_block(lines, i + 1)
                self.screens[name] = body

            else:
                # define / transform / init python / image 等：整块跳过
                _, i = self.collect_block(lines, i + 1)

    # ---- 收集缩进块
    def collect_block(self, lines, start):
        body = []
        if start >= len(lines):
            return body, start
        base = lines[start][0]
        if base == 0:
            # 同级语句之间没有缩进关系，不能把整份文件吞成一个块
            return [], start
        i = start
        while i < len(lines) and lines[i][0] >= base:
            body.append(lines[i])
            i += 1
        if body:
            rel = [(ind - base, t) for ind, t in body]
        else:
            rel = []
        return rel, i

    # ---- 把一个块编译成扁平指令流
    def emit(self, block):
        code = []
        self.emit_into(block, code)
        code.append({"op": "end"})
        return code

    def emit_into(self, block, code):
        i = 0
        n = len(block)
        while i < n:
            indent, text = block[i]

            # ---------------- menu
            if text == "menu:" or text.startswith("menu ") or text.startswith("menu:"):
                # 收集 menu 块所有选项
                menu_body, i = self.collect_block(block, i + 1)
                options = []          # [(caption, body_block)]
                k = 0
                while k < len(menu_body):
                    cind, ctext = menu_body[k]
                    if ctext.endswith(":") and not ctext.startswith("$"):
                        cap = unquote(ctext[:-1])
                        obody, k2 = self.collect_block(menu_body, k + 1)
                        options.append((cap, obody))
                        k = k2
                    else:
                        k += 1

                # 先放一条占位，稍后回填各分支入口
                menu_idx = len(code)
                code.append({"op": "menu", "options": []})

                ends = []
                for cap, obody in options:
                    target = len(code)
                    code[menu_idx]["options"].append({"text": cap, "pc": target})
                    self.emit_into(obody, code)
                    ends.append(len(code))
                    code.append({"op": "jump", "label": None, "pc": None})  # 占位

                after = len(code)
                for p in ends:
                    code[p]["pc"] = after
                continue

            # ---------------- if / elif / else
            if text.startswith("if "):
                cond = text[3:].rstrip(":").strip()
                then_block, i = self.collect_block(block, i + 1)
                branches = [(cond, then_block)]
                else_block = None

                while i < n:
                    ind2, t2 = block[i]
                    if t2.startswith("elif "):
                        c2 = t2[5:].rstrip(":").strip()
                        b2, i = self.collect_block(block, i + 1)
                        branches.append((c2, b2))
                    elif t2.strip() == "else:":
                        else_block, i = self.collect_block(block, i + 1)
                        break
                    else:
                        break

                jumps = []
                for c, b in branches:
                    if_idx = len(code)
                    code.append({"op": "if", "cond": translate_cond(c), "pc": None, "else_pc": None})
                    self.emit_into(b, code)
                    j = len(code)
                    code.append({"op": "jump", "label": None, "pc": None})
                    jumps.append(j)
                    code[if_idx]["pc"] = if_idx + 1
                    code[if_idx]["else_pc"] = len(code)

                if else_block:
                    self.emit_into(else_block, code)

                after = len(code)
                for j in jumps:
                    code[j]["pc"] = after
                # 最后一个 if 的 else 也指向 after
                for ins in code:
                    if ins["op"] == "if" and ins["else_pc"] is None:
                        ins["else_pc"] = after
                continue

            # ---------------- 赋值
            if text.startswith("$"):
                stmt = text[1:].strip()
                if stmt.startswith("persistent."):
                    m = re.match(r"persistent\.(\w+)\s*=\s*True", stmt)
                    if m:
                        code.append({"op": "unlock", "flag": m.group(1)})
                    i += 1
                    continue
                if stmt.startswith("renpy."):
                    i += 1
                    continue
                code.append({"op": "set", "expr": translate_stmt(stmt)})
                i += 1
                continue

            # ---------------- 场景 / 图层
            if text.startswith("scene "):
                rest = text[6:].strip()
                img, _, _at = rest.partition(" at ")
                if " with " in rest:
                    img = rest.split(" with ")[0]
                code.append({"op": "scene", "img": img.strip()})
                i += 1
                continue

            if text.startswith("show "):
                rest = text[5:].strip()
                at = None
                if " at " in rest:
                    img, at = rest.split(" at ", 1)
                else:
                    img = rest
                code.append({"op": "show", "img": img.strip(), "at": (at or "").strip() or None})
                i += 1
                continue

            # ---------------- 音频与停顿（过场用）
            if text.startswith("play ") or text.startswith("queue "):
                rest = text.split(" ", 1)[1]
                parts = rest.split()
                channel = parts[0] if parts else "sound"
                target = parts[1] if len(parts) > 1 else ""
                fade = None
                m = re.search(r"fadein\s+([\d.]+)", rest)
                if m:
                    fade = float(m.group(1))
                code.append({"op": "play", "channel": channel, "target": target, "fade": fade})
                i += 1
                continue

            if text.startswith("stop "):
                rest = text.split(" ", 1)[1]
                channel = rest.split()[0]
                m = re.search(r"fadeout\s+([\d.]+)", rest)
                code.append({"op": "stop", "channel": channel,
                             "fade": float(m.group(1)) if m else None})
                i += 1
                continue

            if text.startswith("pause"):
                m = re.search(r"([\d.]+)", text)
                code.append({"op": "wait", "sec": float(m.group(1)) if m else 0.5})
                i += 1
                continue

            if text.startswith("hide "):
                code.append({"op": "hide", "img": text[5:].strip()})
                i += 1
                continue

            if text.startswith("with "):
                trans = text[5:].strip()
                m = re.match(r"Dissolve\(([\d.]+)\)", trans)
                dur = float(m.group(1)) if m else 0.6
                code.append({"op": "with", "dur": dur})
                i += 1
                continue

            # ---------------- 流程
            if text.startswith("jump "):
                code.append({"op": "jump", "label": text[5:].strip()})
                i += 1
                continue

            if text == "return":
                code.append({"op": "return"})
                i += 1
                continue

            if text.startswith("call screen "):
                code.append({"op": "screen", "name": text[len("call screen "):].strip()})
                i += 1
                continue

            if text.startswith("centered "):
                code.append({"op": "centered", "text": unquote(text[len("centered "):])})
                i += 1
                continue

            if text.startswith("pause"):
                code.append({"op": "wait", "dur": 0.4})
                i += 1
                continue

            # ---------------- 对白
            m = re.match(r'^(\w+)\s+"(.*)"$', text)
            if m:
                who, txt = m.group(1), m.group(2)
                code.append({"op": "say", "who": who, "text": txt})
                i += 1
                continue

            # 未识别：跳过（例如 screen 里的界面语句）
            i += 1


# ---------------------------------------------------------------- 主流程

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sources", nargs="+")
    ap.add_argument("-o", "--out", default="demo/story.json")
    args = ap.parse_args()

    c = Compiler()
    for src in args.sources:
        c.compile_file(src)

    data = {
        "meta": {
            "title": "我在这儿就能为你下厨了",
            "title_en": "I Can Cook For You From Here",
            "chapter": "Ch0 · 重制版第一次约会",
            "source": "icancook/game/script.rpy（与 exe 版同一份剧本）",
        },
        "defaults": c.defaults,
        "labels": c.labels,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    total = sum(len(v) for v in c.labels.values())
    print(f"labels: {len(c.labels)}  instructions: {total}  -> {args.out}")
    for name, code in c.labels.items():
        ops = {}
        for ins in code:
            ops[ins["op"]] = ops.get(ins["op"], 0) + 1
        print(f"  {name:16s} {len(code):4d} {ops}")

    # 跳转目标体检
    bad = 0
    for name, code in c.labels.items():
        for i, ins in enumerate(code):
            if ins["op"] == "jump" and ins.get("label") and ins["label"] not in c.labels:
                print(f"  !! {name}[{i}] jumps to missing label {ins['label']}")
                bad += 1
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
