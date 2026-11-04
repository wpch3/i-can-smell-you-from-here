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
image black = Solid("#000000")

## ——— 演出：让「她离你有多近」变成可感知的变量 ———————————————
transform push_slow:
    zoom 1.0
    linear 26.0 zoom 1.06

transform lean_in:
    zoom 1.05
    linear 3.0 zoom 1.20 xalign 0.5 yalign 0.42

transform lean_back:
    zoom 1.02
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

label start:

    $ chapter_name = "序章 · 重访第一夜"

    scene kv
    with Dissolve(1.2)

    note "有些邀请是不该接受的。"
    note "比如来自一个明确告诉过你「人类很好吃」的人。"

    jump ch0_arrive


## ============================================================
## 进场
## ============================================================

label ch0_arrive:

    scene kv
    with Dissolve(2.0)

    show vig

    show kv at push_slow

    note "小酒馆在一条你从没注意过的巷子里。木墙比记忆中更高，也更暗。"

    note "她已经坐在那儿了。烛台摆在她手边，一盏只够照亮两个人的火。"

    idimya "你来了。"

    idimya "我还在想，你今天会不会不敢来。"

    n "（她笑起来的时候，眼睛几乎闭成一条线。很好看。这才是最麻烦的地方。）"

    idimya "坐吧。别站那么远，我又不会——"

    idimya "……算了，这句我不说完。"

    n "（她把「不会吃你」这句话咽回去了。）"

    show kv at lean_in
    with Dissolve(0.6)

    idimya "三周不见。你有没有想我？"

    menu:
        "说实话。":
            $ trust += 1
            n "「想。想到有点睡不着。」"

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

            show kv at lean_back
            with Dissolve(0.4)
            idimya "……"
            idimya "你是第一个被我问到还想反问我的。"
            idimya "我喜欢。虽然这句「喜欢」对你不算好消息。"

    jump ch0_q1


## ============================================================
## 问题一：你为什么来
## ============================================================

label ch0_q1:

    show kv at push_slow
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

            idimya "「看起来」。"
            idimya "你挑了一个很聪明的词，然后把它用在了最不该用的地方。"
            $ doubt += 1

        "「因为我很饿。」":
            $ scent += 2
            $ trust += 1
            n "「因为我很饿。」"

            show kv at lean_in
            with Dissolve(0.5)

            idimya "……哈。"
            idimya "这句我要记下来。"
            idimya "你要小心，说这种话的人，我会想要多看两眼。"

    jump ch0_smell


## ============================================================
## 气味：第一个可交互段落
## ============================================================

label ch0_smell:

    show kv at push_slow
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

    show kv at push_slow
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
            show kv at lean_in
            with Dissolve(0.5)

            n "「我怕的是自己会习惯你。」"

            idimya "……"
            idimya "这句话，是你今天晚上说的最好听的一句。"
            idimya "也是我听得最认真的一句。"
            idimya "很危险。你说的。不是我。"

    jump ch0_q3


## ============================================================
## 问题三：你希望我是什么
## ============================================================

label ch0_q3:

    show kv at push_slow
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

            show kv at lean_back
            with Dissolve(0.4)

            idimya "那你现在应该已经骗过去了才对。"
            idimya "为什么还坐着？"

            n "（因为我不想走。）"

        "「你本来是什么，就是什么。别为我改。」":
            $ scent += 2
            $ trust += 2
            show kv at lean_in
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

    show kv at push_slow
    with Dissolve(0.6)

    note "你把菜单推回去，合上，放在她手边。"

    n "「今晚你来点。」"
    n "「不过在你点之前——我想知道，你想吃什么。」"

    show kv at lean_in
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

    show kv at push_slow
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
    jump ch0_after


label end_name:

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
    jump ch0_after


label end_scent:

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
    jump ch0_after


## ============================================================
## 章末
## ============================================================

label ch0_after:

    $ renpy.save_persistent()

    scene black
    with Dissolve(1.6)

    centered "{size=20}{color=#8b7b69}序章 · 完{/color}{/size}\n\n{color=#f0dcc2}第一章 · 门铃{/color}\n\n{size=18}{color=#8b7b69}她站在厨房里，背对着你。\n砧板上有什么东西，正在被切成很均匀的片。{/color}{/size}"

    centered "{size=18}{color=#8b7b69}本次周目 · 她记住你的方式{/color}{/size}\n\n{color=#d9a05f}[chapter_name]{/color}"

    return
