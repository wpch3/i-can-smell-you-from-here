## 《我在这儿就能为你下厨了》
## I Can Cook For You From Here
## 非官方恋爱向同人续篇 · 原作 I Can Smell You From Here © catproblem9735
##
## Chapter 0 — 重制版「第一次约会」

## ——— 角色 ———————————————————————————————————————————————
define idimya = Character("伊迪米娅", who_color="#d9a05f", image="idimya")
define n = Character(None, what_color="#cfc6b8")          # 你（内心与对白）
define note = Character(None, what_color="#a89a88")        # 旁白

## ——— 图像 ———————————————————————————————————————————————
image kv = "images/key_visual.jpg"
image vig = "images/vignette.png"
## 前景桌面遮挡层：从 bg_bistro 抠出的桌沿以下部分（tools/build_props.py 生成）。
## show 在立绘之上，把她的腰以下挡住 —— 站姿立绘因此看起来是"坐在桌后"。
image table_front = "images/table_front.png"

image black = Solid("#000000")
image bistro = "images/bg_bistro.jpg"
image kitchen = "images/bg_kitchen.jpg"
image genkan = "images/bg_genkan.jpg"
image morning = "images/bg_morning.jpg"
image fridge = "images/bg_fridge.jpg"
image kitchen_close = "images/bg_kitchen_close.jpg"
image window_dawn = "images/bg_window_dawn.jpg"

## ——— 音频 —（tools/gen_audio.py 程序化生成，无版权问题）
define audio.amb_kitchen = "audio/amb_kitchen.wav"
define audio.amb_fridge = "audio/amb_fridge.wav"
define audio.amb_rain = "audio/amb_rain.wav"
define audio.amb_morning = "audio/amb_morning.wav"
define audio.sfx_knife = "audio/sfx_knife.wav"
define audio.sfx_bell = "audio/sfx_bell.wav"
define audio.sfx_heartbeat = "audio/sfx_heartbeat.wav"
define audio.sfx_breath_soft = "audio/sfx_breath_soft.wav"
define audio.sfx_breath_catch = "audio/sfx_breath_catch.wav"
define audio.sfx_cloth = "audio/sfx_cloth.wav"
define audio.sfx_door = "audio/sfx_door.wav"

## ——— 立绘：从精灵表裁切（坐标由 tools/build_sprites.py 自动生成，勿手改） ———
image idimya base calm = im.Crop("images/idimya/sheet.png", (0, 0, 598, 1360))
image idimya base amused = im.Crop("images/idimya/sheet.png", (598, 0, 598, 1360))
image idimya base sly = im.Crop("images/idimya/sheet.png", (1196, 0, 598, 1360))
image idimya base suspicious = im.Crop("images/idimya/sheet.png", (1794, 0, 598, 1360))
image idimya base hungry = im.Crop("images/idimya/sheet.png", (2392, 0, 598, 1360))
image idimya base smile_soft = im.Crop("images/idimya/sheet.png", (2990, 0, 598, 1360))
image idimya base eyes_down = im.Crop("images/idimya/sheet.png", (0, 1360, 598, 1360))
image idimya base laugh = im.Crop("images/idimya/sheet.png", (598, 1360, 598, 1360))
image idimya base flat = im.Crop("images/idimya/sheet.png", (1196, 1360, 598, 1360))
image idimya apron calm = im.Crop("images/idimya/sheet.png", (1794, 1360, 598, 1360))
image idimya apron amused = im.Crop("images/idimya/sheet.png", (2392, 1360, 598, 1360))
image idimya apron smile_soft = im.Crop("images/idimya/sheet.png", (2990, 1360, 598, 1360))
image idimya apron sly = im.Crop("images/idimya/sheet.png", (0, 2720, 598, 1360))
image idimya apron flat = im.Crop("images/idimya/sheet.png", (598, 2720, 598, 1360))
image idimya coat calm = im.Crop("images/idimya/sheet.png", (1196, 2720, 598, 1360))
image idimya coat suspicious = im.Crop("images/idimya/sheet.png", (1794, 2720, 598, 1360))
image idimya coat sly = im.Crop("images/idimya/sheet.png", (2392, 2720, 598, 1360))
image idimya coat flat = im.Crop("images/idimya/sheet.png", (2990, 2720, 598, 1360))
image idimya ponytail calm = im.Crop("images/idimya/sheet.png", (0, 4080, 598, 1360))
image idimya ponytail amused = im.Crop("images/idimya/sheet.png", (598, 4080, 598, 1360))
image idimya ponytail hungry = im.Crop("images/idimya/sheet.png", (1196, 4080, 598, 1360))
image idimya ponytail sly = im.Crop("images/idimya/sheet.png", (1794, 4080, 598, 1360))
image idimya ponytail flat = im.Crop("images/idimya/sheet.png", (2392, 4080, 598, 1360))
image idimya hairup calm = im.Crop("images/idimya/sheet.png", (2990, 4080, 598, 1360))
image idimya hairup amused = im.Crop("images/idimya/sheet.png", (0, 5440, 598, 1360))
image idimya hairup smile_soft = im.Crop("images/idimya/sheet.png", (598, 5440, 598, 1360))
image idimya hairup sly = im.Crop("images/idimya/sheet.png", (1196, 5440, 598, 1360))
## ——— 立绘注册结束

## ——— 演出：让「她离你有多近」变成可感知的变量 ———————————————
## ——— 摆位：站姿 vs 坐姿 ————————————————————————————————————————
##
## 立绘每一格都是**站姿全身**（头顶到膝盖下，598x1360）。
## 原来只有 sprite_base 一种摆法（xalign .5 / yalign 1.0）：
##   · 高度按原始像素铺满整个 1080，等于「她比背景里的家具高一截」
##   · 底部对齐屏幕底，腿直接穿进圆桌
## 在 bistro（圆桌、她是坐着的）这一场就是灾难：
##   人超出屏幕上沿、没有坐下、脚踩在桌子中间还压不住背景。
##
## 现在分两种：
##   sprite_stand —— 站在屋里（厨房/玄关/冰箱）。缩小到 0.92 屏高，底边贴屏幕底。
##                   0.92 是为了给 120px 遮幅留出头顶位置，否则一开遮幅就削到头发。
##   sprite_seat  —— 坐在圆桌后。缩放/位置从定稿反推：
##                   assets/concept/key-visual-official.png 里脖子处丝巾宽 338px，
##                   立绘同处 284px → zoom 1.19；丝巾上沿对齐后顶端 y≈-46，
##                   但遮幅有 120px，所以上移取 44，保证头顶不被吃掉。
##                   腰以下由前景层 table_front 挡住 —— 于是「站姿立绘」看起来是坐着的。
##                   立绘本身一个像素都没改。
transform sprite_stand:
    xalign 0.5
    yalign 1.0
    zoom 0.92

transform sprite_seat:
    xalign 0.5
    yalign 0.0
    ypos 44
    zoom 1.19

## 兼容：老写法 sprite_base 现在等价于「站姿」
transform sprite_base:
    xalign 0.5
    yalign 1.0
    zoom 0.92

transform push_slow:
    zoom 1.0
    linear 26.0 zoom 1.06

transform lean_in:
    zoom 1.05
    linear 3.0 zoom 1.20

transform lean_back:
    zoom 1.06
    linear 1.6 zoom 1.0

transform flicker:
    alpha 0.06
    linear 0.9 alpha 0.13
    linear 1.4 alpha 0.07
    linear 0.7 alpha 0.15
    repeat

## ——— 启动 ———————————————————————————————————————————————
default scent = 0
default trust = 0
default doubt = 0
default promise = None
default chapter_name = ""
default seasoning = ""          # 第二章：你最后放下的那一样东西
default ch2_trust = 0           # 第二章局部计数（不影响第一章的账本）
default jars_read = 0           # 第三章：你读了几张标签
default ch3_asked = ""          # 第三章：你最后问的那个问题
default ch3_trust = 0           # 第三章局部计数

label start:

    $ chapter_name = "序章 · 重访第一夜"

    scene bistro
    with Dissolve(1.2)

    # 过场：先遮幅再开画，观众会立刻知道"这是正片"
    show bar_top at bar_in_top(0.9)
    show bar_bottom at bar_in_bottom(0.9)

    play sound sfx_bell
    pause 0.6

    note "有些邀请是不该接受的。"
    note "比如来自一个明确告诉过你「人类很好吃」的人。"

    play ambience amb_rain fadein 3.0

    jump ch0_arrive


## ============================================================
## 进场
## ============================================================

label ch0_arrive:

    scene bistro
    with Dissolve(2.0)

    show vig

    show idimya base amused at sprite_seat, push_slow
    ## 顺序要紧：桌面必须 show 在立绘**之后**（zorder 更大），
    ## 才能压在她身上，把腰以下挡掉 —— 于是"站姿立绘"看起来是坐着的。
    ## 注意不能在纯黑场景之前 show：这层不透明部分会跟着一起淡出，
    ## 变成"桌子浮在黑幕上"。
    show table_front

    note "小酒馆在一条你从没注意过的巷子里。木墙比记忆中更高，也更暗。"

    note "她已经坐在那儿了。烛台摆在她手边，一盏只够照亮两个人的火。"

    idimya "你来了。"

    idimya "我还在想，你今天会不会不敢来。"

    n "（她笑起来的时候，眼睛几乎闭成一条线。很好看。这才是最麻烦的地方。）"

    idimya "坐吧。别站那么远，我又不会——"

    idimya "……算了，这句我不说完。"

    n "（她把「不会吃你」这句话咽回去了。）"

    show idimya base amused at sprite_seat, lean_in
    with Dissolve(0.6)

    idimya "三周不见。你有没有想我？"

    menu:
        "说实话。":
            $ trust += 1
            n "「想。想到有点睡不着。」"

            show idimya base laugh at sprite_seat, lean_in
            idimya "噢——"
            idimya "这句答得太快了。快到我都不好意思不信。"

        "绕过去。":
            $ doubt += 1
            n "「我最近挺忙的。」"

            idimya "忙。"
            idimya "忙到把一个人放在心里三周，都没空想一下。"
            $ doubt += 1

        "反问她。":
            $ scent += 2
            n "「你呢？这三个月里，你约过几个人来这张桌子？」"

            show idimya base eyes_down at sprite_seat, lean_back
            with Dissolve(0.4)
            idimya "……"
            idimya "你是第一个被我问到还想反问我的。"
            idimya "我喜欢。虽然这句「喜欢」对你不算好消息。"

    jump ch0_q1


## ============================================================
## 问题一：你为什么来
## ============================================================

label ch0_q1:

    show idimya base calm at sprite_seat, push_slow
    with Dissolve(0.8)

    note "她把烛台往你那边推了一点。火苗歪了一下，她的脸暗了一半，又亮回来。"

    idimya "那我来问第一个问题。"
    idimya "你为什么来？"

    idimya "别说因为无聊。说点我信得过的。"

    menu:
        "「因为我想知道，那天你说的哪句话是真话。」":
            $ trust += 2
            n "「因为我想知道，那天你说的哪句话是真话。」"

            idimya "好问题。"
            idimya "答案是：全都不是。"
            idimya "……除了一句。你猜是哪一句？"

            n "（我不敢猜。）"

        "「因为你看起来不会伤害我。」":
            $ doubt += 2
            n "「因为你看起来不会伤害我。」"

            show idimya base flat at sprite_seat, lean_back
            idimya "「看起来」。"
            idimya "你挑了一个很聪明的词，然后把它用在了最不该用的地方。"
            $ doubt += 1

        "「因为我很饿。」":
            $ scent += 2
            $ trust += 1
            n "「因为我很饿。」"

            show idimya base hungry at sprite_seat, lean_in
            with Dissolve(0.5)

            idimya "……哈。"
            idimya "这句我要记下来。"
            idimya "你要小心，说这种话的人，我会想要多看两眼。"

    jump ch0_smell


## ============================================================
## 气味：第一个可交互段落
## ============================================================

label ch0_smell:

    show idimya base calm at sprite_seat, push_slow
    with Dissolve(0.6)

    note "你低下头。桌上的东西离你很近：烛台、一杯没动过的酒、一本合着的笔记本。"

    note "你可以闻一闻。虽然这念头听上去很不妙。"

    call screen smell_table

    note "[smell_line]"

    if smells_found >= 3:
        $ scent += 1
        idimya "你在闻。"
        idimya "……没关系。我不讨厌被闻。"
        idimya "只是你最好别闻到不该闻的那一层。"

    jump ch0_q2


## ============================================================
## 问题二：你怕我吗
## ============================================================

label ch0_q2:

    show idimya base calm at sprite_seat, push_slow
    with Dissolve(0.6)

    idimya "第二个问题。"
    idimya "你怕我吗？"

    menu:
        "「怕。」":
            $ trust += 2
            n "「怕。」"

            idimya "谢谢你没骗我。"
            idimya "怕我的人都会坐得离我很远。你却没有。"
            idimya "这说明你怕的其实不是我会做什么，而是我会怎么想你。"

        "「不怕。」":
            $ doubt += 2
            n "「不怕。」"

            idimya "你手在抖。"
            idimya "我不介意你撒谎，但请你撒得漂亮一点。"
            $ doubt += 1

        "「我怕的是自己会习惯你。」":
            $ scent += 2
            $ trust += 1
            show idimya base amused at sprite_seat, lean_in
            with Dissolve(0.5)

            n "「我怕的是自己会习惯你。」"

            idimya "……"
            show idimya base smile_soft at sprite_seat, lean_in
            idimya "这句话，是你今天晚上说的最好听的一句。"
            idimya "也是我听得最认真的一句。"
            idimya "很危险。你说的。不是我。"

    jump ch0_q3


## ============================================================
## 问题三：你希望我是什么
## ============================================================

label ch0_q3:

    show idimya base calm at sprite_seat, push_slow
    with Dissolve(0.6)

    note "烛火低了一截。她伸手把蜡油按回烛芯里，动作很慢，像在给什么东西掖被子。"

    idimya "最后一个。"
    idimya "你希望我是什么？"

    idimya "别说人。人这个答案太便宜了。"

    menu:
        "「一个会饿的人。」":
            $ trust += 2
            n "「一个会饿的人。」"

            idimya "……你把「饿了」和「人」放在一起了。"
            idimya "你知道这句话没救了我吗？"
            idimya "我本来打算今晚只喝一杯就走的。"

        "「一个我可以骗过去的东西。」":
            $ doubt += 3
            n "「一个我可以骗过去的东西。」"

            show idimya base suspicious at sprite_seat, lean_back
            with Dissolve(0.4)

            idimya "那你现在应该已经骗过去了才对。"
            idimya "为什么还坐着？"

            n "（因为我不想走。）"

        "「你本来是什么，就是什么。别为我改。」":
            $ scent += 2
            $ trust += 2
            show idimya base sly at sprite_seat, lean_in
            with Dissolve(0.6)

            n "「你本来是什么，就是什么。别为我改。」"

            idimya "……"
            idimya "上一次有人对我说这句话，我把他吃了。"
            idimya "因为他其实是在说：我希望你还是那个不会伤害我的人。"
            idimya "你不一样。你是在说：伤害我也可以。"
            idimya "……你疯了吗？"

            n "（可能是。）"

    jump ch0_reversal


## ============================================================
## 反转：这一次换我来问
## ============================================================

label ch0_reversal:

    show idimya base calm at sprite_seat, push_slow
    with Dissolve(0.6)

    note "你把菜单推回去，合上，放在她手边。"

    n "「今晚你来点。」"
    n "「不过在你点之前——我想知道，你想吃什么。」"

    show idimya base eyes_down at sprite_seat, lean_in
    with Dissolve(0.8)

    note "她的笑停了一下。不是僵住，是那种被人摸到了心口的位置、突然不知道要不要后退的停。"

    idimya "……"
    idimya "第一次有人问我这个。"
    idimya "以前来的人都只问：你会不会吃我。"

    idimya "你想听真话？"

    menu:
        "「真话。」":
            $ trust += 2
            n "「真话。」"

            idimya "真话是：我今晚什么都不想吃。"
            idimya "我来，是因为你说「下次我请你吃饭」。"
            idimya "我想看看，一个说了「下次」的人，会不会真的来。"

        "「不，我想听你骗我一次。」":
            $ scent += 1
            $ doubt += 1
            n "「不。我想听你骗我一次。」"

            idimya "骗你？"
            idimya "那我说：我想吃甜的。"
            idimya "……这句是骗你的。我不吃甜的。"

    idimya "对了。你上次说，下次要给我做点什么。"

    if promise is None:
        $ promise = "一顿饭"
        n "（你想了半天，最后说了一句「一顿饭」。）"
        idimya "嗯。一顿饭。"
    else:
        idimya "你说的那件事，我可一直记着。"
        n "（她当然记着。）"

    idimya "那就说定了。"
    idimya "下一次，你来做。我做客。"

    idimya "……不过我得提醒你一件事。"

    show vig at flicker
    with Dissolve(0.4)

    idimya "我这个人，很容易对一顿饭失望。"

    jump ch0_ending


## ============================================================
## 三档结局：她记住你的方式
## ============================================================

label ch0_ending:

    show idimya base calm at sprite_seat, push_slow
    with Dissolve(0.8)

    if doubt >= trust + 1:

        $ chapter_name = "结局 A · 她记住了你的谎话"
        jump end_lie

    elif scent >= trust + 1:

        $ chapter_name = "结局 C · 她记住了你的味道"
        jump end_scent

    else:

        $ chapter_name = "结局 B · 她记住了你的名字"
        jump end_name


label end_lie:

    show idimya base suspicious at sprite_seat
    with Dissolve(0.4)

    note "她送你到门口，替你拉开门，冷风灌进来。"

    idimya "今天很好。"
    idimya "你说话的时候，一直在算我会不会信。"
    idimya "我不介意。真的。"
    idimya "我只是有点难过——你明明可以只说一句真话的。"

    idimya "下次别来了。"

    note "你走出巷子。手机在口袋里震了一下。"
    note "Fumble：「伊迪米娅 解除匹配」"

    note "你回头。窗里那盏烛火还亮着。"
    note "桌上多了一个杯子。属于别人的杯子。"

    $ persistent.endings_lie = True
    hide table_front          # 圆桌场景结束，桌面层必须收掉
    jump ch0_after


label end_name:

    show idimya base calm at sprite_seat
    with Dissolve(0.4)

    note "她陪你走到巷口，站定，没有跟出来。"

    idimya "你的名字。"
    idimya "……我一直没问。现在问，会不会太晚？"

    n "（你说了。）"

    idimya "我记住了。"
    idimya "我不会念错。我这辈子只记两种东西：味道，和名字。"
    idimya "名字比味道难记多了。你该庆幸。"

    idimya "下次来的时候，别敲门。直接进来。"
    idimya "……我会把所有不想让你看见的东西，都收起来。"

    note "她转身回去了。你站在原地，很久没动。"
    note "你不知道那算是温柔，还是警告。"

    $ persistent.endings_name = True
    hide table_front          # 圆桌场景结束，桌面层必须收掉
    jump ch0_after


label end_scent:

    show idimya base sly at sprite_seat
    with Dissolve(0.4)

    note "她没送你。你走到门口时，她在背后开口。"

    idimya "等一下。"

    note "你回头。她还在座位上，一只手撑着下巴，火光照在锁骨上。"

    idimya "你今天吃了什么？"
    idimya "……不用回答。我只是想确认一下，这个味道是你自己的。"
    idimya "不是别人的。"

    idimya "回去吧。"
    idimya "我们还会见的。"
    idimya "我认路，也认味道。"

    note "巷子很长。你走到尽头才发现，自己一路上都在屏着呼吸。"

    $ persistent.endings_scent = True
    hide table_front          # 圆桌场景结束，桌面层必须收掉
    jump ch0_after


## ============================================================
## 章末
## ============================================================

label ch0_after:

    $ renpy.save_persistent()

    hide table_front
    scene black
    with Dissolve(1.6)

    scene kitchen
    with Dissolve(1.4)

    show vig
    show idimya apron smile_soft at sprite_base, push_slow

    note "第一章 · 门铃"

    note "她站在厨房里，背对着你。围裙的带子在腰后打了个很随意的结。"

    note "砧板上有什么东西，正在被切成很均匀的片。"

    note "她没有回头。"

    idimya "门没锁。"

    idimya "……我说过你不用敲的。"

    centered "{size=18}{color=#8b7b69}本次周目 · 她记住你的方式{/color}{/size}\n\n{color=#d9a05f}[chapter_name]{/color}"

    jump ch1_title


## ============================================================
## 第一章 · 门铃
## ============================================================
## 这一章的重点不是「她会不会吃你」，而是「她允许你看到多少」。
## 采用了 L2 分层动态立绘（丝巾/刘海/hair 摆动），并在厨房段落
## 用围裙造型 + 背对你（用 lean_back + flat 表现）。

label ch1_title:

    $ chapter_name = "第一章 · 门铃"

    scene black
    with Dissolve(1.2)

    note "第一章"
    note "门铃"

    jump ch1_genkan


label ch1_genkan:

    scene genkan
    with Dissolve(1.8)

    play ambience amb_rain fadein 3.0

    show vig

    note "你按了门铃。"

    note "里面没有脚步声。过了很久，门自己开了一条缝——像是有人早就站在门后，只是等你先按下去。"

    show idimya hairup calm at sprite_base, push_slow
    with Dissolve(0.8)

    show idimya hairup smile_soft at sprite_base
    with Dissolve(0.5)

    note "她头发是随便盘起来的，几缕落在颈侧。没有化妆。"
    note "看到是你的时候，她眼睛里有一点东西亮了一下。很快，然后就没了。"

    show idimya hairup calm at sprite_base
    with Dissolve(0.6)

    idimya "你迟到了四分钟。"

    n "（她没有看表。）"

    idimya "进来吧。鞋子放那边，别踩到垫子外面。"

    note "玄关很窄。你侧着身进来，闻到炖东西的味道——很浓，很甜，压着一层别的什么。"

    idimya "外套挂那儿。"

    menu:
        "照做。":
            $ trust += 1
            note "你把外套挂在那件长外套旁边。它的下摆有一块洗过很多次的痕迹。"

            show idimya hairup amused at sprite_base, push_slow
            with Dissolve(0.5)

            idimya "……好。"
            idimya "你比我想的听话。"

        "先问一句：那件外套是谁的？":
            $ scent += 2
            $ doubt += 1
            n "「那件外套，是谁的？」"

            show idimya hairup calm at sprite_base, lean_back
            with Dissolve(0.4)

            show idimya hairup sly at sprite_base, lean_in
            with Dissolve(0.5)

            idimya "……"
            idimya "上一个在这里挂过外套的人。"
            idimya "他没有拿走。"
            idimya "你可以理解成我留了个纪念。"

            note "她没有笑。这比笑更糟。"

        "不脱，站门口。":
            $ doubt += 2
            n "（你没有动。）"

            show idimya hairup calm at sprite_base, lean_back
            with Dissolve(0.4)

            idimya "行。那就站着。"
            idimya "饭凉了会很难吃，不过这是你的选择。"

            note "她转身走进厨房。你站在玄关，看着自己的鞋，忽然意识到——她一次都没催你。"

            note "过了大概一分钟，你还是脱了鞋。"

    jump ch1_kitchen


label ch1_kitchen:

    scene kitchen
    with Dissolve(1.6)

    play ambience amb_kitchen fadein 3.5

    show vig

    show idimya apron calm at sprite_base, push_slow
    with Dissolve(0.8)

    note "厨房比你想象的小，也比你想的干净。干净到不像有人天天在这里做饭。"

    note "砧板上有一块切得很整齐的东西。你只看了一眼，就把视线移开了。"

    idimya "别站那儿。过来，帮我把这个端过去。"

    note "她背对着你，围裙带子在腰后打了个很随便的结。"

    idimya "我问你一件事。"

    idimya "上次你说，下次你来做。还算数吗？"

    menu:
        "算数。现在就做。":
            $ trust += 2
            $ promise = "现在做"
            n "「算数。现在就可以。」"

            show idimya apron smile_soft at sprite_base, lean_in
            with Dissolve(0.5)

            idimya "现在？"
            idimya "……好。那这顿我来吃。"

            note "她往旁边让开半步，把灶台前的位置让给你。这是今晚她第一次把什么东西让给你。"

            jump ch1_cook

        "算数，但改天。":
            $ doubt += 1
            n "「算数。但改天吧，今天是你做。」"

            idimya "改天。"
            idimya "……行。我记性好，你知道的。"

            note "她把「改天」两个字说得很轻，像在把它放进某个抽屉。"

            jump ch1_knife

        "反悔。我做不到。":
            $ scent += 1
            $ trust += 1
            n "「我做不到。我那天是随口说的。」"

            show idimya apron flat at sprite_base, lean_back
            with Dissolve(0.4)

            note "她停了很久。锅里的东西在响。"

            idimya "谢谢你没继续骗我。"
            idimya "……但我现在有点难过。这很奇怪，对吧？"
            idimya "我吃人的时候都不会难过。"

            jump ch1_knife


label ch1_cook:

    note "你打开冰箱拿东西。"

    scene fridge
    with Dissolve(1.0)

    play ambience amb_fridge fadein 2.5

    show vig

    note "冷光打在你脸上。"
    note "架子上很整齐。非常整齐。每一格都标了日期。"

    note "你数了一下。有十七个。"
    note "不是十七盒东西。是十七个日期。"

    menu:
        "关上门，装作没看见。":
            $ doubt += 1
            n "（你把门关上了。）"

            scene kitchen
            with Dissolve(0.8)
            show vig
            show idimya apron calm at sprite_base, push_slow

            idimya "找到你要的了？"
            n "「找到了。」"
            idimya "你脸色不太好。"
            idimya "……厨房灯有点暗，对吧。"

        "问她：这些日期是什么？":
            $ scent += 2
            $ trust += 2
            n "「这些日期是什么？」"

            scene kitchen
            with Dissolve(0.8)
            show vig
            show idimya apron smile_soft at sprite_base, lean_in

            idimya "……你是第一个问的人。"
            idimya "以前的人要么不打开，要么打开了就再也没说过话。"
            idimya "那些是我记得的日子。有些是好的，有些不是。"
            idimya "我吃下去的东西，我不想忘记它们。这是我能给的最起码的东西。"

            n "（你不知道该说这是温柔还是残忍。）"

        "拿出一盒，放到她面前。":
            $ scent += 3
            $ doubt += 1

            n "（你把最里面的那一盒拿出来，放在她手边的台面上。）"

            scene kitchen
            with Dissolve(0.8)
            show vig
            show idimya apron flat at sprite_base, lean_back

            note "她低头看着那盒东西，很久没有动。"

            idimya "……你知道你在做什么吗。"
            n "「不知道。」"
            idimya "很好。至少这句是真话。"
            idimya "把它放回去。"

            note "你把盒子放回去，关上门。冷光消失的那一刻，厨房忽然显得很暖。"

    jump ch1_knife


label ch1_knife:

    scene kitchen
    with Dissolve(1.0)

    show vig
    show idimya apron calm at sprite_base, push_slow

    note "她把刀放下了。放得很轻，几乎没有声音。"

    idimya "饭还要一会儿。"
    idimya "要不要先坐下。"

    note "你这才发现，厨房里其实只有一把椅子。"

    menu:
        "坐。":
            $ trust += 1
            note "你坐下了。她站在你旁边，靠着台面，低头看你。"

            show idimya apron smile_soft at sprite_base, lean_in
            with Dissolve(0.6)

            idimya "这样很好。"
            idimya "我喜欢矮一点的人。不，不是身高。"
            idimya "是愿意坐下来的人。"

        "问她：你站着，我坐着，这算什么？":
            $ scent += 2
            n "「你站着，我坐着。这算什么？」"

            show idimya apron sly at sprite_base, lean_in
            with Dissolve(0.5)

            idimya "算我在让你。"
            idimya "我很少让人。你要珍惜。"

        "站着。保持距离。":
            $ doubt += 2
            note "你没有坐。她也没有再让。"

            show idimya apron flat at sprite_base, lean_back
            with Dissolve(0.4)

            idimya "……好。"
            idimya "那我们就这样说话。"

            note "接下来的十分钟，锅在响，你们谁都没有再开口。"

    jump ch1_end


label ch1_end:

    # 过场：先给窗，再给人。中间那 2 秒空白就是"一整夜过去了"。
    scene window_dawn
    with Dissolve(2.6)

    play ambience amb_morning fadein 4.0

    show vig

    note "雨停了。"
    note "窗上有一个圆形的痕，是很久以前有人用手擦开的，擦得刚好够看出去。"

    pause 1.2

    scene morning
    with Dissolve(2.0)

    show vig

    note "后来你不太记得那顿饭是怎么吃完的。"
    note "你只记得窗外开始亮的时候，她还坐在那儿，没有催你走。"

    show idimya ponytail calm at sprite_base, push_slow
    with Dissolve(1.0)

    idimya "天亮了。"
    idimya "……你要走的话，现在是最好的时候。"

    menu:
        "「我不走。」":
            $ trust += 2
            n "「我不走。」"

            show idimya ponytail amused at sprite_base, lean_in
            with Dissolve(0.6)

            idimya "你知道你在说什么吗。"
            idimya "天亮了，我就没那么好看了。"
            idimya "……而且我饿的时候，也不再那么客气。"

            n "「我知道。」"

            idimya "……"
            idimya "那你把外套挂回去吧。"

            note "她说了这句话，就去洗碗了。背对着你。"
            note "你听见水声里夹着一句很轻的话，轻到可能是你听错了。"

            $ persistent.ch1_stay = True

        "「我该走了。」":
            $ doubt += 1
            n "「我该走了。」"

            show idimya ponytail flat at sprite_base, lean_back
            with Dissolve(0.5)

            idimya "嗯。"
            idimya "路上小心。"

            note "她送都没有送。你穿鞋的时候，听到厨房传来水声。"
            note "还有一声很轻的、像是把什么东西放回柜子里的声音。"

            $ persistent.ch1_leave = True

        "问她：「下一次，还是我按门铃吗？」":
            $ scent += 2
            $ trust += 1
            n "「下一次，还是我按门铃吗？」"

            show idimya ponytail amused at sprite_base, lean_in
            with Dissolve(0.6)

            idimya "不。"
            idimya "下一次，你自己开门。"

            note "她说这句话的时候，把一把钥匙推到你面前。"
            note "钥匙是温的。她大概握了很久。"

            $ promise = "自己开门"
            $ persistent.ch1_key = True

    $ renpy.save_persistent()

    scene black
    with Dissolve(1.8)

    if doubt >= trust + 2:
        $ chapter_name = "第一章结局 · 她记住了你看见了什么"
    elif promise == "自己开门":
        $ chapter_name = "第一章结局 · 她给了你钥匙"
    else:
        $ chapter_name = "第一章结局 · 她记住了你留下来"

    centered "{size=18}{color=#8b7b69}第一章 · 完{/color}{/size}\n\n{color=#d9a05f}[chapter_name]{/color}"

    jump ch2_title

## ——————————————————————————————————————————————————————————————
## Chapter 2 — 刀与糖
## 核心：一把真的刀、一个 30 秒的调味交互、一次"被看见"的体面
## ——————————————————————————————————————————————————————————————

label ch2_title:

    stop ambience fadeout 1.5
    scene black
    with Dissolve(1.4)

    # 切章：先全黑，再让两条遮幅滑进来 —— 这一下就是"过场"
    show bar_top at bar_in_top(0.7)
    show bar_bottom at bar_in_bottom(0.7)

    centered "{size=17}{color=#8b7b69}第二章 · 刀与糖{/color}\n\n{size=15}{color=#6b5c4d}一起做饭。\n调味不是靠菜谱，是靠闻。{/color}"

    # 第一章的分支在这里收束：三档进入语气不同，但都通向同一间厨房
    if persistent.ch1_key:
        note "你是用自己那把钥匙进来的。"
        note "门开的时候，她正在切东西，没有回头。"
    elif persistent.ch1_leave:
        note "你走了。然后又回来了。"
        note "你自己也说不清是哪一步开始回头的。"
    else:
        note "你没有走。"
        note "天亮以后你睡了一会儿，醒来的时候，厨房里已经有声音了。"

    # 遮幅留在画面上：这一章全程电影画幅
    scene kitchen
    with Dissolve(1.6)

    play ambience amb_kitchen fadein 3.5

    show vig
    show idimya apron calm at sprite_base, push_slow
    with Dissolve(1.0)

    note "她刚回来，大衣还没脱。袖口有一点潮。"

    show idimya coat calm at sprite_base
    with Dissolve(0.8)

    idimya "外面还在下。"
    idimya "我在楼下站了一会儿。"

    n "（她没有说在等谁。）"

    show idimya coat suspicious at sprite_base
    with Dissolve(0.5)

    idimya "你身上的味道变了。"
    idimya "不是不好。只是变了。"

    show idimya coat sly at sprite_base, lean_in
    with Dissolve(0.5)

    idimya "你一直看着这件衣服。"
    idimya "喜欢的话，可以拿走。"
    idimya "……我开玩笑的。"

    show idimya coat flat at sprite_base
    with Dissolve(0.6)

    note "她把大衣挂到椅背上。椅背已经很旧了，挂着的地方磨得发亮。"

    show idimya apron calm at sprite_base, push_slow
    with Dissolve(1.0)

    note "台上摆着两样东西：一把刀，和一小碟糖。"
    note "刀是厨房里最锋利的那把。糖是粗糙的黄糖，结成块。"

    idimya "选一个。"
    n "「……什么？」"
    idimya "今天你先动刀，还是先动糖。"
    idimya "顺序会决定这顿饭是什么味道。"
    idimya "也会决定我今晚怎么想你。"

    menu:
        "先拿刀。":
            $ ch2_trust += 1
            $ scent += 1
            jump ch2_knife

        "先拿糖。":
            $ ch2_trust += 2
            $ trust += 1
            jump ch2_sugar

        "两样都不拿，先问她：你希望我选哪个？":
            $ scent += 2
            $ doubt += 1
            jump ch2_ask


label ch2_knife:

    note "你握住了刀柄。比想象的沉。"

    show idimya apron sly at sprite_base, lean_in
    with Dissolve(0.5)

    idimya "手很稳。"
    idimya "稳的人一般不太诚实。"
    n "「为什么？」"
    idimya "因为稳是练出来的。练过的人，都有不想让人看见的部分。"

    play sound sfx_knife
    note "她绕到你身后，手覆在你的手背上，带着你切下第一刀。"
    play sound sfx_heartbeat
    note "她的呼吸落在你耳后。刀很凉，她的手很热。"

    show idimya ponytail hungry at sprite_base, lean_in
    with Dissolve(0.7)

    idimya "切的时候别看刀。看你要切的东西。"
    idimya "看刀的人会切到手。看东西的人不会。"

    n "（她说这话的时候在看着你的脖子。）"

    $ ch2_trust += 1
    jump ch2_season


label ch2_sugar:

    note "你捏起一块黄糖。它在你手指间有点黏。"

    show idimya apron smile_soft at sprite_base, lean_in
    with Dissolve(0.5)

    idimya "……你选了这个。"
    n "「选错了？」"
    idimya "没有错。只是很少有人先选糖。"
    idimya "大家都会先拿刀。因为刀看起来比较像答案。"

    note "她把糖接过去，指尖擦过你的掌心。"
    note "然后她把糖放进嘴里，含了一下，才丢进锅里。"

    show idimya ponytail sly at sprite_base, lean_in
    with Dissolve(0.6)

    idimya "这样比较甜。"
    idimya "你要不要尝尝是不是真的。"

    n "（她在等你回答。她知道你在想什么，她也知道你知道。）"

    $ ch2_trust += 2
    jump ch2_season


label ch2_ask:

    n "「你希望我选哪个？」"

    show idimya apron flat at sprite_base
    with Dissolve(0.4)

    note "她停了一下。锅里的油开始响。"

    idimya "……你把问题还给我了。"
    idimya "上次也有一个人这样做。"
    idimya "他后来活了很久。"

    n "（「活了很久」这个词，从她嘴里说出来，意思和你想的不一样。）"

    show idimya apron calm at sprite_base, push_slow
    with Dissolve(0.6)

    idimya "选糖吧。"
    idimya "今天我想甜一点。"

    $ trust += 2
    jump ch2_season


label ch2_season:

    scene kitchen
    with Dissolve(0.6)

    show vig
    show idimya apron calm at sprite_base

    scene kitchen_close
    with Dissolve(1.2)

    show vig at flicker

    note "锅热了。她把三样东西推到你面前：盐、糖、还有一小瓶深色的东西。"
    note "瓶子没有标签。但你已经知道她习惯在每样东西上写日期——这一瓶是唯一没有的。"

    idimya "调味不是靠菜谱，是靠闻。"
    idimya "你先闻。闻完再决定放什么。"
    idimya "放错了也没关系。我会吃完。"

    call screen seasoning_pick

    if _return == "salt":
        $ seasoning = "盐"
        $ ch2_trust += 1
        note "你放了一小撮盐。"
        note "她尝了一口，眉毛动了一下。"
        idimya "咸的。"
        idimya "咸是诚实。你不会骗舌头。"
    elif _return == "sugar":
        $ seasoning = "糖"
        $ ch2_trust += 1
        note "你放了一勺糖。"
        note "她尝了一口，很轻地笑了一下。"
        idimya "甜的。"
        idimya "甜是讨好。你在讨好我。"
        n "「有用吗。」"
        idimya "有用。"
    else:
        $ seasoning = "那一瓶没有标签的东西"
        $ scent += 3
        $ doubt += 2
        note "你拿起了那瓶没有标签的东西。"
        note "拔开瓶塞的一瞬间，整个厨房的气味都变了。"
        note "很像下雨前的土。也很像她身上靠近脖子那里的味道。"
        note "她突然伸手，按住了你的手腕。不快，但很稳。"
        idimya "……你怎么知道是这个。"
        n "「我不知道。我只是闻到了。」"
        idimya "……"
        idimya "那你比我以为的要危险。"
        show idimya apron sly at sprite_base, lean_in
        with Dissolve(0.5)
        idimya "不过没关系。我喜欢危险的东西。"
        idimya "它们比较好吃。"

    $ renpy.save_persistent()

    scene kitchen
    with Dissolve(1.4)

    jump ch2_end


label ch2_end:

    scene kitchen
    with Dissolve(1.0)

    show vig
    show idimya apron smile_soft at sprite_base, push_slow

    note "菜盛出来了。两盘。她那一盘比你的小。"

    n "「你不饿？」"
    idimya "我饿。"
    idimya "但今天我想看你吃。"

    note "你低头吃了一口。味道很怪。"
    note "你说不清是盐放多了，还是糖放少了，还是那瓶东西本来就不该出现在菜里。"
    note "但这是你很久以来，第一次把一整盘东西吃完。"

    show idimya apron amused at sprite_base, lean_in
    with Dissolve(0.6)

    idimya "吃完了。"
    idimya "你知道这意味着什么吗。"
    n "「……什么？」"
    idimya "意味着下次你还会来。"

    note "她说得很轻，像在说一件已经发生的事。"

    # 用本章自己的账（ch2_trust + 放下的那一样），不掺第一章的累计值，
    # 否则玩家一路照做也会被判成"她早就看穿你了"。
    if seasoning == "那一瓶没有标签的东西":
        $ chapter_name = "第二章结局 · 她已经知道你会回来"
        $ persistent.ch2_seen = True
    elif ch2_trust >= 3:
        $ chapter_name = "第二章结局 · 她给你留了半盘"
        $ persistent.ch2_shared = True
    else:
        $ chapter_name = "第二章结局 · 她记住了你放的那一撮"
        $ persistent.ch2_taste = True

    $ renpy.save_persistent()

    stop ambience fadeout 2.2

    scene black
    with Dissolve(1.8)

    hide bar_top
    hide bar_bottom
    with Dissolve(0.8)

    centered "{size=18}{color=#8b7b69}第二章 · 完{/color}{/size}\n\n{color=#d9a05f}[chapter_name]{/color}"

    jump ch3_title

## ——————————————————————————————————————————————————————————————
## Chapter 3 — 十七个日期
## 核心：冰箱。十七个罐子，十七个日期。她终于愿意解释。
## 这一章不吓人，它是"明白了"——明白了比吓人难受得多。
## ——————————————————————————————————————————————————————————————

label ch3_title:

    stop ambience fadeout 2.0
    with Dissolve(1.2)

    centered "{size=17}{color=#8b7b69}第三章 · 十七个日期{/color}\n\n{size=15}{color=#6b5c4d}你终于问出了那个问题。\n她也终于愿意回答。{/color}"

    show bar_top at bar_in_top(0.8)
    show bar_bottom at bar_in_bottom(0.8)

    scene fridge
    with Dissolve(2.0)

    play ambience amb_fridge fadein 3.0

    show vig

    # 开头先不说话，让冰箱自己响三秒
    pause 2.6

    note "又过了几个晚上。"

    # 她记得你上次放下的东西。这一句让"选择"跨章生效，玩家会背脊一凉。
    if seasoning == "盐":
        note "桌上还放着那罐盐。位置没动过。"
        note "罐子旁边压着一张小纸片，上面只写了两个字：诚实。"
    elif seasoning == "糖":
        note "桌上放着一小碟黄糖，边缘的黏已经干了。"
        note "碟子旁边压着一张小纸片，上面只写了两个字：讨好。"
    elif seasoning == "那一瓶没有标签的东西":
        note "那个没有标签的瓶子不见了。"
        note "架子空出一格，正好是它的形状。"
    else:
        note "桌上什么都没有。干净得像没有人做过饭。"

    note "有些事你一直没问。不是因为不想知道，是因为你知道问了就得记住。"

    play sound sfx_door

    note "今晚她不在厨房。"
    note "你听见浴室的水声。然后你站在冰箱前面，手已经放在门上了。"

    play sound sfx_breath_soft

    note "你打开了门。"

    menu:
        "读最上面那一排的日期。":
            $ jars_read += 2
            $ scent += 2
            jump ch3_read_top

        "读最下面那一排。":
            $ jars_read += 2
            $ doubt += 1
            jump ch3_read_bottom

        "什么都不读。只是站着，让它开在那里。":
            $ ch3_trust += 2
            jump ch3_stand


label ch3_read_top:

    note "最上面一排，从左到右，日期是倒着的。"
    note "最近的在左边，最旧的在右边。像有人一直在往前面插。"

    show idimya base calm at sprite_base, push_slow
    with Dissolve(1.2)

    note "水声停了。"

    idimya "你在看日期。"
    n "「……嗯。」"

    idimya "那你数到第几个了。"
    n "「四个。」"

    idimya "……四个。"
    idimya "那还行。"

    note "她说「还行」的时候，语气像是在说一件可以挽回的事。"

    $ ch3_trust += 1
    jump ch3_ask


label ch3_read_bottom:

    note "最下面一排的日期，和上面不一样。"
    note "上面的日期之间隔了几天，几周，甚至一年。"
    note "最下面那一排——它们隔得太近了。"

    play sound sfx_breath_catch

    note "你数了一下。七个。"
    note "七个日期，挤在四十一天里。"

    show idimya base flat at sprite_base
    with Dissolve(0.8)

    note "你已经知道那不是「记得的日子」了。那是「吃过的日子」。"

    idimya "……你数了下面的。"

    note "她没有生气。这比生气更让人害怕。"

    idimya "上面那排是我舍不得忘的。"
    idimya "下面那排是我没法忘的。"

    $ doubt += 2
    $ scent += 1
    jump ch3_ask


label ch3_stand:

    note "你什么都没读。"
    note "你只是站在那里，让冷光打在你脸上，闻到十七种不同的、被封起来的气味。"

    play sound sfx_breath_soft

    show idimya base calm at sprite_base, push_slow
    with Dissolve(1.4)

    note "她站在厨房门口，头发还是湿的。"

    idimya "你没有打开任何一个。"
    n "「没有。」"

    idimya "为什么。"

    n "「因为我不想只挑一个知道。」"

    note "她很久没有说话。"

    show idimya base eyes_down at sprite_base
    with Dissolve(0.7)

    idimya "……你这样很麻烦。"
    idimya "我准备了很多种回答，一种都用不上。"

    $ ch3_trust += 2
    $ trust += 2
    jump ch3_ask


label ch3_ask:

    scene fridge
    with Dissolve(0.8)

    show vig
    show idimya base calm at sprite_base

    note "她把冰箱门关上了。很轻。"
    note "厨房一下子安静下来，只剩下压缩机的声音。"

    note "她吸了一口气，很轻，但你听见了。"

    play sound sfx_breath_soft

    idimya "问吧。"
    idimya "你今晚只可以问一个问题。我会回答。"
    idimya "但我不会说第二次。"

    menu:
        "「那十七个日期里，有几个是我们认识之后？」":
            $ ch3_asked = "after"
            $ scent += 3
            $ ch3_trust += 1
            jump ch3_answer_after

        "「你吃下去之后，会记得多久？」":
            $ ch3_asked = "memory"
            $ ch3_trust += 1
            jump ch3_answer_memory

        "「如果有一天我变成其中一个，你会写哪一天？」":
            $ ch3_asked = "you"
            $ scent += 2
            $ doubt += 2
            jump ch3_answer_you


label ch3_answer_after:

    show idimya base amused at sprite_base, lean_in
    with Dissolve(0.7)

    idimya "一个。"
    n "「……一个？」"
    idimya "只有一个。"
    play sound sfx_breath_catch

    idimya "你认识我以后，我只吃过一次。"

    n "（你想起第一章那个晚上。厨房里有一把椅子。她一直站着。）"

    idimya "那天我在楼下站了一会儿。"
    idimya "我本来不是去等你。"

    note "她转过头，看着冰箱。"

    idimya "所以你现在知道，为什么那天我让你把外套挂回去了。"

    show idimya base eyes_down at sprite_base
    with Dissolve(0.6)

    idimya "空着的地方，总得挂点什么。"

    $ trust += 3
    jump ch3_end


label ch3_answer_memory:

    show idimya base calm at sprite_base
    with Dissolve(0.6)

    idimya "很久。"
    idimya "比人记得自己的名字还久。"

    n "「那你会想起来的是味道，还是那个人？」"

    show idimya base suspicious at sprite_base, lean_in
    with Dissolve(0.5)

    idimya "我刚刚说了，你只能问一个问题。"

    pause 1.0

    show idimya base smile_soft at sprite_base, lean_in
    with Dissolve(0.9)

    idimya "……味道先回来。"
    idimya "人是后来的。"
    idimya "有时候人回来得很晚，晚到我已经不知道该把它放在哪一排。"

    note "你听懂了：最下面那一排，就是那些「人回来得太晚」的罐子。"

    $ scent += 2
    $ trust += 2
    jump ch3_end


label ch3_answer_you:

    show idimya base flat at sprite_base
    with Dissolve(0.5)

    note "她看着你，看了很久。"
    note "久到你能听见自己耳朵里的血流声。"

    play sound sfx_heartbeat

    show idimya base sly at sprite_base, lean_in
    with Dissolve(0.8)

    idimya "今天的日期。"
    idimya "……我开玩笑的。"

    note "她没有笑。"

    show idimya base eyes_down at sprite_base
    with Dissolve(0.7)

    idimya "我不会写日期。"
    idimya "我会把你放在上面那一排，然后永远不打开。"

    n "（你不知道这算不算被爱。）"

    $ doubt += 1
    $ trust += 2
    jump ch3_end


label ch3_end:

    scene kitchen
    with Dissolve(1.2)

    play ambience amb_kitchen fadein 3.0

    show vig
    show idimya apron calm at sprite_base, push_slow
    with Dissolve(0.8)

    note "后来她去烧水。你坐在那把唯一的椅子上。"

    if seasoning == "盐":
        idimya "上次那盘咸了。"
        idimya "我后来又做了一遍，还是咸。"
        idimya "……我大概是想再听你说一次真话。"
    elif seasoning == "糖":
        idimya "上次那盘太甜，我吃得很慢。"
        idimya "不是因为不好吃。是因为我不想吃完。"
    elif seasoning == "那一瓶没有标签的东西":
        idimya "那瓶东西我扔了。"
        idimya "留在家里，我每天都会想再闻一次。"
    else:
        pass

    play sound sfx_cloth

    show idimya apron smile_soft at sprite_base, lean_in
    with Dissolve(0.7)

    idimya "你今晚不走，对吧。"

    note "这不是问句。"

    menu:
        "「不走。」":
            $ ch3_trust += 2
            $ trust += 2
            jump ch3_stay

        "「我明天要上班。」":
            $ ch3_trust += 1
            jump ch3_leave

        "「你先告诉我，你在楼下等的是谁。」":
            $ ch3_asked = "who"
            $ scent += 2
            $ doubt += 2
            jump ch3_who


label ch3_stay:

    show idimya apron amused at sprite_base, lean_in
    with Dissolve(0.6)

    idimya "很好。"
    idimya "那我把沙发收拾一下。"

    n "「……沙发？」"
    idimya "沙发。"
    idimya "你以为是什么。"

    note "她笑起来的时候，你几乎忘了冰箱里有什么。"

    $ chapter_name = "第三章结局 · 她给了你沙发"
    $ persistent.ch3_sofa = True
    jump ch3_finish


label ch3_leave:

    show idimya apron flat at sprite_base
    with Dissolve(0.5)

    idimya "嗯。"
    idimya "上班要紧。"

    note "她说得很平静。平静得像早就知道你会这么说。"

    show idimya apron smile_soft at sprite_base, lean_in
    with Dissolve(0.8)

    idimya "明天也是这个时间？"
    n "「……你不问我为什么还来？」"
    idimya "不问。"
    idimya "问了你就不来了。"

    $ chapter_name = "第三章结局 · 她算准了你会回来"
    $ persistent.ch3_counted = True
    jump ch3_finish


label ch3_who:

    play sound sfx_breath_catch

    show idimya apron flat at sprite_base
    with Dissolve(0.4)

    note "空气停了半秒。"

    show idimya apron sly at sprite_base, lean_in
    with Dissolve(0.7)

    idimya "……你今晚的问题已经用完了。"
    idimya "但这个问题，我可以免费回答。"

    pause 1.2

    play sound sfx_breath_catch

    idimya "我在楼下等的，从来都是同一个人。"

    note "她说完就去洗杯子了。水声很大。"

    n "（你不知道「同一个人」指的是谁。你只知道，她没有看你。）"

    $ chapter_name = "第三章结局 · 她等的从来是同一个人"
    $ persistent.ch3_same = True
    jump ch3_finish


label ch3_finish:

    $ renpy.save_persistent()

    stop ambience fadeout 2.4

    scene black
    with Dissolve(1.8)

    hide bar_top
    hide bar_bottom
    with Dissolve(0.7)

    centered "{size=18}{color=#8b7b69}第三章 · 完{/color}{/size}\n\n{color=#d9a05f}[chapter_name]{/color}"

    centered "{size=17}{color=#8b7b69}第四章 · 早餐{/color}\n\n{size=15}{color=#6b5c4d}天亮了。桌上摆着两副碗筷。\n一副是你的。另一副，昨天晚上就在那里。\n\n（制作中）{/color}"

    return
