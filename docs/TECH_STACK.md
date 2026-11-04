# 技术选型：语言、引擎与打包方式（exe 版）

> **结论：Python 生态的 Ren'Py 8.5.3 + 自写剧本。产出 Windows 免安装 .exe。**

---

## 1. 为什么不是别的

| 方案 | 语言 | 为什么不用 |
|---|---|---|
| 网页原生 VN（上一版方案） | JS/HTML | 你已明确要 exe。用 Electron 包一层能出 exe，但包体 150–250 MB，且等于把浏览器塞进安装目录 |
| Unity | C# | 纯对白游戏用 Unity 是杀鸡用牛刀；包体大、启动慢、VN 的存档/回滚/历史/自动播放都要自己写 |
| Godot 4 | GDScript | 原作用的就是它，自由度高，但**VN 专用功能全要自己实现**；且 4.x 的 Windows 导出还要处理线程/渲染兼容，包体也比 Ren'Py 大 |
| **Ren'Py 8.5.3** | **Python** | ✅ 见下 |

## 2. 选 Ren'Py 的五个理由

1. **它就是为这件事生的。** 存档、读档、回滚（回想）、对白历史、跳过、自动播放、字号/文字速度设置、窗口缩放、全屏——全部开箱即用。这些是 VN 玩家**默认会去点**的东西，自己写要几百行，写不好就被骂。
2. **语言是 Python，剧本是 DSL。** 日常写对白就是写 `.rpy`：
   ```renpy
   idimya "你来了。"
   menu:
       "说实话。":
           $ trust += 1
   ```
   逻辑部分是真 Python，后面要做「三量表」「承诺账本」「嗅觉图鉴」这种系统，不需要跟引擎打架。
3. **中文支持成本最低。** 换一个 TTF 就是中文字体（本项目已内置 Noto Sans SC，OFL 授权），不需要额外字体图集或位图字。
4. **exe 打包是官方功能。** 启动器里的 Build Distributions 直接产出 Windows 免安装包（zip，解压双击 exe）。不是第三方壳。
5. **迁移成本为零。** 万一以后想上 Steam / itch / Android / Web，同一份工程直接再打一个包即可。

**唯一代价**：Ren'Py 的画面演出是「声明式」的（ATL 变换、图层），要做很花的特效不如 Godot 自由。但本作的演出需求是**烛光呼吸、立绘推近、气味浮层、画面压暗**——这些 Ren'Py 都能干净地做（见 `game/script.rpy` 里的 `transform`）。

## 3. 工程结构

```
icancook/
├── project.json            # 构建配置（打哪几个平台）
├── icon.ico                # exe 图标（已从定稿主视觉裁出）
└── game/
    ├── options.rpy         # 游戏名、版本、build.name、存档目录
    ├── gui.rpy             # GUI 尺寸与配色（已改为 1920×1080）
    ├── screens.rpy         # 界面（对白框/选项/主菜单已改为中文极简风）
    ├── style_custom.rpy    # ★ 视觉皮肤：底部纯深色横条 + 无框文字选项
    ├── script.rpy          # ★ 剧本：Ch0 重制版第一次约会 + 3 结局
    ├── smell.rpy           # ★ 「闻一闻这张桌子」交互 screen
    ├── fonts/              # Noto Sans SC（OFL）
    ├── images/             # 背景（主视觉定稿）+ 暗角
    └── gui/                # 界面底图（已按 1920×1080 重制）
```

## 4. 怎么出 exe

### 路线 A（已在仓库里配好）：GitHub Actions，不需要本地 Windows
`.github/workflows/build-exe.yml` 会在 GitHub 的 Windows 机器上：
1. 下载 Ren'Py 8.5.3 官方 SDK
2. `renpy.exe icancook compile` —— **真编译**，语法错会直接让流程失败（等于免费帮你验剧本）
3. `renpy.exe launcher distribute icancook --package win` —— 产出 Windows 包
4. 解压成可直接运行的文件夹，上传为 Artifact

触发方式：推一个 `v*` tag，或在 Actions 页面点 **Run workflow**。
产物：「Actions → 最近一次运行 → Artifacts → `icancook-win`」，解压后双击 `i_can_cook_for_you_from_here.exe`。

### 路线 B：本机 Windows
1. 下载 Ren'Py 8.5.3 SDK（Windows 版）
2. 启动器里把 `icancook` 目录作为项目打开
3. **Build Distributions → 只勾 Windows → Build**
4. 产物在 `icancook-dists/` 里，是一个 zip，解压即玩

> 为什么这台 Linux 沙盒不能直接给你 exe：Ren'Py 的 Windows 打包需要 Windows 版的 SDK 二进制（`renpy.exe` + 一堆 `.dll`），而沙盒的外网只放行了 GitHub / npm / PyPI，下载不到 Ren'Py 的 SDK 包。所以 exe 这一步交给 GitHub Actions 的 Windows runner 做——它属于同一个仓库，不需要你本地装任何东西。

## 5. 已经做了的骨架（M1）

- 1920×1080，中文界面，Noto Sans SC
- 极简皮肤：底部一条半透明深色横条，无边框文字选项（对齐原作观感）
- Ch0 完整流程：进场 → 三个问题 → **嗅觉交互** → 反转（换你问她）→ 三档结局 → 章末
- 隐藏变量：`scent / trust / doubt`，结局由它们算出来（UI 不显示，只用演出反馈）
- 「承诺账本」的钩子（`promise`）——为第四章逐条复述埋好
- 三种结局写进 `persistent`，为将来做鉴赏页
