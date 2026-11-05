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
    # 非 base 组一律用**本造型自己的表情图**（ponytail_amused.png 这种），
    # 不能借 expr_*.png —— 那些是拿 base_v1 出的，头发是短发，
    # 借过来会把马尾/盘发换回短发，而且五官坐标也有 1~2px 偏差。
    # 注意：outfit_apron.png 其实是「蓝吊带」，不是围裙（早期命名遗留）。
    # 真围裙是 apron_flat.png，所以围裙组以它为底，表情也从它 img2img 出来。
    ("apron",      "apron_flat.png", [
        ("calm",     None),
        ("amused",   "apron_amused.png"),
        ("smile_soft","apron_smile_soft.png"),
        ("sly",      "apron_sly.png"),
        ("flat",     None),
    ]),
    ("coat",       "outfit_coat.png", [
        ("calm",     None),
        ("suspicious","coat_suspicious.png"),
        ("sly",      "coat_sly.png"),
        ("flat",     "coat_flat.png"),
    ]),
    ("ponytail",   "hair_ponytail.png", [
        ("calm",     None),
        ("amused",   "ponytail_amused.png"),
        ("hungry",   "ponytail_hungry.png"),
        ("sly",      "ponytail_sly.png"),
        ("flat",     "ponytail_flat.png"),
    ]),
    ("hairup",     "hair_up.png", [
        ("calm",     None),
        ("amused",   "hairup_amused.png"),
        ("smile_soft","hairup_smile_soft.png"),
    ]),
]

BLINK_SRC = "blink_closed.png"
# 眼部横带（源图坐标 768×1376，实测位）
EYE_BOX = "300x100+235+235"
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


def run(*args):
    subprocess.run(args, check=True, capture_output=True)


def alpha(src: Path, dst: Path):
    """黑底 → 透明"""
    run("convert", str(src), "-fuzz", FUZZ, "-transparent", "black", "-alpha", "set", str(dst))


def face_patch(src: Path, canvas: Path, base_file: str):
    """从表情图里只取眼部那一块，羽化边缘后贴到造型底图上。

    背景：AI 出的 expr_*.png 都是拿 base_v1 当参考的，头发是短发。
    直接拿它当 ponytail/amused 会把马尾换回短发。
    只借「眼睛周围」就不会动到发型和衣服。
    """
    px, py, pw, ph = (int(v) for v in
                      FACE_PATCH.replace("x", "+").split("+"))
    align = EYE_ALIGN.get(base_file, EYE_ALIGN["base_v1.png"])
    scale = align["scale"]
    gx, gy = align["center"]
    ax, ay = EXPR_ANCHOR

    stem = canvas.with_suffix("")
    piece = Path(str(stem) + "_piece.png")
    run("convert", str(src), "-fuzz", FUZZ, "-transparent", "black", "-alpha", "set",
        "-crop", FACE_PATCH, "+repage", str(piece))

    # 1) 按眼距缩放（绕表情基准点），让五官大小和本组造型一致
    sw, sh = round(pw * scale), round(ph * scale)
    scaled = Path(str(stem) + "_scaled.png")
    run("convert", str(piece), "-filter", "Lanczos",
        "-resize", f"{sw}x{sh}!", str(scaled))

    # 2) 羽化遮罩（尺寸跟缩放后一致）
    f = FACE_FEATHER
    mask = Path(str(stem) + "_mask.png")
    run("convert", "-size", f"{sw}x{sh}", "xc:black",
        "-fill", "white",
        "-draw", f"roundrectangle {f},{f} {sw - f},{sh - f} {f + 4},{f + 4}",
        "-blur", f"0x{f / 2}", str(mask))

    cut = Path(str(stem) + "_cut.png")
    run("convert", str(scaled),
        "(", str(mask), "-alpha", "copy", ")",
        "-compose", "DstIn", "-composite", str(cut))

    # 3) 贴到画布：让表情的「双眼中点」与造型的「双眼中点」重合。
    #    注意 piece 的坐标原点是裁切框左上角，不是源图左上角 —— 早期漏了这层
    #    换算，贴片会飞到头顶上去。
    ex, ey = ax - px, ay - py                    # 眼中心在裁切块内的位置
    px_c, py_c = pw / 2, ph / 2                  # 缩放围绕裁切块中心
    ex_s = px_c + scale * (ex - px_c)            # 缩放后眼中心在块内的位置
    ey_s = py_c + scale * (ey - py_c)
    ox = round(gx - ex_s)                        # 贴到画布时的左上角偏移（源坐标）
    oy = round(gy - ey_s)

    run("convert", str(canvas),
        "(", str(cut), ")",
        "-geometry", f"+{ox}+{oy}",
        "-compose", "over", "-composite", str(canvas))

    for tmp in (piece, scaled, mask, cut):
        tmp.unlink(missing_ok=True)


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
            # 画布永远是**本组底图**（发型/衣服来自它），
            # 表情图只提供眼睛那一块。
            alpha(SRC / base_file, dst)
            # 所有表情图都是原生同构图（拿本造型底图做 img2img 出来的），
            # 直接整图透明化即可，不需要任何贴片修补。
            jobs.append((group, face, dst))

    if not jobs:
        raise SystemExit("没有可用源图")

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
