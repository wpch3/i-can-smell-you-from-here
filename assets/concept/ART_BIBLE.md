# 美术设定锁（Art Bible）· 定稿参照

**定稿图：** `assets/concept/key-visual-official.png`（1920 版：`key-visual-official.jpg`）
**原始参考：** `assets/reference/original-first-date-screenshot.png`

> 这张定稿是**唯一标准**。以后所有立绘、表情差分、CG 都必须以它为锚点，
> 不允许再"改良"或"重新设计"形象。只允许改变量（表情、手势、光线、机位）。

---

## 1. 角色锚点（写死，不可改）

| 部位 | 定稿描述 |
|---|---|
| 年龄感 | 20 代前半，24 岁 |
| 脸型 | 小巧鹅蛋脸、尖下巴、颧骨柔和 |
| 眼睛 | 大而狭长的深棕杏眼，半垂眼睑、上眼线深、睫毛重、目光直视镜头，带一点被逗笑的意思 |
| 眉 | 细、平、微微上扬 |
| 鼻 | 小巧，鼻头有一点高光 |
| 嘴 | 柔和的哑光豆沙色，微微抿着，单侧嘴角上挑 0.5 毫米的笑 |
| 皮肤 | 冷调象牙白，脸颊有淡红晕；强侧光（烛光）半边暖橙、半边冷影 |
| 头发 | 浅金色短波波头，齐眉钝刘海，发尾到下颌处向外翘；厚涂笔触，暖金高光 |
| 身形 | 纤细窄肩，锁骨与胸骨线清晰，胸部自然不夸张（**不要放大**） |
| 服装 | 浅蓝挂脖上衣（细带），浅蓝丝巾绕颈垂下 |
| 标志物 | 圆形深色木桌、左侧粗陶烛台、右侧深色皮质笔记本 |

## 2. 笔触与后期（风格 DNA）

- 厚涂数字油画：**可见的笔触堆叠、湿画法过渡、纸纹/画布颗粒**
- 边缘粗糙、局部"没画完"，尤其在手臂、桌沿、背景
- 无干净线稿、无赛璐璐分区、无塑料高光、无 3D 感
- 色板：`#1A1410` 近黑 · `#2E2319` 深棕 · `#3F3024` 木墙 · `#E8C79B` 烛光暖 · `#F0DED0` 皮肤 · `#A8C4D4` 丝巾蓝
- 全画面 70% 在暗部，唯一暖光源永远是烛火，**皮肤是全图最高明度**
- 暗角（vignette）必须存在；四角压到近乎纯黑

## 3. 生成提示词模板（复用）

```
[场景/机位] — same character as the locked reference: early-20s woman, pale ivory skin,
short pale-golden blonde bob with blunt fringe and flipped ends at the jaw, large dark
almond eyes half-lidded and smoky, small nose, dusty-rose half-smile, slim shoulders,
light baby-blue halter top, pale blue silk scarf at the throat.
Painted in thick digital oil — visible brush strokes, wet blending, canvas grain,
rough unfinished edges, strong chiaroscuro. Muted palette: umber, sepia, charcoal,
cream skin, one dusty-blue accent. Single warm candle source from lower left.
[表情/手势] [背景] 16:9. No text, no UI, no watermark, no clean line art, no cel shading.
```

**表情差分只改这一句：**
- 平静 | `calm, eyes lowered a fraction`
- 被逗笑 | `amused, eyes crinkled, one corner of the mouth lifted`
- 靠近 | `leaning in, chin slightly down, eyes fixed on the viewer`
- 起疑 | `smile held but eyes flat, one brow a hair higher`
- 饥饿 | `lips parted, pupils wide, smile too still`
- 温柔（罕见） | `soft, unguarded, no smile, eyes warm`

## 4. UI 规范

- 对白框：底部纯深色横条（无圆角、无边框发光），左内边距 32px，字号小、无衬线，字色 `#E6E0D8`
- 选项：极简文字列表，悬停时该行左侧出现一条 2px 暖金竖线
- 推进指示：右下角 10px 白色下三角，1.2 秒呼吸
- 禁用：粉色、爱心、闪亮粒子、大字号音效字

## 5. 音效规范

- 底噪：lo-fi 钢琴 + 环境房间噪（-30dB）
- 她开口时，环境音**降 3dB**（听觉上的"聚光"）
- 关键台词：字间隙插入极轻的木地板吱声或火焰噼啪
- 禁止：恐怖片小提琴尖啸、jump scare 音效
