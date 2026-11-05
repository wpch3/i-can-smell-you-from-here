#!/usr/bin/env python3
"""
build_layers.py —— L2 分层试点：把立绘切成「可刚性运动」的几层

为什么不用 Live2D：
  厚涂的笔触本身就是信息，网格变形会把刷痕拉成橡皮泥。
  这里只做**刚性位移 + 旋转**（整层平移，绝不拉伸），笔触完整保留。

切出三层（都不需要重画，直接从现有精灵表里扣）：
  layer_scarf.png   丝巾垂下的尾端 —— 摆幅最大，最出效果
  layer_bangs.png   前发（刘海 + 两侧发绺）—— 轻微摆动
  layer_spec.png    高光层（丝巾 + 肩部的亮面）—— 用透明度呼吸模拟烛光

产物：icancook/game/images/idimya/layers/
      + layers.json（每层的定位框，与 sheet 的格子坐标对齐）
"""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPR = ROOT / "icancook" / "game" / "images" / "idimya"
OUT = SPR / "layers"

# 以 base/calm 这一格为基准（其余造型共用同一套分层几何）
BASE_FRAME = "base/calm"

# 相对格子左上角的取景（x, y, w, h），羽化半径
LAYERS = {
    # 丝巾垂下的那一截：从颈侧一直到腰际
    "scarf": {
        "box": (322, 262, 150, 560),
        "feather": 14,
        "pivot": (0.18, 0.02),     # 以颈侧为轴
    },
    # 刘海 + 两侧发绺
    "bangs": {
        "box": (110, 10, 390, 188),
        "feather": 18,
        "pivot": (0.5, 0.12),
    },
    # 高光：丝巾亮面 + 肩头
    "spec": {
        "box": (250, 230, 300, 220),
        "feather": 26,
        "pivot": (0.5, 0.5),
    },
}


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

        # 2) 羽化遮罩：圆角矩形 + 高斯模糊，边缘渐隐，位移时不会露出硬边
        f = cfg["feather"]
        mask = OUT / f"_{name}_mask.png"
        run("convert", "-size", f"{bw}x{bh}", "xc:black",
            "-fill", "white",
            "-draw", f"roundrectangle {f},{f} {bw-f},{bh-f} {f},{f}",
            "-blur", f"0x{f/2}", str(mask))

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
