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
node tools/simulate.js        # 81 条分支路径的纯逻辑总检
node tools/smoke-test.js      # 真点一遍（需要 npm i jsdom）
```

## 现在有什么

| 路径 | 说明 |
|---|---|
| `assets/concept/key-visual-official.png` | ✅ **主视觉定稿**（唯一形象标准，锁定不再改） |
| `assets/reference/original-first-date-screenshot.png` | 风格锚点：原作游戏内截图 |
| `icancook/` | **游戏工程（Ren'Py 8.5.3）**，产出 Windows .exe |
| `demo/` | **网页 Demo**（同一份剧本，浏览器直接玩） |
| `tools/rpy2json.py` | 剧本转译器：`.rpy` → `demo/story.json` |
| `docs/TECH_STACK.md` | 技术选型：为什么是 Ren'Py + Python，怎么出 exe |
| `docs/GAME_CONCEPT.md` | 概念书：故事、章节、系统、结局 |
| `docs/ART_BIBLE.md` | 美术设定锁 + 可复用提示词模板 + UI / 音效规范 |
| `docs/ROADMAP.md` | 里程碑 |

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
