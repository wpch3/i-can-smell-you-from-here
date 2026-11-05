##  Chapter 2 交互 — 「调味不是靠菜谱，是靠闻」
##
##  30 秒倒计时。玩家先「闻」三样东西，再决定放哪一样。
##  闻过再放，她的话会变；不闻就放，她会看不起你（但不会扣分，这游戏不惩罚人）。
##
##  设计意图：这一章的表演核心是「她看着你做一件不可逆的事」。
##  倒计时不是为了紧张，是为了让玩家在最后几秒真的犹豫。

init python:

    SEASON_DATA = {
        "salt":  ("盐。粗粒的，放在一只小陶碟里。没有任何味道，但你会想把它放在舌头上试一下。",
                  "咸是诚实。"),
        "sugar": ("黄糖。结成块，边缘有点黏。有一点焦味，像是熬过头了又被人救回来。",
                  "甜是讨好。"),
        "jar":   ("一只没有标签的深色小瓶。拔开瓶塞的瞬间，整个厨房的气味都变了。",
                  "这一瓶，你不该闻到。"),
    }

    def season_sniff(key):
        seen = renpy.store.season_seen
        if key not in seen:
            renpy.store.season_seen = set(seen) | {key}
        renpy.store.season_note, renpy.store.season_hint = SEASON_DATA[key]

default season_seen = set()
default season_note = ""
default season_hint = ""
default season_timer = 30.0
default season_done = False


## 倒计时：只在 screen 显示期间走
screen season_ticker():
    timer 0.1 repeat True action Function(season_tick)


init python:

    def season_tick():
        if not renpy.store.season_done:
            renpy.store.season_timer = max(0.0, renpy.store.season_timer - 0.1)


transform season_glow:
    alpha 0.55
    linear 1.6 alpha 1.0
    linear 1.6 alpha 0.55
    repeat


screen seasoning_pick():

    zorder 60
    modal True

    add Solid("#050402a8")
    use season_ticker

    ## 倒计时条：剩得越少越红
    frame:
        xalign 0.5
        ypos 44
        xsize 760
        padding (0, 0)
        background Solid("#1a1511")

        bar:
            value season_timer
            range 30.0
            xsize 760
            ysize 6
            left_bar Solid("#d9a05f" if season_timer > 8 else "#a8443a")
            right_bar Solid("#2a231c")

    vbox:
        xalign 0.5
        ypos 66
        spacing 6
        text "调 味" size 15 color "#d9a05f" xalign 0.5
        text "先闻。闻完再决定放什么。放错了也没关系——我会吃完。" size 17 color "#b9ac9a" xalign 0.5

    ## 三样东西
    hbox:
        xalign 0.5
        ypos 0.40
        spacing 90

        button:
            padding (34, 30)
            background None
            hover_background Solid("#d9a05f1a")
            action Function(season_sniff, "salt")
            vbox:
                spacing 8
                text "盐" size 26 color "#e8dcc8" xalign 0.5
                text "闻一闻" size 14 color "#8b7b69" xalign 0.5

        button:
            padding (34, 30)
            background None
            hover_background Solid("#d9a05f1a")
            action Function(season_sniff, "sugar")
            vbox:
                spacing 8
                text "黄糖" size 26 color "#e8dcc8" xalign 0.5
                text "闻一闻" size 14 color "#8b7b69" xalign 0.5

        button:
            padding (34, 30)
            background None
            hover_background Solid("#a8443a22")
            action Function(season_sniff, "jar")
            vbox:
                spacing 8
                text "没有标签的瓶子" size 20 color "#d8c7ae" xalign 0.5
                text "闻一闻" size 14 color "#8b7b69" xalign 0.5

    ## 闻到的内容
    if season_note:
        frame:
            xalign 0.5
            ypos 0.56
            xsize 880
            padding (30, 24)
            background Solid("#0b0805e8")

            vbox:
                spacing 10
                text season_hint size 15 color "#d9a05f"
                text season_note size 21 color "#e8e0d4"

    ## 最后：放下去（不可逆）
    hbox:
        xalign 0.5
        yalign 0.94
        spacing 54
        if season_seen:
            textbutton "放盐":
                text_size 17
                text_color "#cfc3b2"
                text_hover_color "#f6e9d6"
                action [SetVariable("season_done", True), Return("salt")]
            textbutton "放糖":
                text_size 17
                text_color "#cfc3b2"
                text_hover_color "#f6e9d6"
                action [SetVariable("season_done", True), Return("sugar")]
            textbutton "放那一瓶":
                text_size 17
                text_color "#c98f86"
                text_hover_color "#f0b0a4"
                action [SetVariable("season_done", True), Return("jar")]
        else:
            text "先闻一样东西。" size 16 color "#6b5c4d"

    ## 时间到：默认放盐（她不会为难你，但会记住你没犹豫）
    if season_timer <= 0 and not season_done:
        timer 0.1 action [SetVariable("season_done", True), Return("salt")]
