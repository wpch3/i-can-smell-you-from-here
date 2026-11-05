#!/usr/bin/env python3
"""
gen_audio.py —— 程序化生成环境音 / 音效（不依赖任何外部音频库）

为什么不用素材库：这个项目是非商业同人，能不用别人的音频就不用。
环境音本来就是"没有旋律的东西"，用噪声 + 几个正弦分量合成反而更合适：
  · 低频嘶声     → 火、冰箱压缩机、远处车流
  · 带通白噪     → 雨、油锅
  · 缓慢起伏的正弦 → 房间的"呼吸"（人耳会读成"有人在附近"）
  · 偶发事件     → 锅铲轻碰、木头收缩、门铃

循环处理：生成两倍长度，取首尾交叉淡化，接缝听不出来。

用法：python3 tools/gen_audio.py
产物：icancook/game/audio/*.wav（mono / 22050Hz / 16bit，体积可控）
"""

import math
import random
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "icancook" / "game" / "audio"
SR = 22050


# ---------------------------------------------------------------- 基础积木
def white(n, rng):
    return [rng.uniform(-1.0, 1.0) for _ in range(n)]


def smooth(x, k):
    """一阶低通（简单的指数滑动平均），k 越小越闷。"""
    out = [0.0] * len(x)
    y = 0.0
    for i, v in enumerate(x):
        y += k * (v - y)
        out[i] = y
    return out


def bandpass(x, lo, hi, rng=None):
    """低通(hi) - 低通(lo)，够用了。"""
    a = smooth(x, hi)
    b = smooth(x, lo)
    return [a[i] - b[i] for i in range(len(x))]


def sine(n, freq, phase=0.0):
    w = 2 * math.pi * freq / SR
    return [math.sin(w * i + phase) for i in range(n)]


def envelope(n, attack, decay, curve=2.0):
    """短事件的包络。"""
    out = []
    for i in range(n):
        t = i / SR
        if t < attack:
            v = t / max(attack, 1e-6)
        else:
            v = max(0.0, 1.0 - (t - attack) / max(decay, 1e-6))
        out.append(v ** curve)
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    out = [0.0] * n
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    return out


def gain(x, g):
    return [v * g for v in x]


def place(dest, src, at_sec, g=1.0):
    """把短事件叠加到长床上（at_sec 秒处）。"""
    start = int(at_sec * SR)
    for i, v in enumerate(src):
        j = start + i
        if 0 <= j < len(dest):
            dest[j] += v * g
    return dest


def loopify(x, fade_sec=1.5):
    """首尾交叉淡化，做无缝循环。"""
    f = int(fade_sec * SR)
    body = x[: len(x) - f]
    tail = x[len(x) - f:]
    for i in range(f):
        k = i / f
        body[i] = body[i] * k + tail[i] * (1 - k)
    return body


def soft_limit(x, ceiling=0.92):
    """tanh 软限幅，避免削顶爆音。"""
    return [math.tanh(v / ceiling) * ceiling for v in x]


def write(name, x, peak=0.72):
    x = soft_limit(x)
    m = max(1e-9, max(abs(v) for v in x))
    x = [v / m * peak for v in x]
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(
            struct.pack("<h", int(max(-1.0, min(1.0, v)) * 32767)) for v in x))
    print(f"  {name:24s} {len(x) / SR:5.1f}s  {p.stat().st_size // 1024:5d} KB")


# ---------------------------------------------------------------- 各条音床
def amb_kitchen(sec=36):
    """厨房：火焰的低频嘶声 + 油锅的细响 + 房间的呼吸。"""
    rng = random.Random(11)
    n = int(sec * SR)
    hiss = gain(bandpass(white(n, rng), 0.02, 0.10), 0.5)      # 火
    fry = gain(bandpass(white(n, rng), 0.35, 0.75), 0.06)      # 油
    hum = gain(sine(n, 47.0), 0.05)                            # 房间基频
    breath = [1.0 + 0.35 * math.sin(2 * math.pi * i / (SR * 7.5)) for i in range(n)]
    bed = [hiss[i] * breath[i] + fry[i] + hum[i] for i in range(n)]
    # 偶发：锅铲轻碰、木头收缩
    for t in (4.2, 11.7, 19.3, 27.9, 33.1):
        m = int(0.22 * SR)
        hit = [rng.uniform(-1, 1) for _ in range(m)]
        hit = bandpass(hit, 0.25, 0.6)
        hit = [hit[i] * envelope(m, 0.004, 0.2, 3.0)[i] for i in range(m)]
        place(bed, hit, t, 0.6)
    return loopify(bed, 2.0)


def amb_fridge(sec=34):
    """冰箱：压缩机低鸣 + 冷白噪 + 极慢的起伏（不太舒服的那种）。"""
    rng = random.Random(23)
    n = int(sec * SR)
    comp = gain(sine(n, 61.5), 0.22)
    comp2 = gain(sine(n, 92.0, 1.1), 0.08)
    cold = gain(bandpass(white(n, rng), 0.55, 0.95), 0.10)
    drone = gain(bandpass(white(n, rng), 0.01, 0.04), 0.55)
    wob = [1.0 + 0.25 * math.sin(2 * math.pi * i / (SR * 11.0)) for i in range(n)]
    bed = [comp[i] * wob[i] + comp2[i] + cold[i] + drone[i] for i in range(n)]
    # 偶发：压缩机启动的"咔"
    for t in (8.5, 24.0):
        m = int(0.35 * SR)
        clk = bandpass([rng.uniform(-1, 1) for _ in range(m)], 0.2, 0.9)
        clk = [clk[i] * envelope(m, 0.002, 0.3, 3.5)[i] for i in range(m)]
        place(bed, clk, t, 0.5)
    return loopify(bed, 2.0)


def amb_rain(sec=38):
    """玄关外：雨。中频为主，带一点远处的低频隆隆。"""
    rng = random.Random(37)
    n = int(sec * SR)
    rain = gain(bandpass(white(n, rng), 0.30, 0.80), 0.55)
    far = gain(bandpass(white(n, rng), 0.01, 0.05), 0.45)
    swell = [1.0 + 0.3 * math.sin(2 * math.pi * i / (SR * 9.0)) for i in range(n)]
    bed = [rain[i] * swell[i] + far[i] for i in range(n)]
    # 偶发：水滴落在檐上
    for t in (3.1, 9.6, 15.2, 21.8, 28.4, 34.0):
        m = int(0.09 * SR)
        drip = gain(sine(m, rng.uniform(900, 1500)), 1.0)
        drip = [drip[i] * envelope(m, 0.001, 0.06, 2.0)[i] for i in range(m)]
        place(bed, drip, t, 0.12)
    return loopify(bed, 2.0)


def amb_morning(sec=32):
    """清晨：很轻的风 + 远处鸟（两只，间隔不规则）。"""
    rng = random.Random(53)
    n = int(sec * SR)
    wind = gain(bandpass(white(n, rng), 0.02, 0.12), 0.5)
    air = gain(bandpass(white(n, rng), 0.45, 0.9), 0.05)
    bed = [wind[i] + air[i] for i in range(n)]
    for t in (2.2, 5.9, 6.7, 12.4, 17.1, 17.9, 23.6, 28.9):
        m = int(0.16 * SR)
        f0 = rng.uniform(2200, 3200)
        chirp = []
        for i in range(m):
            tt = i / SR
            f = f0 * (1.0 + 0.35 * (tt / 0.16))
            chirp.append(math.sin(2 * math.pi * f * tt))
        chirp = [chirp[i] * envelope(m, 0.008, 0.14, 2.2)[i] for i in range(m)]
        place(bed, chirp, t, 0.10)
    return loopify(bed, 2.0)


def sfx_knife():
    """刀落砧板：一下闷响 + 一点金属余韵。"""
    rng = random.Random(7)
    m = int(0.42 * SR)
    thud = [rng.uniform(-1, 1) for _ in range(m)]
    thud = bandpass(thud, 0.05, 0.25)
    thud = [thud[i] * envelope(m, 0.001, 0.30, 3.0)[i] for i in range(m)]
    ring = [math.sin(2 * math.pi * 2900 * i / SR) * math.exp(-i / (SR * 0.05))
            for i in range(m)]
    return mix(gain(thud, 1.0), gain(ring, 0.10))


def sfx_bell():
    """门铃：两声，第二声低一点。"""
    out = [0.0] * int(1.6 * SR)
    for k, (f, t0) in enumerate(((1175.0, 0.0), (880.0, 0.42))):
        m = int(1.1 * SR)
        tone = []
        for i in range(m):
            tt = i / SR
            env = math.exp(-tt * 3.2)
            tone.append((math.sin(2 * math.pi * f * tt)
                         + 0.45 * math.sin(2 * math.pi * f * 2.01 * tt)
                         + 0.20 * math.sin(2 * math.pi * f * 3.02 * tt)) * env)
        place(out, tone, t0, 0.55)
    return out


def sfx_heartbeat():
    """一下心跳：低沉的两次撞击。"""
    out = [0.0] * int(1.1 * SR)
    for t0 in (0.0, 0.22):
        m = int(0.35 * SR)
        beat = gain(sine(m, 52.0), 1.0)
        beat = [beat[i] * envelope(m, 0.008, 0.28, 2.5)[i] for i in range(m)]
        place(out, beat, t0, 0.8)
    return out


def main():
    print("生成音频：")
    write("amb_kitchen.wav", amb_kitchen())
    write("amb_fridge.wav", amb_fridge())
    write("amb_rain.wav", amb_rain())
    write("amb_morning.wav", amb_morning())
    write("sfx_knife.wav", sfx_knife(), peak=0.8)
    write("sfx_bell.wav", sfx_bell(), peak=0.8)
    write("sfx_heartbeat.wav", sfx_heartbeat(), peak=0.75)
    total = sum(p.stat().st_size for p in OUT.glob("*.wav")) // 1024
    print(f"合计 {total} KB → {OUT}")


if __name__ == "__main__":
    main()
