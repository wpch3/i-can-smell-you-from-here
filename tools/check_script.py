#!/usr/bin/env python3
"""
check_script.py —— 剧本静态检查（补 Ren'Py 编译器的盲区）

Ren'Py 的 compile 只查语法，不查"你 show 的这张图到底存不存在"；
lint 会查，但输出在 CI 日志里不方便本地迭代。这个脚本在本地就能查完：

  1. show / scene 用到的图片名，必须能解析到 image 定义或立绘组合
  2. jump 的 label 必须存在
  3. 台词里的 [变量] 必须在 default 里声明过
  4. 引号必须成对（字符串里嵌裸双引号会破坏解析）
  5. 每组 (造型, 表情) 必须在 sheet.json 里真实存在

用法：python3 tools/check_script.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAME = ROOT / "icancook" / "game"
SCRIPT = GAME / "script.rpy"
SHEET = GAME / "images" / "idimya" / "sheet.json"

problems = []


def bad(msg):
    problems.append(msg)


def main():
    text = SCRIPT.read_text(encoding="utf-8")
    lines = text.split("\n")

    # ---------- 1. 收集已定义的图片名
    defined = set()
    for m in re.finditer(r'^image\s+([\w ]+?)\s*=', text, re.M):
        defined.add(tuple(m.group(1).split()))
    # 立绘：image idimya <造型> <表情> 已由 build_sprites 写入 defined，root 名 "idimya"
    sprite_groups = {d[1:] for d in defined if d and d[0] == "idimya"}
    plain = {d[0] for d in defined if len(d) == 1}

    # ---------- 2. jump 目标
    labels = set(re.findall(r"^label\s+(\w+)\s*:", text, re.M))

    # ---------- 3. 变量
    defaults = set(re.findall(r"^default\s+(\w+)\s*=", text, re.M))
    defaults |= set(re.findall(r"^default\s+(\w+)\s*=", (GAME / "smell.rpy").read_text(encoding="utf-8"), re.M))
    defaults |= set(re.findall(r"^default\s+(\w+)\s*=", (GAME / "season.rpy").read_text(encoding="utf-8"), re.M))
    # persistent.* 与 Ren'Py 内置
    builtin = {"chapter_name", "_return"}

    # ---------- 4. 逐行检查
    for i, line in enumerate(lines, 1):
        st = line.strip()
        if not st or st.startswith("#"):
            continue

        # 引号成对（只查会带字符串的语句）
        if re.match(r"^(note|idimya|n|centered)\s", st) or st.startswith('text "'):
            if st.count('"') % 2:
                bad(f"{i}: 引号不成对 → {st[:70]}")

        # 台词变量
        for m in re.finditer(r"\[(\w+)\]", st):
            v = m.group(1)
            if v not in defaults and v not in builtin:
                bad(f"{i}: 台词引用了未声明的变量 [{v}]")

        # show 的图
        m = re.match(r"^show\s+([\w\s]+?)(?:\s+at\s|\s+with\s|$)", st)
        if m:
            parts = m.group(1).split()
            if parts[0] == "idimya":
                if len(parts) == 2:
                    key = ("base", parts[1])
                elif len(parts) >= 3:
                    key = (parts[1], parts[2])
                else:
                    continue
                if key not in sprite_groups:
                    bad(f"{i}: show idimya {' '.join(key)} —— sheet.json 里没有这一格")
            elif parts[0] not in plain and parts[0] not in {"screen"}:
                if parts[0] not in {"bar_top", "bar_bottom"}:
                    bad(f"{i}: show {parts[0]} —— 没有 image 定义")

        # scene 的图
        m = re.match(r"^scene\s+(\w+)", st)
        if m:
            name = m.group(1)
            if name not in plain and name != "black":
                bad(f"{i}: scene {name} —— 没有 image 定义")

        # jump 目标
        m = re.match(r"^jump\s+(\w+)", st)
        if m and m.group(1) not in labels:
            bad(f"{i}: jump {m.group(1)} —— 没有这个 label")

    # ---------- 5. sheet.json 完整性
    manifest = json.loads(SHEET.read_text(encoding="utf-8"))
    frames = set()
    for k in manifest["frames"]:
        g, f = k.split("/")
        frames.add((g, f))
    # 反向：注册了但表里没有
    for d in defined:
        if d and d[0] == "idimya" and len(d) == 3:
            if (d[1], d[2]) not in frames:
                bad(f"image idimya {d[1]} {d[2]} —— sheet.json 里没有这一格（注册块过期，重跑 build_sprites）")

    # ---------- 汇总
    print(f"剧本 {len(lines)} 行 · image {len(defined)} 个 · label {len(labels)} 个 · 立绘格 {len(frames)} 个")
    if problems:
        print(f"\n发现 {len(problems)} 个问题：")
        for p in problems:
            print("  ✗", p)
        return 1
    print("✅ 静态检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
