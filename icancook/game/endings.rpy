##  结局图鉴 —— 三个章节，九个结局
##
##  为什么单独做一个 screen 而不是塞进主菜单：
##  这本书的"收集感"不来自通关次数，而来自**你用什么方式被她记住**。
##  所以每一格都写成一句描述，而不是"结局 3/9 未解锁"。

init python:

    ENDING_BOOK = [
        ("序章 · 重访第一夜", [
            ("endings_lie",   "A · 她记住了你的谎话",
             "你说了一个漂亮的谎。她笑着信了。然后你再也记不清自己原本想说什么。"),
            ("endings_name",  "B · 她记住了你的名字",
             "你给了她名字。她念它的时候，像是在试一件很合身的东西。"),
            ("endings_scent", "C · 她记住了你的味道",
             "你没说话。她闻了闻，就什么都知道了。"),
        ]),
        ("第一章 · 门铃", [
            ("ch1_stay",  "她记住了你留下来",
             "天亮了。你没有走。她说「那你把外套挂回去吧」。"),
            ("ch1_leave", "她记住了你看见了什么",
             "你知道了不该知道的事。她把这件事，连同你，一起收好了。"),
            ("ch1_key",   "她给了你钥匙",
             "钥匙是温的。她大概握了很久。"),
        ]),
        ("第二章 · 刀与糖", [
            ("ch2_shared", "她给你留了半盘",
             "她饿着，看你吃完。这一盘里有她没舍得给自己留的那一半。"),
            ("ch2_taste",  "她记住了你放的那一撮",
             "你放下的东西变成了这顿饭的味道。她没说好不好，只是吃完了。"),
            ("ch2_seen",   "她已经知道你会回来",
             "你碰了那瓶没有标签的东西。从那一刻起，你没有退路了。"),
        ]),
        ("第三章 · 十七个日期", [
            ("ch3_sofa",    "她给了你沙发",
             "她说「沙发」，然后笑了。你几乎忘了冰箱里有什么。"),
            ("ch3_counted", "她算准了你会回来",
             "她没有问你明天为什么还来。因为她知道你一定会来。"),
            ("ch3_same",    "她等的从来是同一个人",
             "她没有看你。她说从来都是同一个人。你没有问那个人是谁。"),
        ]),
    ]

    def ending_flags():
        """把 persistent 上的开关读成一个 dict，供 screen 判断。"""
        out = {}
        for _, items in ENDING_BOOK:
            for flag, _, _ in items:
                out[flag] = bool(getattr(persistent, flag, False))
        return out

default _ending_view = 0


screen ending_book():

    tag menu
    modal True
    zorder 200

    add Solid("#08060a")

    vbox:
        xalign 0.5
        ypos 50
        spacing 4
        text "记住你的方式" size 26 color "#d9a05f" xalign 0.5
        text "ENDINGS" size 12 color "#6b5c4d" xalign 0.5
        null height 18

    viewport:
        xalign 0.5
        ypos 130
        xsize 1100
        ysize 760
        mousewheel True
        draggable True

        vbox:
            spacing 26

            $ flags = ending_flags()
            $ total = sum(len(items) for _, items in ENDING_BOOK)
            $ got = sum(1 for v in flags.values() if v)

            text "已收集 [got] / [total]" size 14 color "#8b7b69"

            for title, items in ENDING_BOOK:
                vbox:
                    spacing 10

                    text title size 15 color "#8b7b69"

                    for flag, name, desc in items:
                        frame:
                            xfill True
                            padding (18, 14)
                            background Solid("#12100e" if flags[flag] else "#0c0a08")

                            vbox:
                                spacing 6
                                if flags[flag]:
                                    text "◆ [name]" size 20 color "#e8dcc8"
                                    text desc size 15 color "#a89a88"
                                else:
                                    text "◇ 未抵达" size 18 color "#3f3933"

    textbutton "返回":
        xalign 0.5
        yalign 0.965
        text_size 16
        text_color "#cfc3b2"
        text_hover_color "#f6e9d6"
        action Return()
