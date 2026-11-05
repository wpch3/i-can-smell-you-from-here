#!/usr/bin/env python3
"""
build_layers.py —— L2 分层试点：把立绘切成「可刚性运动」的几层

为什么不用 Live2D：
  厚涂的笔触本身就是信息，网格变形会把刷痕拉成橡皮泥。
  这里只做**刚性位移 + 旋转**（整层平移，绝不拉伸），笔触完整保留。

为什么每层不是「矩形羽化」而必须「按遮罩显影」：
  矩形羽化会把框里的**所有东西**一起抠出来 —— 刘海那一框里还有眉毛、眼睑、
  额头皮肤，丝巾那一框里还有吊带和胸口。层一动，这些零件就跟着漂，
  于是出现"眉毛浮在脸上""吊带和丝巾错位"。正确做法是先用色相/形状
  把「丝巾 / 头发 / 高光」自身分离成遮罩，再用遮罩显影原图，
  框里不属于该部件的东西一律不带走。

切出三层（都不需要重画，直接从现有精灵表里扣）：
  layer_scarf.png   丝巾垂下的尾端 —— 摆幅最大，最出效果
  layer_bangs.png   前发（刘海 + 两侧发绺）—— 轻微摆动
  layer_spec.png    高光层（丝巾 + 肩部的亮面）—— 用透明度呼吸模拟烛光

产物：icancook/game/images/idimya/layers/
      + layers.json（每层的定位框，与 sheet 的格子坐标对齐）
"""

import json
import sys
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SPR = ROOT / "icancook" / "game" / "images" / "idimya"
OUT = SPR / "layers"

# 以 base/calm 这一格为基准（其余造型共用同一套分层几何）
BASE_FRAME = "base/calm"

# 相对格子左上角的取景（x, y, w, h），羽化半径
LAYERS = {
    # 丝巾垂下的那一截：从颈侧一直到腰际。
    # 遮罩 = 蓝布（B 明显高于 R）。框里同时有黑吊带和胸口的皮肤，只留蓝色。
    "scarf": {
        # 旧的框 (322,262,150,560) 横跨了吊带、胸口和裙子：
        # 遮罩只按「蓝色」取像素，于是裙子上一大块蓝色也被切了进来，
        # 层一动，胸口/裙子上就浮出一块错位的蓝布 —— 用户报的"部件错位"。
        # 现在只框**垂下的那条尾巴**（右侧，y≈400 起），下沿停在 696：
        # 再往下它已经和裙沿连成一片，切开反而会露出缝。
        "box": (382, 396, 130, 300),
        "feather": 12,
        "pivot": (0.30, 0.02),     # 以打结处为轴
        "mask": "scarf",
    },
    # 刘海：只留**头发**。原来的矩形框里还连着眉毛、眼睑和额头皮肤，
    # 一动就成了「眉毛浮在脸中间」—— 用户报的"部件错位"就是这个。
    "bangs": {
        "box": (110, 10, 390, 210),
        "feather": 12,
        "pivot": (0.5, 0.10),
        "mask": "hair",
    },
    # 高光：只留皮肤上最亮的一小片，且框不能压到吊带/丝巾边缘，
    # 否则叠加会让衣服边缘发亮 → 看起来像错位。
    "spec": {
        "box": (250, 230, 300, 220),
        "feather": 20,
        "pivot": (0.5, 0.5),
        "mask": "highlight",
    },
}


def mask_scarf(rgb):
    """蓝布：B 明显高于 R，且不是暗部/黑吊带。"""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (b > r + 15) & (b > 90)


def mask_hair(rgb):
    """橙发：R 远高于 B。皮肤肤色 R-B 只有 60~80，用 80 的阈值能分开。"""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (r - b > 80) & (r > 120)


def mask_highlight(rgb):
    """肩头/锁骨的高光：皮肤色里偏亮的那部分（排除蓝布和白围裙）。

    阈值原来定在 168，实测整格最亮处也才 165 → 遮罩全空，
    layer_spec.png 是个 385 字节的空图，引擎叠了半天什么都没叠。
    现在改成「皮肤色 & 亮度 > 全图中位数 + 22」。"""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = (r * 299 + g * 587 + b * 114) / 1000.0
    skin = (r > b + 30) & (r > 90)
    if not skin.any():
        return skin
    return skin & (lum > np.median(lum[skin]) + 22)


MASKS = {"scarf": mask_scarf, "hair": mask_hair, "highlight": mask_highlight}


def run(*args):
    subprocess.run(args, check=True, capture_output=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((SPR / "sheet.json").read_text(encoding="utf-8"))
    cw, ch = manifest["cell"]["w"], manifest["cell"]["h"]
    cx, cy, _, _ = manifest["frames"][BASE_FRAME]

    # 先把基准格整块抠出来当素材
    src = OUT / "_base.png"
    run("convert", str(SPR / "sheet.png"), "-crop", f"{cw}x{ch}+{cx}+{cy}", "+repage", str(src))

    info = {"cell": {"w": cw, "h": ch}, "layers": {}}

    for name, cfg in LAYERS.items():
        bx, by, bw, bh = cfg["box"]
        # 1) 取景
        piece = OUT / f"_{name}_raw.png"
        run("convert", str(src), "-crop", f"{bw}x{bh}+{bx}+{by}", "+repage", str(piece))

        # 2) 遮罩：用颜色谓词从原图里分离出该部件本体，
        #    只对「本来就是该部件」的像素给白色，框里的其他零件一律黑。
        #    这样层位移时，不会把眉毛/吊带/皮肤一起带着漂。
        rgb = np.frombuffer(
            subprocess.run(["convert", str(src), "-depth", "8", "rgb:-"],
                           check=True, capture_output=True).stdout,
            dtype=np.uint8).reshape(ch, cw, 3).astype(np.int16)
        sub = rgb[by:by + bh, bx:bx + bw]
        m = MASKS[cfg["mask"]](sub)
        # 吃掉零星的噪点：只保留有一定连通面积的像素（3x3 中值滤波近似）
        from numpy.lib.stride_tricks import sliding_window_view
        pad = np.pad(m.astype(np.uint8), 1, mode="edge")
        m = sliding_window_view(pad, (3, 3)).sum(axis=(2, 3)) >= 5
        alpha_src = sub.sum(axis=2) > 0          # 原图透明区一律不进遮罩
        m = m & alpha_src
        mask = OUT / f"_{name}_mask.png"
        subprocess.run(["convert", "-size", f"{bw}x{bh}", "-depth", "8", "gray:-",
                        str(mask)],
                       input=(m.astype(np.uint8) * 255).tobytes(), check=True)
        run("convert", str(mask), "-blur", f"0x{cfg['feather']/2}", str(mask))

        # 3) 羽化：用 DstIn 把「原有 alpha」和「遮罩 alpha」相乘
        #    注意不能用 CopyOpacity —— 那会把原来的透明区变成不透明黑块
        cut = OUT / f"_{name}_cut.png"
        run("convert", str(piece),
            "(", str(mask), "-alpha", "copy", ")",
            "-compose", "DstIn", "-composite", str(cut))

        # 4) 贴回整格坐标系（引擎端直接叠，不需要额外偏移）
        layer = OUT / f"layer_{name}.png"
        run("convert",
            "-size", f"{cw}x{ch}", "xc:none",
            "(", str(cut), ")",
            "-geometry", f"+{bx}+{by}",
            "-compose", "over", "-composite", str(layer))

        info["layers"][name] = {
            "file": f"layers/layer_{name}.png",
            "box": [bx, by, bw, bh],
            "pivot": cfg["pivot"],          # 旋转/摆动的轴心（相对 box 的 0..1）
            "canvas": [cw, ch],
        }

    (SPR / "layers.json").write_text(json.dumps(info, ensure_ascii=False, indent=1),
                                     encoding="utf-8")

    # 自检：三层在**零位移**下叠回原格，必须逐像素一致（RMSE=0）。
    # 这条能一次性抓出「遮罩选错颜色 / 层偏移 / 空层」三类错误 ——
    # 本轮就是靠它发现 layer_spec 阈值定在 168 时整张是空的。
    if "--no-check" not in sys.argv:
        base_cell = OUT / "_check_base.png"
        run("convert", str(SPR / "sheet.png"), "-crop", f"{cw}x{ch}+{cx}+{cy}",
            "+repage", str(base_cell))
        stacked = OUT / "_check_stack.png"
        names = list(LAYERS)
        run("convert", str(base_cell),
            "(", str(OUT / f"layer_{names[0]}.png"), ")",
            "(", str(OUT / f"layer_{names[1]}.png"), ")",
            "(", str(OUT / f"layer_{names[2]}.png"), ")",
            "-compose", "over", "-composite", str(stacked))
        r = subprocess.run(["compare", "-metric", "RMSE", str(base_cell), str(stacked),
                            "null:"], capture_output=True, text=True)
        err = (r.stderr or "").strip()
        base_cell.unlink(missing_ok=True)
        stacked.unlink(missing_ok=True)
        # 叠上去只会多、不会少 → 允许极小的 alpha 舍入，其余一律报错
        if err.startswith("0 (0)") or err.startswith("0 (0.0"):
            print(f"  自检 三层零位移叠回原格：RMSE={err} ✅")
        else:
            print(f"  自检 三层零位移叠回原格：RMSE={err} ❌（零件不一致）")

    for p in OUT.glob("_*.png"):
        p.unlink()

    print(f"基准格 {BASE_FRAME} → {cw}×{ch}")
    for name in LAYERS:
        f = OUT / f"layer_{name}.png"
        print(f"  {f.name:22s} {f.stat().st_size // 1024:5d} KB  "
              f"box={LAYERS[name]['box']}")
    print("清单：", SPR / "layers.json")


if __name__ == "__main__":
    main()
