#!/usr/bin/env python3
"""
build_seat.py —— 坐姿立绘资产

为什么需要这个脚本
------------------
定妆立绘（sheet.png 的每一格）都是**站姿全身**。bistro 那一章她明明是坐着的，
过去一直靠「前景桌面层 table_front 挡住腰以下」来假装 —— 用户一眼看穿：
桌沿之下依旧是站姿（腿直、没有膝盖透视、手垂在身侧）。
hack 骗不过眼睛，只能真做一张坐姿。

素材
----
assets/sprites/idimya/seat_src.png        坐姿基准表情（calm）
assets/sprites/idimya/seat_expr_*.png     同一张坐姿图的其余表情

★ 这张坐姿图是**按定妆图重绘**的：同一张脸、同一套衣服、同一支笔触。
  所以这里**不再把定妆脸贴上去**。早期版本贴过，结果就是两张脸互相错位、
  出现"重影/四只眼"——正是用户明令禁止的"部件重合"。
  只有一张脸，就不可能有重影。

要做的只有几何：
  1. 黑底转透明
  2. 按「头部」量到的尺度缩放，让她的头和 sheet 里的头一样大
     （不缩放的话，切成坐姿近景时她会突然变成"头小身子大"）
  3. 统一平移：头顶对齐、身体中轴对齐
  4. 所有表情 + 眨眼补丁共用同一个裁切框 → 切表情绝不跳位
  5. 写 seat.json 供引擎 / Ren'Py 共用

用法：python3 tools/build_seat.py
"""

import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "sprites" / "idimya"
OUT = ROOT / "icancook" / "game" / "images" / "idimya"
SHEET = OUT / "sheet.png"

BASE_FACES = [
    ("calm", "seat_src.png"),
    ("amused", "seat_expr_amused.png"),
    ("sly", "seat_expr_sly.png"),
    ("suspicious", "seat_expr_suspicious.png"),
    ("hungry", "seat_expr_hungry.png"),
    ("smile_soft", "seat_expr_smile_soft.png"),
    ("eyes_down", "seat_expr_eyes_down.png"),
    ("laugh", "seat_expr_laugh.png"),
]
# flat = calm（转场/留白时的"不给表情"，和 sheet 里 base/flat 的处理一致）
ALIASES = {"flat": "calm"}

FUZZ = "11%"
BEAUTY = ["-unsharp", "0x1.3+0.9+0.02",
          "-modulate", "100,116,100",
          "-brightness-contrast", "1x7"]


def run(*args):
    subprocess.run(args, check=True, capture_output=True)


def size(path):
    w, h = subprocess.run(["identify", "-format", "%w %h", str(path)],
                          capture_output=True, text=True, check=True).stdout.split()
    return int(w), int(h)


def to_alpha(src, dst):
    run("convert", str(src), "-fuzz", FUZZ, "-transparent", "black",
        "-alpha", "set", str(dst))


def head_metrics(path):
    """量「头」：头顶那一行 + 头部最宽处（肩线之上）。

    为什么用头而不是眼睛：厚涂图的瞳孔边界是糊的，用最暗点找眼，
    在不同图上能差出 20~30px，缩放比直接偏 10%（真机就是重影）。
    头部轮廓是硬的，误差只有 1~2px。
    """
    w, h = size(path)
    raw = subprocess.run(["convert", str(path), "-alpha", "extract",
                          "-depth", "8", "gray:-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(h, w).astype(np.float32) / 255.0
    op = a > 0.5
    top = int(np.where(op.any(1))[0].min())
    # 头部 = 头顶往下 340px（肩线在更下面），取其中最宽的一行的一半作为"头宽"
    best_w, best_y, best_cx = 0, top, w / 2
    for y in range(top, min(h, top + 340)):
        xs = np.where(op[y])[0]
        if len(xs) < 5:
            continue
        width = xs.max() - xs.min()
        if width > best_w:
            best_w, best_y, best_cx = width, y, (xs.max() + xs.min()) / 2.0
    return {"top": int(top), "w": int(best_w), "y": int(best_y), "cx": float(best_cx)}


def sheet_head():
    """定妆图的头部尺度：取 sheet 的第一格"""
    cell = OUT / "_cell0.png"
    run("convert", str(SHEET), "-crop", "598x1360+0+0", "+repage", str(cell))
    tmp = OUT / "_cell0_a.png"
    to_alpha(cell, tmp)
    m = head_metrics(tmp)
    cell.unlink(missing_ok=True)
    tmp.unlink(missing_ok=True)
    return m


def main():
    missing = [f for _, f in BASE_FACES if not (SRC / f).exists()]
    if missing:
        print("  !! 缺少坐姿源图：", ", ".join(missing))
    faces = [(n, f) for n, f in BASE_FACES if (SRC / f).exists()]
    if not faces:
        raise SystemExit("没有坐姿源图")

    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "_seat_tmp"
    tmp.mkdir(exist_ok=True)

    ref_h = sheet_head()
    to_alpha(SRC / faces[0][1], tmp / "ref.png")
    src_h = head_metrics(tmp / "ref.png")
    s = ref_h["w"] / src_h["w"]
    print(f"头部最宽：定妆 {ref_h['w']}px / 坐姿 {src_h['w']}px → 缩放 {s:.4f}")

    # 缩放到与定妆图同尺度后，头顶对齐：让 seat 的头顶落在 canvas 的 PAD_TOP 行
    PAD_TOP, PAD_X = 60, 60
    w0, h0 = size(tmp / "ref.png")
    sw, sh = int(round(w0 * s)), int(round(h0 * s))
    CW, CH = int(round(w0 * s)) + PAD_X * 2, int(round(h0 * s)) + PAD_TOP * 2

    # 头部中心横向对齐画布中线
    off_x = int(round(CW / 2 - src_h["cx"] * s))
    off_y = int(round(PAD_TOP - src_h["top"] * s))

    frames = {}
    for name, fn in faces:
        a = tmp / f"a_{name}.png"
        to_alpha(SRC / fn, a)
        scaled = tmp / f"s_{name}.png"
        run("convert", str(a), "-filter", "Lanczos", "-resize", f"{sw}x{sh}", str(scaled))
        out = tmp / f"c_{name}.png"
        run("convert", "-size", f"{CW}x{CH}", "xc:none", "(", str(scaled), ")",
            "-geometry", f"{off_x:+d}{off_y:+d}", "-compose", "over", "-composite", str(out))
        run("convert", str(out), *BEAUTY, str(out))
        frames[name] = out
        print(f"  合成 seat/{name}")

    # 眨眼：坐姿组**不做**闭眼补丁。
    # blink_closed.png 是站姿那张的闭眼差分，几何与坐姿图不同；
    # 强行缩放贴过去，眼皮会落在她的脖子上（真机截图出现过）。
    # 引擎里座位场景直接关掉眨眼层，比"叠一个错位的眼皮"安全得多。

    # 统一裁切框（所有表情 + 眨眼 + flat 别名共用）
    paths = list(frames.values())
    left = top = 10 ** 9
    right = bottom = -10 ** 9
    for p in paths:
        out = subprocess.run(["convert", str(p), "-trim", "-format", "%wx%h%O", "info:"],
                             capture_output=True, text=True, check=True).stdout.strip()
        wh, off = out.split("+", 1) if "+" in out else (out, "0+0")
        w, h = (int(v) for v in wh.split("x"))
        x, y = (int(v) for v in off.split("+"))
        left, top = min(left, x), min(top, y)
        right, bottom = max(right, x + w), max(bottom, y + h)
    cw, ch = right - left, bottom - top
    print(f"统一裁切框 {cw}x{ch}+{left}+{top}")

    manifest = {"cell": {"w": cw, "h": ch},
                "head": {"w": ref_h["w"], "top": 0},
                "frames": {}}
    for name, p in frames.items():
        out = OUT / f"seat__{name}.png"
        run("convert", str(p), "-crop", f"{cw}x{ch}+{left}+{top}", "+repage", str(out))
        manifest["frames"][name] = {"file": out.name, "w": cw, "h": ch}
    for alias, target in ALIASES.items():
        manifest["frames"][alias] = manifest["frames"][target]


    (OUT / "seat.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
    for f in tmp.glob("*"):
        f.unlink(missing_ok=True)
    tmp.rmdir()
    print(f"完成：{len(frames)} 个表情（+{len(ALIASES)} 别名）→ {OUT}/seat.json")


if __name__ == "__main__":
    main()
