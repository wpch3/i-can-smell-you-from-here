#!/usr/bin/env python3
"""
build_sprites.py — 把 AI 出的立绘源图加工成引擎可用的资产

输入：assets/sprites/idimya/*.png（纯黑底、768×1376）
输出：
  icancook/game/images/idimya/
      sheet.png            5 张表情差分拼成的精灵表（统一裁切，坐标写进 sheet.json）
      sheet.json           每格坐标 + 尺寸，供网页引擎与 Ren'Py 共用
      blink_patch.png      只有眼睛区域可见的透明补丁（用于叠加眨眼）
      (单张透明图也保留一份，便于以后手工修)

做法：
  1. 黑底转透明（fuzz 容差可调），所有差分共用同一裁切框，保证切换表情不跳位
  2. 眨眼：从 blink_closed 里取出眼部横带，做羽化遮罩，其余全透明
  3. 拼表：横向排列，写入坐标清单

用法：python3 tools/build_sprites.py
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "sprites" / "idimya"
OUT = ROOT / "icancook" / "game" / "images" / "idimya"

# 造型组：每套服装+发型 = 一组表情差分。剧情里用 `show idimya <造型>/<表情>` 调用。
# 顺序即精灵表顺序；每组 512 宽的格位，方便引擎端直接按列号索引。
GROUPS = [
    # 造型名        基准图                表情后缀 → 文件
    ("base",       "base_v1.png", [
        ("calm",       None),
        ("amused",     "expr_amused.png"),
        ("sly",        "expr_sly.png"),
        ("suspicious", "expr_suspicious.png"),
        ("hungry",     "expr_hungry.png"),
        ("smile_soft", "expr_smile_soft.png"),
        ("eyes_down",  "expr_eyes_down.png"),
        ("laugh",      "expr_laugh.png"),
    ]),
    ("apron",      "outfit_apron.png", [
        ("calm",     None),
        ("amused",   "expr_amused.png"),
        ("smile_soft","expr_smile_soft.png"),
        ("sly",      "expr_sly.png"),
    ]),
    ("coat",       "outfit_coat.png", [
        ("calm",     None),
        ("suspicious","expr_suspicious.png"),
        ("sly",      "expr_sly.png"),
    ]),
    ("ponytail",   "hair_ponytail.png", [
        ("calm",     None),
        ("amused",   "expr_amused.png"),
        ("hungry",   "expr_hungry.png"),
    ]),
]

BLINK_SRC = "blink_closed.png"
# 眼部横带（源图坐标 768×1376，实测位）
EYE_BOX = "300x100+235+235"
FUZZ = "11%"


def run(*args):
    subprocess.run(args, check=True, capture_output=True)


def alpha(src: Path, dst: Path):
    """黑底 → 透明"""
    run("convert", str(src), "-fuzz", FUZZ, "-transparent", "black", "-alpha", "set", str(dst))


def trimbox(paths):
    """取所有图的并集裁切框（用 -trim 的几何信息推算）"""
    boxes = []
    for p in paths:
        out = subprocess.run(
            ["convert", str(p), "-trim", "-format", "%wx%h%O", "info:"],
            capture_output=True, text=True, check=True).stdout.strip()
        w, rest = out.split("x", 1)
        h, rest = rest.split("+", 1) if "+" in rest else rest.split("-", 1)
        x, y = rest.split("+") if "+" in out else ("0", "0")
        boxes.append((int(w), int(h), int(x), int(y)))
    left = min(b[2] for b in boxes)
    top = min(b[3] for b in boxes)
    right = max(b[2] + b[0] for b in boxes)
    bottom = max(b[3] + b[1] for b in boxes)
    return left, top, right - left, bottom - top


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "_tmp"
    tmp.mkdir(exist_ok=True)

    # 1) 每个 (造型, 表情) 生成透明图
    jobs = []          # (造型, 表情, 透明图路径)
    for group, base_file, faces in GROUPS:
        for face, fn in faces:
            src = SRC / (fn or base_file)
            if not src.exists():
                print(f"  !! 缺少源图，跳过：{src.name}")
                continue
            dst = tmp / f"{group}__{face}.png"
            alpha(src, dst)
            jobs.append((group, face, dst))

    if not jobs:
        raise SystemExit("没有可用源图")

    # 2) 所有图共用并集裁切框，保证切换造型/表情都不跳位
    l, t, w, h = trimbox([j[2] for j in jobs] + [tmp / "blink.png"]
                         if (tmp / "blink.png").exists() else [j[2] for j in jobs])
    w += w % 2
    h += h % 2
    print(f"统一裁切框: {w}x{h}+{l}+{t}")

    frames = {}
    order = []
    for group, face, path in jobs:
        name = f"{group}/{face}"
        run("convert", str(path), "-crop", f"{w}x{h}+{l}+{t}", "+repage",
            str(OUT / f"{group}__{face}.png"))
        frames[name] = None
        order.append(name)

    # 3) 拼表（横向，按 order 顺序）
    run("convert", *[str(OUT / (n.replace("/", "__") + ".png")) for n in order],
        "+append", str(OUT / "sheet.png"))

    cols = len(order)
    manifest = {
        "image": "sheet.png",
        "cell": {"w": w, "h": h},
        "frames": {n: [i * w, 0, w, h] for i, n in enumerate(order)},
        "blink_patch": "blink_patch.png",
        "groups": {g: [f for (gg, f, _) in
                       [(x[0], x[1], None) for x in jobs] if gg == g]
                   for g, _, _ in GROUPS},
    }

    # 4) 眨眼补丁
    blink_src = SRC / BLINK_SRC
    if blink_src.exists():
        eye_png = tmp / "eye_raw.png"
        run("convert", str(blink_src), "-fuzz", FUZZ, "-transparent", "black",
            "-crop", EYE_BOX, "+repage", str(eye_png))
        info = subprocess.run(["identify", "-format", "%w %h", str(eye_png)],
                              capture_output=True, text=True, check=True).stdout.split()
        ew, eh = int(info[0]), int(info[1])
        mask = tmp / "eye_mask.png"
        run("convert", "-size", f"{ew}x{eh}", "xc:black",
            "-fill", "white", "-draw", f"roundrectangle 6,6 {ew-7},{eh-7} 12,12",
            "-blur", "0x6", str(mask))
        patch = tmp / "eye_patch.png"
        run("convert", str(eye_png), str(mask), "-alpha", "off",
            "-compose", "CopyOpacity", "-composite", str(patch))
        run("convert", "-size", f"{w}x{h}", "xc:none", "(", str(patch), ")",
            "-geometry", f"+{235 - l}+{235 - t}", "-compose", "over", "-composite",
            str(OUT / "blink_patch.png"))

    # 5) 单张成品：默认删除（精灵表已够用，省 20MB）；需要时加 --singles
    if "--singles" in sys.argv:
        for name in order:
            src = OUT / (name.replace("/", "__") + ".png")
            dst = OUT / (name.replace("/", "_") + ".png")
            src.replace(dst)
    else:
        for name in order:
            (OUT / (name.replace("/", "__") + ".png")).unlink(missing_ok=True)

    (OUT / "sheet.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                                    encoding="utf-8")

    for p in tmp.glob("*.png"):
        p.unlink()
    tmp.rmdir()

    print(f"共 {cols} 格：")
    for i, n in enumerate(order):
        print(f"  [{i:2d}] {n}")
    print("产物：")
    for f in sorted(OUT.glob("*")):
        print(f"  {f.name:34s} {f.stat().st_size // 1024:6d} KB")


if __name__ == "__main__":
    main()
