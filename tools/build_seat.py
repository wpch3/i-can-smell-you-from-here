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

# 闭眼差分：单独一张源图（和 seat_src 同一构图，手/衣服/头发完全一致，只有眼睛不同）
CLOSED_SRC = "seat_expr_closed.png"
# 眼睛只可能出现在这个横带里（seat_src 坐标 768x1376）。实测：
# 「睁眼 vs 闭眼」的差异像素 1958 个，全部落在 y=151..239 / x=295..478
EYE_BAND = (150, 240)
# 蒙版羽化：眼皮阴影、睫毛要整块盖住，否则闭眼后还留着睁眼的眼角
EYE_FEATHER = "0x5"

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


def eye_mask(open_png, closed_png):
    """睁眼 / 闭眼逐像素求差 → 只有「眼皮那一块」为白的蒙版（源图坐标系）。

    为什么不用矩形横带：矩形会把鼻子、脸颊、围巾一起显影，
    眨眼时脸中央浮出一个方块 —— 这是本项目早期真机踩过的坑。
    """
    w, h = size(open_png)
    raw_a = subprocess.run(["convert", str(open_png), "-depth", "8", "rgb:-"],
                           capture_output=True, check=True).stdout
    raw_b = subprocess.run(["convert", str(closed_png), "-depth", "8", "rgb:-"],
                           capture_output=True, check=True).stdout
    a = np.frombuffer(raw_a, np.uint8).reshape(h, w, 3).astype(np.int16)
    b = np.frombuffer(raw_b, np.uint8).reshape(h, w, 3).astype(np.int16)
    diff = np.abs(a - b).max(2)
    mask = diff > 14
    band = np.zeros_like(mask)
    band[EYE_BAND[0]:EYE_BAND[1], :] = True
    mask &= band
    if mask.sum() < 200:
        print("  !! 闭眼差异像素太少，放弃眨眼补丁")
        return None
    # 膨胀：眼皮阴影 / 睫毛要整块盖住，否则闭眼后还留着睁眼的眼角
    from numpy.lib.stride_tricks import sliding_window_view
    for _ in range(3):
        pad = np.pad(mask.astype(np.uint8), 2, mode="edge")
        mask = sliding_window_view(pad, (5, 5)).max(axis=(2, 3)) > 0
    mask &= band
    mask_png = closed_png.with_name(closed_png.stem + "_mask.png")
    subprocess.run(["convert", "-size", f"{w}x{h}", "-depth", "8", "gray:-", str(mask_png)],
                   input=(mask.astype(np.uint8) * 255).tobytes(), check=True)
    blurred = closed_png.with_name(closed_png.stem + "_mask_b.png")
    run("convert", str(mask_png), "-blur", EYE_FEATHER, str(blurred))
    print(f"  闭眼蒙版 {int(mask.sum())} px")
    return blurred


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

    # 闭眼补丁：用**坐姿自己的**闭眼差分做，不再借用站姿那张。
    # 做法和 build_sprites.py 一致：睁眼图与闭眼图逐像素求差 → 得到"眼皮"蒙版，
    # 只把闭着的眼皮显影出来。矩形横带会在脸上留方块，这一条真机验证过。
    blink = None
    if (SRC / CLOSED_SRC).exists():
        blink = tmp / "c_blink.png"
        to_alpha(SRC / CLOSED_SRC, tmp / "closed_a.png")
        run("convert", str(tmp / "closed_a.png"), "-filter", "Lanczos",
            "-resize", f"{sw}x{sh}", str(tmp / "closed_s.png"))
        # 和一张"睁眼基准"叠一次，保证闭眼图里除了眼皮没有别的差异
        run("convert", "-size", f"{CW}x{CH}", "xc:none",
            "(", str(tmp / "closed_s.png"), ")",
            "-geometry", f"{off_x:+d}{off_y:+d}", "-compose", "over",
            "-composite", str(blink))
        mask = eye_mask(tmp / "ref.png", tmp / "closed_a.png")
        if mask is not None:
            # ★ 蒙版必须和补丁在同一坐标系。
            #   蒙版是在**源图**尺度（768x1376）上算的，补丁在**画布**尺度（CWxCH）。
            #   直接 CopyOpacity 会因尺寸不同而被拉伸/错位 —— 眨眼时眼皮落在鼻子上。
            #   正确姿势：蒙版按同一缩放 + 同一偏移放到画布上，再当 alpha 用。
            mask_scaled = tmp / "mask_s.png"
            run("convert", str(mask), "-filter", "Lanczos", "-resize", f"{sw}x{sh}",
                str(mask_scaled))
            mask_canvas = tmp / "mask_c.png"
            run("convert", "-size", f"{CW}x{CH}", "xc:black", "(", str(mask_scaled), ")",
                "-geometry", f"{off_x:+d}{off_y:+d}", "-compose", "over",
                "-composite", str(mask_canvas))
            run("convert", str(blink), str(mask_canvas), "-alpha", "off",
                "-compose", "CopyOpacity", "-composite", str(blink))
            run("convert", str(blink), *BEAUTY, str(blink))
    else:
        print("  !! 缺少闭眼源图 seat_expr_closed.png，坐姿不眨眼")

    # 统一裁切框（所有表情 + 眨眼 + flat 别名共用）
    paths = list(frames.values()) + ([blink] if blink else [])
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

    # 预合成的「闭眼整帧」：Ren'Py 那边没有分层叠加，
    # 直接在 ATL 里切换「睁眼整帧 / 闭眼整帧」最稳 ——
    # 不会出现半透明叠加、也不会残留睁眼（本项目早期在网页端踩过的两个坑）。
    if blink:
        for name, p in frames.items():
            out_closed = OUT / f"seat__{name}_closed.png"
            run("convert", str(p), "(", str(blink), ")", "-compose", "over",
                "-composite", "-crop", f"{cw}x{ch}+{left}+{top}", "+repage",
                str(out_closed))
            manifest["frames"][name]["closed"] = out_closed.name

    if blink:
        out_blink = OUT / "seat__blink.png"
        run("convert", str(blink), "-crop", f"{cw}x{ch}+{left}+{top}", "+repage", str(out_blink))
        manifest["blink"] = {"file": out_blink.name, "w": cw, "h": ch}


    (OUT / "seat.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
    for f in tmp.glob("*"):
        f.unlink(missing_ok=True)
    tmp.rmdir()
    print(f"完成：{len(frames)} 个表情（+{len(ALIASES)} 别名）→ {OUT}/seat.json")


if __name__ == "__main__":
    main()
