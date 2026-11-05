# 我在这儿就能为你下厨了
**I Can Cook For You From Here** — 非官方恋爱向同人续篇 · **Windows 桌面版（Ren'Py / Python）**

原作 *I Can Smell You From Here* © **catproblem9735**（Godot，5 结局）。
本项目为非商业同人，**不使用原作任何素材文件**（背景 / 立绘 / 音乐全部重制），仅沿用角色设定与画风语言。
原作出处：https://kingdomofmarionettes.org/i-can-smell-you-from-here/

---

## 立刻试玩

```bash
python3 -m http.server 8000 --bind 0.0.0.0
# 打开 http://localhost:8000/
```

网页 Demo 不是另写的一套：它由 `tools/rpy2json.py` **从 exe 版同一份剧本自动转译**。
改了 `icancook/game/script.rpy` 之后跑一次：

```bash
python3 tools/rpy2json.py icancook/game/script.rpy -o demo/story.json
node tools/simulate.js        # 全部固定路径 + 3000 条随机路径的纯逻辑总检
python3 tools/build_props.py                    # 前景桌面遮挡层（改过 bg_bistro 就要重跑）
python3 tools/check_script.py                   # 静态检查：引号/图名/label/变量/摆位
node tools/smoke-test.js "0,0,0,0,0,0,0,0,0"   # 真点一遍（需要 npm i jsdom）
```

## 现在有什么

| 路径 | 说明 |
|---|---|
| `assets/concept/key-visual-official.png` | ✅ **主视觉定稿**（唯一形象标准，锁定不再改） |
| `assets/reference/original-first-date-screenshot.png` | 风格锚点：原作游戏内截图 |
| `icancook/` | **游戏工程（Ren'Py 8.5.3）**，产出 Windows .exe |
| `demo/` | **网页 Demo**（同一份剧本，浏览器直接玩） |
| `tools/rpy2json.py` | 剧本转译器：`.rpy` → `demo/story.json` |
| `tools/build_sprites.py` | 立绘管线：造型 × 表情 → 网格精灵表 + `im.Crop` 注册块 |
| `tools/build_layers.py` | L2 分层：切出刘海 / 丝巾 / 高光三张独立层 |
| `tools/gen_audio.py` | 程序化合成 4 条环境音 + 7 个音效（零版权素材） |
| `tools/build_props.py` | 前景道具层：从 `bg_bistro` 抠出桌沿以下的 `table_front.png`（让她「坐」在桌后，接缝自检 RMSE=0） |
| `tools/check_script.py` | 剧本静态检查，补 Ren'Py 编译器的盲区 |
| `docs/TECH_STACK.md` | 技术选型：为什么是 Ren'Py + Python，怎么出 exe |
| `docs/GAME_CONCEPT.md` | 概念书：故事、章节、系统、结局 |
| `docs/ART_BIBLE.md` | 美术设定锁 + 可复用提示词模板 + UI / 音效规范 |
| `docs/ROADMAP.md` | 里程碑 |

## 已完成的内容

- **序章**：进店 → 三个有重量的问题 → 点菜反转 → 三种「她记住你的方式」
- **第一章 · 门铃**：玄关 → 厨房（「上次你说下次你来做，还算数吗」）→ 冰箱里十七个标着日期的罐子 → 一把椅子 → 天亮三选，章末 3 个结局
- **第二章 · 刀与糖**：先刀还是先糖 → 30 秒调味小交互（先闻再放，不可逆）→ 3 个章末结局
- **第三章 · 十七个日期**：读冰箱标签 → 只准问一个问题 → 3 个章末结局；会承接第二章你放下的那一样东西
- **立绘**：5 套造型 × 表情 = **27 格**（base 9 / apron 5 / coat 4 / ponytail 5 / hairup 4），598×1360 网格精灵表；所有造型的脸都来自同一张 `base_v1` 定妆脸
- **动态立绘**：L1（眨眼 / 呼吸 / 视点跟随 / 烛光）+ L2（刘海 / 丝巾 / 高光三层刚性位移与光呼吸）
- **背景**：小酒馆 / 玄关 / 厨房 / 砧板特写 / 冰箱（夜开）/ 雨停的窗 / 早晨餐桌
- **音频**：4 条程序化环境音 + 7 个音效（`tools/gen_audio.py` 合成，零版权素材）
- **演出**：电影遮幅、镜头推近、焦点漂移、章节卡对焦、台词按标点停顿

## 下载 exe

**[➜ GitHub Releases 直接下载](https://github.com/wpch3/i-can-smell-you-from-here/releases/latest)**
`i_can_cook_for_you_from_here-0.1.0-win.zip` → 解压 → 双击 `i_can_cook_for_you_from_here.exe`
（Windows 10/11 x64，免安装。Ren'Py 8.5.3 打包，约 40 MB）

## 出 exe

推 `v*` tag 即自动构建并**发布到 Releases**（公开下载，无需登录）：

```bash
git tag -f v0.1.6 && git push origin refs/tags/v0.1.6 --force
```

也可以在 Actions → **Build Windows EXE** → Run workflow（需先合并到 `main`）。
本机则用 Ren'Py 8.5.3 启动器打开 `icancook/` → Build Distributions → Windows。

## 一句话

原作让你为了**不被吃掉**而撒谎；这一作为了**不被看穿**而诚实。
