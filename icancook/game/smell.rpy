##  嗅觉交互 — 「闻一闻这张桌子」

init python:

    SMELL_DATA = {
        "candle":   ("蜡油。烧过很多次了，每次都是同一支。她大概从来不换。",
                     "蜡油、旧火、还有一点铁。"),
        "notebook": ("皮面的本子，压着一股很淡的甜味。翻过很多次，边角是软的。",
                     "皮革、纸、干了很久的甜。"),
        "hand":     ("她的手腕上没有香水。只有体温，和一点洗涤剂的味道。",
                     "体温、皂、干净的皮肤。"),
        "air":      ("空气里有别的东西。不是这桌的。是走廊深处飘过来的。",
                     "铁锈。很新鲜的那种铁锈。"),
    }

    def smell_do(key):
        seen = renpy.store.smell_seen
        if key not in seen:
            seen.add(key)
            renpy.store.smell_seen = set(seen)
            renpy.store.smells_found = len(seen)
        renpy.store.smell_line = SMELL_DATA[key][0]
        renpy.store.smell_note = SMELL_DATA[key][1]

default smells_found = 0
default smell_seen = set()
default smell_line = ""
default smell_note = ""

transform smell_pulse:
    alpha 0.35
    linear 1.1 alpha 0.85
    linear 1.1 alpha 0.35
    repeat


screen smell_table():

    zorder 60
    modal True

    ## 暗掉画面，只留一点轮廓
    add Solid("#0504029c")

    ## 顶部提示
    vbox:
        xalign 0.5
        ypos 60
        spacing 6
        text "嗅" size 15 color "#d9a05f" xalign 0.5
        text "把光标移到桌上的东西上，按住左键不放，直到气味浮上来。" size 17 color "#b9ac9a" xalign 0.5

    ## 三个可闻的地方
    button:
        xpos 0.38
        ypos 0.72
        padding (28, 28)
        background None
        hover_background Solid("#d9a05f22")
        action Function(smell_do, "candle")
        text "烛台" size 16 color "#e8dcc8"

    button:
        xpos 0.59
        ypos 0.80
        padding (28, 28)
        background None
        hover_background Solid("#d9a05f22")
        action Function(smell_do, "notebook")
        text "笔记本" size 16 color "#e8dcc8"

    button:
        xpos 0.50
        ypos 0.48
        padding (44, 34)
        background None
        hover_background Solid("#d9a05f18")
        action Function(smell_do, "hand")
        text "她的手" size 16 color "#e8dcc8"

    button:
        xpos 0.06
        ypos 0.24
        padding (24, 18)
        background None
        hover_background Solid("#d9a05f18")
        action Function(smell_do, "air")
        text "空气" size 16 color "#e8dcc8"

    ## 气味浮层
    if smell_line:
        frame:
            xpos 120
            yalign 0.62
            xsize 780
            padding (28, 22)
            background Solid("#0b0805e8")

            vbox:
                spacing 8
                text smell_note size 15 color "#d9a05f"
                text smell_line size 21 color "#e8e0d4"

    ## 计数器 + 离开
    hbox:
        xalign 0.5
        yalign 0.94
        spacing 40

        text "闻到 [smells_found] / 4" size 16 color "#8b7b69" yalign 0.5

        textbutton "起身":
            text_size 16
            text_color "#cfc3b2"
            text_hover_color "#f6e9d6"
            action Return()
