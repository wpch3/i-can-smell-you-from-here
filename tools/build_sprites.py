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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "sprites" / "idimya"
OUT = ROOT / "icancook" / "game" / "images" / "idimya"

# 表情 → 源文件（顺序即精灵表顺序）
EXPRESSIONS = [
    ("calm", "base_v1.png"),
    ("amused", "expr_amused.png"),
    ("sly", "expr_sly.png"),
    ("suspicious", "expr_suspicious.png"),
    ("hungry", "expr_hungry.png"),
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

    # 1) 透明化
    cut = {}
    for name, fn in EXPRESSIONS + [("blink", BLINK_SRC)]:
        src = SRC / fn
        if not src.exists():
            raise SystemExit(f"缺少源图：{src}")
        dst = tmp / f"{name}.png"
        alpha(src, dst)
        cut[name] = dst

    # 2) 统一裁切
    l, t, w, h = trimbox(list(cut.values()))
    # 像素取偶数，避免缩放时半像素
    w += w % 2
    h += h % 2
    print(f"统一裁切框: {w}x{h}+{l}+{t}")

    cells = []
    for i, (name, _) in enumerate(EXPRESSIONS):
        dst = OUT / f"{name}.png"
        run("convert", str(cut[name]), "-crop", f"{w}x{h}+{l}+{t}", "+repage", str(dst))
        cells.append({"name": name, "x": i * w, "y": 0, "w": w, "h": h})

    # 3) 眨眼补丁：只保留眼部横带，做羽化
    eye_png = tmp / "eye_raw.png"
    run("convert", str(SRC / BLINK_SRC), "-crop", EYE_BOX, "+repage", str(eye_png))
    # 羽化用一张模糊的白色圆角矩形做遮罩
    out_info = subprocess.run(["identify", "-format", "%w %h", str(eye_png)],
                              capture_output=True, text=True, check=True).stdout.split()
    ew, eh = int(out_info[0]), int(out_info[1])
    mask = tmp / "eye_mask.png"
    run("convert", "-size", f"{ew}x{eh}", "xc:black",
        "-fill", "white", "-draw", f"roundrectangle 6,6 {ew-7},{eh-7} 12,12",
        "-blur", "0x6", str(mask))
    patch = tmp / "eye_patch.png"
    run("convert", str(eye_png), str(mask), "-alpha", "off",
        "-compose", "CopyOpacity", "-composite", str(patch))
    # 合成到全画布，位置与裁切框对齐
    run("convert", "-size", f"{w}x{h}", "xc:none",
        "(", str(patch), ")",
        "-geometry", f"+{235 - l}+{235 - t}",
        "-compose", "over", "-composite",
        str(OUT / "blink_patch.png"))

    # 4) 拼精灵表
    run("convert", *[str(OUT / f"{n}.png") for n, _ in EXPRESSIONS],
        "+append", str(OUT / "sheet.png"))

    manifest = {
        "image": "sheet.png",
        "cell": {"w": w, "h": h},
        "frames": {c["name"]: [c["x"], c["y"], c["w"], c["h"]] for c in cells},
        "blink_patch": {"file": "blink_patch.png", "w": w, "h": h},
    }
    (OUT / "sheet.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                                    encoding="utf-8")

    # 5) 清理临时
    for p in tmp.glob("*.png"):
        p.unlink()
    tmp.rmdir()

    print("表情:", ", ".join(n for n, _ in EXPRESSIONS))
    for f in sorted(OUT.glob("*")):
        print(f"  {f.name:20s} {f.stat().st_size // 1024:6d} KB")


if __name__ == "__main__":
    main()
