#!/usr/bin/env python3
"""
build_props.py — 生成「遮挡道具」层（前景桌面），让站姿立绘能正确地"坐"在桌后

## 为什么需要这个

我们的立绘（sheet.png 的每一格）是**站姿全身**：头到小腿，底边直接切在膝盖下。
引擎原来把她当成「站在屏幕最前面、底边贴屏幕底」来摆 —— 于是：

  · 人比背景里那张桌子高一大截（她的腰在桌沿之上，腿穿过整张桌面）
  · 头顶被画面上沿切掉
  · 她的脚"站"在桌子正中，等于人浮在背景图层外面

而仓库里的定稿 `assets/concept/key-visual-official.png` 早就是对的：
她是**坐**在桌后，桌面把腰以下全部挡住。

要复现定稿，缺的不是新立绘，而是**一块"桌面在立绘前面"的图层**。
这个脚本从 bg_bistro.jpg 里把「桌沿以下的前景」抠成一张带透明通道的 PNG：

    icancook/game/images/table_front.png   1920x1080 RGBA

引擎里 show 在立绘**之上**、遮幅**之下**，桌面就自然把她腰部截断 ——
视觉上她坐在桌后，实际上立绘一帧没改。

## 桌沿在哪：从图里量，不靠眼估

桌沿是一道很清楚的亮/暗边界（暗的木墙 → 亮的桌面）。脚本逐列向下扫，
取"亮度陡增且上方持续更暗"的第一行，然后：

  1. 中值滤波剔掉离群点（蜡烛、笔记本、她的轮廓都会干扰）
  2. 二次曲线拟合（圆桌在透视里就是抛物线）→ 全宽都能拿到一个平滑的 y
  3. 再按列做局部 ±6px 精修，跟住真实笔触边缘

实测残差中位 1.8px，肉眼看不出锯齿。

## 蜡烛是例外

烛火是**高于桌沿**的（火苗从桌面往上窜），按桌沿切会把火苗切掉。
尝试记录（都失败过，别再走一遍）：

  1. 方块抬高  → 画面上出现一个看得见的矩形接缝
  2. 高斯鼓包  → 变成她胸前一座黑色小山丘，比切掉火苗还糟
  3. 最终：不抬桌沿，而是**把蜡烛和火苗本身抠出来**当额外的 alpha。
     烛火是全图最亮的东西（lum≈200），周围是近乎纯黑的暗部（lum<35），
     亮度键控能干净地分离出来，边缘天然贴着真实轮廓。

## 用法

    python3 tools/build_props.py            # 生成/覆盖 table_front.png
    python3 tools/build_props.py --check    # 只检查桌子层是否存在且尺寸对

依赖：ImageMagick 6（convert）+ numpy。
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BG = ROOT / "icancook" / "game" / "images" / "bg_bistro.jpg"
OUT = ROOT / "icancook" / "game" / "images" / "table_front.png"

W, H = 1920, 1080

# 蜡烛/烛火：火苗在桌沿之上，按桌沿切会把火苗切掉。
# 所以在蜡烛位置把边界"抬起来"，而且必须是**平滑的鼓包**，不能是方块 ——
# 方块会在画面上留下一个看得见的矩形接缝（试过，一眼假）。
# 实测：火苗尖 x≈820 y≈806，烛身 x 721..887。抬到 790 刚好把火苗整个包住，
# 再高就会连她肩膀一起被"抬"进遮挡层，把她的手臂切掉一条。
CANDLE_RECT = (690, 770, 260, 300)   # x, y, w, h —— 只为限制键控范围
KEY_LO, KEY_HI = 60.0, 110.0         # 亮度键控的软阈值

# 扫描参数
SEARCH_FROM = 600        # 桌沿不可能出现在这行以上
RISE = 9                 # 亮度陡增阈值（0-255）
MIN_LUM = 38             # 太暗的"边缘"是噪声
ABOVE_DARK = 7           # 上方均值必须比边缘暗这么多


def read_ppm(path):
    import numpy as np
    f = open(path, "rb")
    if f.readline().strip() != b"P6":
        raise SystemExit("只认 P6 PPM")
    line = f.readline()
    while line.startswith(b"#"):
        line = f.readline()
    w, h = map(int, line.split())
    f.readline()
    return np.frombuffer(f.read(w * h * 3), dtype=np.uint8).reshape(h, w, 3).astype(float)


def measure_edge():
    """返回长度 W 的数组：每列桌沿的 y"""
    import numpy as np

    with tempfile.TemporaryDirectory() as td:
        ppm = Path(td) / "bg.ppm"
        subprocess.run(["convert", str(BG), str(ppm)], check=True)
        lum = read_ppm(ppm).mean(axis=2)

    raw = {}
    for x in range(W):
        col = lum[:, x]
        for y in range(SEARCH_FROM, H - 6):
            if (col[y] - col[y - 6] > RISE and col[y] > MIN_LUM
                    and col[y - 16:y - 2].mean() < col[y] - ABOVE_DARK):
                raw[x] = y
                break

    xs = np.array(sorted(raw), dtype=float)
    ys = np.array([raw[int(x)] for x in xs], dtype=float)
    keep = np.ones(len(xs), bool)
    # 迭代拟合 + 去离群（蜡烛火焰、笔记本、她的身体都会给出假边缘）
    for _ in range(8):
        coef = np.polyfit(xs[keep], ys[keep], 2)
        resid = np.abs(np.polyval(coef, xs) - ys)
        keep = resid < max(6.0, float(np.percentile(resid[keep], 88)))
    coef = np.polyfit(xs[keep], ys[keep], 2)
    fit = np.polyval(coef, np.arange(W))
    print(f"  拟合二次曲线 {coef[0]:.3e} x^2 + {coef[1]:.4f} x + {coef[2]:.1f}"
          f"（样本 {int(keep.sum())}/{len(xs)}）")

    # 局部精修：在拟合值附近 ±7px 找真实边缘
    edge = fit.copy()
    for x in range(W):
        y0 = int(max(SEARCH_FROM, fit[x] - 7))
        y1 = int(min(H - 4, fit[x] + 8))
        col = lum[:, x]
        best, bestd = None, 3.0
        for y in range(y0, y1):
            d = col[y] - col[y - 4]
            if d > bestd:
                best, bestd = y, d
        if best is not None:
            edge[x] = best

    # 中值平滑，避免逐列抖动
    sm = edge.copy()
    for x in range(2, W - 2):
        sm[x] = float(np.median(edge[x - 2:x + 3]))
    edge = sm

    return edge, lum


def build():
    import numpy as np

    print(":: build_props.py — 前景桌面遮挡层")
    print(f"  源背景 {BG.relative_to(ROOT)}")
    edge, lum = measure_edge()

    # 遮罩：桌沿以下不透明，以上全透明。
    # 关键是**解析式抗锯齿**（y 方向 1px 线性过渡），不要 blur+threshold ——
    # threshold 会切出一圈半透明的硬边，在深色画面上就是一道可见的接缝。
    yy = np.arange(H)[:, None].astype(float)
    alpha = np.clip(yy - edge[None, :] + 0.5, 0.0, 1.0)

    # 蜡烛 + 火苗：在限定矩形内按亮度键控，让它单独露在桌沿之上
    rx, ry, rw, rh = CANDLE_RECT
    patch = lum[ry:ry + rh, rx:rx + rw]
    key = np.clip((patch - KEY_LO) / (KEY_HI - KEY_LO), 0.0, 1.0)
    sub = alpha[ry:ry + rh, rx:rx + rw]
    alpha[ry:ry + rh, rx:rx + rw] = np.maximum(sub, key)

    mask = (alpha * 255.0 + 0.5).astype(np.uint8)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        pgm = td / "mask.pgm"
        hdr = f"P5\n{W} {H}\n255\n".encode()
        pgm.write_bytes(hdr + mask.tobytes())

        subprocess.run([
            "convert", str(BG),
            "(", str(pgm), ")",
            "-alpha", "off", "-compose", "CopyOpacity", "-composite",
            "-define", "png:compression-level=9",
            str(OUT),
        ], check=True)

    # 统计一下遮挡比例，方便确认不是"糊了一层全屏"
    covered = float(mask.mean() / 255)
    print(f"  ✅ {OUT.relative_to(ROOT)}  {W}x{H}  遮挡面积 {covered*100:.1f}%")
    print(f"     桌沿 y: 左 {edge[0]:.0f} · 中 {edge[W//2]:.0f} · 右 {edge[-1]:.0f}"
          f"（蜡烛用亮度键控单独保留：{CANDLE_RECT}）")

    # 自检：把这一层叠回背景，必须和原背景**逐像素一致**。
    # 只要 RMSE 不为 0，就说明透明区/不透明区之间露出了缝 ——
    # 在深色画面上那是一条一眼可见的亮边。这一步是防回归的硬指标。
    with tempfile.TemporaryDirectory() as td:
        merged = Path(td) / "merged.png"
        subprocess.run(["convert", str(BG), str(OUT), "-compose", "over",
                        "-composite", str(merged)], check=True)
        diff = subprocess.run(["compare", "-metric", "RMSE", str(BG), str(merged), "null:"],
                              capture_output=True, text=True).stderr.strip()
    print(f"     接缝自检 RMSE={diff}（必须是 0：叠回背景应与原图逐像素一致）")


def check():
    if not OUT.exists():
        print(f"✗ 缺少 {OUT.relative_to(ROOT)}，跑 python3 tools/build_props.py")
        return 1
    info = subprocess.run(["identify", "-format", "%wx%h %[channels]", str(OUT)],
                          capture_output=True, text=True, check=True).stdout
    size, chans = info.split()
    ok = size == f"{W}x{H}" and "a" in chans
    print(("✅ " if ok else "✗ ") + f"table_front.png {size} {chans}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    # Windows 控制台默认 GBK，打印中文会抛 UnicodeEncodeError，看起来像"检查失败"
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if a.check:
        raise SystemExit(check())
    build()


if __name__ == "__main__":
    main()
