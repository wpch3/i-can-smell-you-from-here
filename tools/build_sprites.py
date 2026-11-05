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
  2. 眨眼：把 blink_closed 与 base_v1 逐像素求差得到"眼睛蒙版"，
     只显影闭着的眼皮（不是矩形横带——那会在脸上留方块）
  3. 拼表：横向排列，写入坐标清单

用法：python3 tools/build_sprites.py
"""

import json
import subprocess
import sys

import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "sprites" / "idimya"
OUT = ROOT / "icancook" / "game" / "images" / "idimya"

# 造型组：每套服装+发型 = 一组表情差分。剧情里用 `show idimya <造型>/<表情>` 调用。
#
# ★ 脸的唯一来源是 base_v1.png（定妆脸）★
#   每套造型的脸都从 base_v1 上「抠下来贴过去」，表情再从对应的 expr_*.png 借。
#   为什么不再用「拿造型图做 img2img 出表情」：
#   每一次 img2img 都会把五官磨平一格 —— 下颌变宽、鼻梁塌成一块、嘴唇失去光泽、
#   皮肤发灰，整张脸比 base 老五六岁。25 格里有 17 格是这样，风格就散了。
#   现在的做法只用一次 AI 生成（base_v1 与本造型定妆图），脸永远只有一张。
GROUPS = [
    # 造型名        底图（衣服/发型）      表情后缀 → 来源图
    ("base",       "base_v1.png", [
        ("calm",       None),
        ("amused",     "expr_amused.png"),
        ("sly",        "expr_sly.png"),
        ("suspicious", "expr_suspicious.png"),
        ("hungry",     "expr_hungry.png"),
        ("smile_soft", "expr_smile_soft.png"),
        ("eyes_down",  "expr_eyes_down.png"),
        ("laugh",      "expr_laugh.png"),
        # 剧本里 `show idimya base flat` 会用（转身/近景留白时的"不给表情"）
        ("flat",       "expr_flat.png"),
    ]),
    # 注意：outfit_apron.png 其实是「蓝吊带」，不是围裙（早期命名遗留）。
    # 真围裙是 apron_flat.png。
    ("apron",      "apron_flat.png", [
        ("calm",     None),
        ("amused",   "expr_amused.png"),
        ("smile_soft","expr_smile_soft.png"),
        ("sly",      "expr_sly.png"),
        ("flat",     None),
    ]),
    ("coat",       "outfit_coat.png", [
        ("calm",     None),
        ("suspicious","expr_suspicious.png"),
        ("sly",      "expr_sly.png"),
        ("flat",     "coat_flat.png"),
    ]),
    ("ponytail",   "hair_ponytail.png", [
        ("calm",     None),
        ("amused",   "expr_amused.png"),
        ("hungry",   "expr_hungry.png"),
        ("sly",      "expr_sly.png"),
        ("flat",     "ponytail_flat.png"),
    ]),
    ("hairup",     "hair_up.png", [
        ("calm",     None),
        ("amused",   "expr_amused.png"),
        ("smile_soft","expr_smile_soft.png"),
        ("sly",      "expr_sly.png"),
    ]),
]

# 脸部合成参数（源图 768x1376 坐标）。实测：所有源图双眼中心 (375,260)、眼距 338。
FACE_SRC = "base_v1.png"
# 下沿必须收在下巴以上：base_v1 的下巴在 y≈355，超过就会把脖子一起贴过去，
# 围裙组的领口会叠成「双丝巾」。
# 左右也要收进来：左边界原先压在左下颌骨上，会切出一条竖直线。
FACE_BOX = (272, 190, 212, 182)      # 只盖脸（含下颌），不碰头发和脖子
FACE_RX, FACE_RY = 0.46, 0.50        # 椭圆半径（占 box 比例）
FACE_BLUR = "0x1e"                   # 贴脸用：中等羽化
# 表情框：从眉线以下开始，避开刘海（早期用 (262,190,232,232) 会把刘海擦掉一块）
EXPR_BOX = (272, 208, 212, 162)      # 眉线以下到下巴，含嘴
EXPR_RX, EXPR_RY = 0.47, 0.52
EXPR_BLUR = "0x34"                   # 贴表情用：重羽化，接缝完全看不出来

# 定妆调色（Beauty pass）：「够不够惊艳」主要卡在这三下
#   unsharp          —— 让眼线和唇锋重新立起来（AI 输出普遍偏软）
#   modulate 116     —— 饱和度 +16%：皮肤透出气血、蓝布不回灰
#   brightness 1x7   —— 抬一点对比：厚涂的高光才"亮得起来"
BEAUTY = ["-unsharp", "0x1.3+0.9+0.02",
          "-modulate", "100,116,100",
          "-brightness-contrast", "1x7"]

BLINK_SRC = "blink_closed.png"
# 眼睛可能出现的位置（源图坐标 768×1376）。闭眼蒙版只允许落在这个横带里。
EX0, EY0, EX1, EY1 = 150, 205, 640, 292
# 表情借用框：比眼睛略大，带上眼周/眉/颧骨的明暗，粘贴后才不"贴片"。
# 所有源图（base / apron / coat / ponytail / hairup / expr_* / blink_closed）
# 出自同一套构图，五官完全对齐，所以可以直接按绝对坐标互贴。
FACE_PATCH = "320x118+225+222"
FACE_FEATHER = 10
# 表情配准：各源图的五官并不是严格同坐标，必须按「双眼中心 + 眼距」归一化。
# 下面这张表是用瞳孔暗点质心实测出来的（单位：768x1376 源图坐标），
# 眼距以 base_v1 为 1.0，换算成 scale；center 是双眼中点。
EYE_ALIGN = {
    "base_v1.png":        {"scale": 1.000, "center": (374.5, 260.2)},
    "outfit_apron.png":   {"scale": 0.999, "center": (374.5, 260.2)},
    "outfit_coat.png":    {"scale": 0.999, "center": (374.5, 260.2)},
    "hair_ponytail.png":  {"scale": 0.929, "center": (376.4, 265.7)},
    "hair_up.png":        {"scale": 0.953, "center": (375.2, 268.2)},
}
# 表情图（expr_* / blink）都以 base_v1 为基准出图
EXPR_ANCHOR = (374.5, 260.2)
FUZZ = "11%"
# 源图尺寸（所有 assets/sprites/idimya/*.png 都是这个规格）
SW_SRC, SH_SRC = 768, 1376


def run(*args):
    subprocess.run(args, check=True, capture_output=True)


def alpha(src: Path, dst: Path):
    """黑底 → 透明"""
    run("convert", str(src), "-fuzz", FUZZ, "-transparent", "black", "-alpha", "set", str(dst))


def _oval_cut(src: Path, box, rx, ry, blur, dst: Path):
    """从 src 里按 box 抠一块，用椭圆羽化遮罩做 alpha（CopyOpacity 才是对的姿势：
    DstIn 需要预先有 alpha 的遮罩，直接用灰度图会得到硬边）。"""
    bx, by, bw, bh = box
    face = dst.with_name(dst.stem + "_face.png")
    mask = dst.with_name(dst.stem + "_mask.png")
    run("convert", str(src), "-crop", f"{bw}x{bh}+{bx}+{by}", "+repage", str(face))
    run("convert", "-size", f"{bw}x{bh}", "xc:black", "-fill", "white",
        "-draw", f"ellipse {bw // 2},{bh // 2} {int(bw * rx)},{int(bh * ry)} 0,360",
        "-blur", blur, str(mask))
    run("convert", str(face), str(mask), "-alpha", "off",
        "-compose", "CopyOpacity", "-composite", str(dst))
    face.unlink(missing_ok=True)
    mask.unlink(missing_ok=True)


def color_match(patch: Path, ref: Path):
    """把 patch 的整体色偏对齐到 ref（同尺寸区域）：逐通道 均值/方差 匹配。

    每套造型的底色并不一样（围裙那张脖子偏红、大衣那张偏冷），
    直接贴上去会有「另一张脸」的割裂感。这一步只调色，不动结构。
    """
    def stats(p):
        out = subprocess.run(["convert", str(p), "-alpha", "off",
                              "-format", "%[fx:mean.r] %[fx:mean.g] %[fx:mean.b] "
                                         "%[fx:standard_deviation.r] "
                                         "%[fx:standard_deviation.g] "
                                         "%[fx:standard_deviation.b]", "info:"],
                             capture_output=True, text=True, check=True).stdout.split()
        return [float(x) for x in out]
    try:
        mp, sp = stats(patch), stats(ref)
    except Exception:
        return
    # 单通道线性变换：p' = (p - m_p) * (s_r / s_p) + m_r
    args = []
    for i, ch in enumerate("RGB"):
        m_p, s_p = mp[i], mp[3 + i]
        m_r, s_r = sp[i], sp[3 + i]
        k = (s_r / s_p) if s_p > 1e-4 else 1.0
        b = m_r - m_p * k
        args += ["-channel", ch, "-evaluate", "multiply", f"{k:.4f}",
                 "-evaluate", "add", f"{b:.4f}"]
    tmp = patch.with_name(patch.stem + "_cm.png")
    run("convert", str(patch), "-colorspace", "sRGB", *args,
        "-channel", "RGBA", str(tmp))
    tmp.replace(patch)


def paste_face(src: Path, canvas: Path):
    """把 base_v1 的定妆脸贴到某套造型的底图上（衣服/发型保持本造型）。"""
    cut = canvas.with_name(canvas.stem + "_fc.png")
    _oval_cut(src, FACE_BOX, FACE_RX, FACE_RY, FACE_BLUR, cut)
    # 不做全局色彩匹配：参考区域包含大量橙发，按均值/方差对齐会把肤色拉爆。
    # 各造型的底色差异（围裙组偏暖）小到可以接受，宁可不动。
    bx, by = FACE_BOX[0], FACE_BOX[1]
    run("convert", str(canvas), "(", str(cut), ")", "-geometry", f"+{bx}+{by}",
        "-compose", "over", "-composite", str(canvas))
    cut.unlink(missing_ok=True)


def paste_expression(expr: Path, canvas: Path):
    """把表情图的「眉线以下」贴到已合成的脸上。框刻意避开刘海，
    否则重羽化会把刘海擦掉一块，一眼假。"""
    cut = canvas.with_name(canvas.stem + "_ec.png")
    _oval_cut(expr, EXPR_BOX, EXPR_RX, EXPR_RY, EXPR_BLUR, cut)
    bx, by = EXPR_BOX[0], EXPR_BOX[1]
    run("convert", str(canvas), "(", str(cut), ")", "-geometry", f"+{bx}+{by}",
        "-compose", "over", "-composite", str(canvas))
    cut.unlink(missing_ok=True)


RENPY_SCRIPT = ROOT / "icancook" / "game" / "script.rpy"
MARK_BEGIN = "## ——— 立绘：从精灵表裁切"
MARK_END = "## ——— 立绘注册结束"


def sync_renpy(manifest):
    """把 sheet.json 里的每格坐标写回 script.rpy 的 `image idimya ... im.Crop(...)`。

    以前这一步是手工跑的，改一次格数就会忘；现在并进构建脚本，永远一致。
    """
    if not RENPY_SCRIPT.exists():
        return
    lines = [MARK_BEGIN + "（坐标由 tools/build_sprites.py 自动生成，勿手改） ———"]
    for name, (x, y, cw, ch) in manifest["frames"].items():
        group, face = name.split("/")
        lines.append(f'image idimya {group} {face} = '
                     f'im.Crop("images/idimya/sheet.png", ({x}, {y}, {cw}, {ch}))')
    lines.append(MARK_END)
    block = "\n".join(lines)

    src = RENPY_SCRIPT.read_text(encoding="utf-8")
    a = src.index(MARK_BEGIN)
    a = src.rindex("\n", 0, a) + 1                 # 行首
    b = src.index(MARK_END) + len(MARK_END)
    b = src.index("\n", b) if "\n" in src[b:] else len(src)
    RENPY_SCRIPT.write_text(src[:a] + block + src[b:], encoding="utf-8")
    print(f"Ren'Py 注册块已同步：{len(manifest['frames'])} 条")


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
            # 画布永远是**本组底图**（发型 / 衣服来自它）
            alpha(SRC / base_file, dst)
            # 非 base 组：先把 base_v1 的定妆脸贴上去
            if base_file != FACE_SRC:
                paste_face(SRC / FACE_SRC, dst)
            # 表情：只借眉线以下那一块，不碰发型和衣服
            if fn:
                alpha(SRC / fn, tmp / "_expr.png")
                paste_expression(tmp / "_expr.png", dst)
                (tmp / "_expr.png").unlink(missing_ok=True)
            # 统一调色（所有格子同一套参数，风格才不会散）
            run("convert", str(dst), *BEAUTY, str(dst))
            jobs.append((group, face, dst))

    if not jobs:
        raise SystemExit("没有可用源图")

    sw, sh = SW_SRC, SH_SRC

    # 2) 所有图共用并集裁切框，保证切换造型/表情都不跳位
    l, t, w, h = trimbox([j[2] for j in jobs] + [tmp / "blink.png"]
                         if (tmp / "blink.png").exists() else [j[2] for j in jobs])
    # 换算到源图坐标系后夹紧：裁切框一旦越界，ImageMagick 会悄悄少给几个像素，
    # 结果就是 sheet 每格 1361 而 sheet.json 写 1362，Ren'Py 的 im.Crop 直接越界。
    info = subprocess.run(["identify", "-format", "%w %h", str(jobs[0][2])],
                          capture_output=True, text=True, check=True).stdout.split()
    sw, sh = int(info[0]), int(info[1])
    w = min(w + w % 2, sw - l)
    h = min(h + h % 2, sh - t)
    w -= w % 2
    h -= h % 2
    print(f"统一裁切框: {w}x{h}+{l}+{t}（源图 {sw}x{sh}）")

    frames = {}
    order = []
    for group, face, path in jobs:
        name = f"{group}/{face}"
        run("convert", str(path), "-crop", f"{w}x{h}+{l}+{t}", "+repage",
            str(OUT / f"{group}__{face}.png"))
        frames[name] = None
        order.append(name)

    # 3) 拼表：多行网格，不做超宽单行。
    #    24 格 × 602 = 14448px，单行虽然还勉强能过，但很多 GPU / 移动端
    #    对 16384 的纹理上限是硬限，再加造型就会炸。固定 GRID_COLS 列。
    GRID_COLS = 6
    rows = (len(order) + GRID_COLS - 1) // GRID_COLS
    manifest_frames = {}
    for i, n in enumerate(order):
        r, c = divmod(i, GRID_COLS)
        manifest_frames[n] = [c * w, r * h, w, h]

    blank = tmp / "_blank.png"
    run("convert", "-size", f"{w}x{h}", "xc:none", str(blank))

    row_files = []
    for r in range(rows):
        cells = [str(OUT / (order[r * GRID_COLS + c].replace("/", "__") + ".png"))
                 if r * GRID_COLS + c < len(order) else str(blank)
                 for c in range(GRID_COLS)]
        rf = tmp / f"_row{r}.png"
        run("convert", *cells, "+append", str(rf))
        row_files.append(str(rf))
    run("convert", *row_files, "-append", str(OUT / "sheet_raw.png"))
    # 压一下体积：厚涂图色阶丰富，200 色肉眼几乎看不出，体积掉 2/3
    run("convert", str(OUT / "sheet_raw.png"), "-strip",
        "-colors", "200", "-define", "png:compression-level=9",
        str(OUT / "sheet.png"))
    (OUT / "sheet_raw.png").unlink(missing_ok=True)

    cols = len(order)
    manifest = {
        "image": "sheet.png",
        "cell": {"w": w, "h": h},
        "cols": GRID_COLS,
        "rows": rows,
        "frames": manifest_frames,
        "blink_patch": "blink_patch.png",
        "groups": {g: [f for (gg, f, _) in
                       [(x[0], x[1], None) for x in jobs] if gg == g]
                   for g, _, _ in GROUPS},
    }

        # 4) 眨眼补丁
    #
    # 这里的蒙版必须是**两只眼睛的形状**，不能是「一条圆角矩形横带」。
    # 旧做法用 roundrectangle 羽化，框里带着鼻子、脸颊和围巾，
    # 一闭眼就在脸中央浮出一个方块 —— 用户报的"闭眼部件重合"就是这个。
    #
    # 蒙版来源：把 Open 版和 Closed 版的**脸部区域逐像素求差**，
    # 差异自然就集中在两只眼睛上（实测 4357 px，bbox 245,187–540,287），
    # 再膨胀几圈盖住眼皮阴影，最后只让这一块显影 blink_closed 的像素。
    # 这样蒙版天生只含眼睛，不可能把鼻子/围巾带进来。
    blink_src = SRC / BLINK_SRC
    if blink_src.exists():
        base_src = SRC / FACE_SRC                # base_v1.png，所有表情的基础脸
        def _rgba(path):
            raw = subprocess.run(["convert", str(path), "-fuzz", FUZZ,
                                  "-transparent", "black", "-depth", "8", "rgba:-"],
                                 capture_output=True, check=True).stdout
            return np.frombuffer(raw, dtype=np.uint8).reshape(sh, sw, 4).astype(np.int16)

        a_img, b_img = _rgba(base_src), _rgba(blink_src)
        # 裁切后的整格尺寸 (w,h) 对应源图 (l,t) 起点，这里在源图坐标系里做
        diff = np.abs(a_img[..., :3] - b_img[..., :3]).max(axis=2)
        eye_band = np.zeros(diff.shape, bool)
        eye_band[EY0:EY1, EX0:EX1] = True      # 只允许出现在脸部横带内
        mask = (diff > 14) & eye_band
        # 膨胀：眼皮阴影、睫毛要整块盖住，否则闭眼后还留着睁眼的眼角
        from numpy.lib.stride_tricks import sliding_window_view
        for _ in range(3):
            pad = np.pad(mask.astype(np.uint8), 2, mode="edge")
            mask = sliding_window_view(pad, (5, 5)).max(axis=(2, 3)) > 0
        # 眉毛线以上一律不进蒙版：闭眼不该把眉毛一起擦淡
        mask[:EY0 - 6, :] = False
        # 与原图 alpha 取交集（透明区不进蒙版）
        mask &= b_img[..., 3] > 10

        mask_png = tmp / "eye_mask_src.png"
        subprocess.run(["convert", "-size", f"{sw}x{sh}", "-depth", "8", "gray:-",
                        str(mask_png)],
                       input=(mask.astype(np.uint8) * 255).tobytes(), check=True)
        run("convert", str(mask_png), "-blur", "0x5", str(tmp / "eye_mask_b.png"))

        b_rgba = tmp / "blink_rgba.png"
        run("convert", str(blink_src), "-fuzz", FUZZ, "-transparent", "black",
            "-depth", "8", str(b_rgba))
        patch_src = tmp / "eye_patch_src.png"
        run("convert", str(b_rgba), str(tmp / "eye_mask_b.png"),
            "-alpha", "off", "-compose", "CopyOpacity", "-composite", str(patch_src))
        # 对齐到整格裁切框 + 统一调色，和 sheet 里的格子完全同源同色
        run("convert", "-size", f"{w}x{h}", "xc:none", "(",
            str(patch_src), ")", "-geometry", f"+{-l}+{-t}",
            "-compose", "over", "-composite", *BEAUTY,
            str(OUT / "blink_patch.png"))
        print(f"眨眼补丁：眼睛蒙版 {int(mask.sum())} px")

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

    # 6) 顺手把 Ren'Py 侧的立绘注册块重写一遍（坐标改了不同步会静默错位）
    sync_renpy(manifest)

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
