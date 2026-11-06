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


## 热区坐标说明（1920x1080）
##
## 旧版是一组手写的 0~1 比例：烛台 (0.38, 0.72)、笔记本 (0.59, 0.80)、
## 「她的手」(0.50, 0.48)、空气 (0.06, 0.24)。
## 这些数字是照**站姿**立绘猜的，而这一场用的是坐姿图：
##   · 「她的手」其实落在她胸口下方，标签漂在半空中；
##   · 烛台/笔记本直接压在桌沿上沿，点不到。
## 用户截图里的「部件与任务 UI 不匹配」就是这两条。
##
## 现在改成按**画面实际内容**标定（坐标经过真机截图核对）：
##   坐姿图 xalign 0.5 / zoom 1.19 下，她就坐在画面中间，
##   手在 y≈0.50 附近、膝在 y≈0.66，前景桌面从 y≈0.78 开始。
## 所以：她的手 → (0.545, 0.505)；烛台/笔记本落在桌面可见区 (≈0.82 以下)。
screen smell_table():

    zorder 60
    modal True

    ## 关不掉就是卡关 —— 这条是被用户当场卡住之后补的。
    ## 右键 / ESC 都返回，和 Ren'Py 常规菜单一致；底部还有显式按钮。
    key "game_menu" action Return()
    key "K_ESCAPE" action Return()

    ## 暗掉画面，只留一点轮廓
    add Solid("#0504029c")

    ## 顶部提示
    vbox:
        xalign 0.5
        ypos 60
        spacing 6
        text "嗅" size 15 color "#d9a05f" xalign 0.5
        text "把光标移到桌上的东西上，按住左键不放，直到气味浮上来。" size 17 color "#b9ac9a" xalign 0.5

    ## 四个可闻的地方。padding 给足，热区才够大、好点。
    button:
        xpos 0.40
        ypos 0.83
        padding (40, 30)
        background None
        hover_background Solid("#d9a05f22")
        action Function(smell_do, "candle")
        text "烛台" size 16 color "#e8dcc8"

    button:
        xpos 0.62
        ypos 0.86
        padding (40, 30)
        background None
        hover_background Solid("#d9a05f22")
        action Function(smell_do, "notebook")
        text "笔记本" size 16 color "#e8dcc8"

    ## 「她的手」—— 坐姿图里她的手在身前、大约 y=0.50
    button:
        xpos 0.475
        ypos 0.47
        padding (52, 40)
        background None
        hover_background Solid("#d9a05f18")
        action Function(smell_do, "hand")
        text "她的手" size 16 color "#e8dcc8"

    ## 空气：左边那块空处，和人物不重叠
    button:
        xpos 0.06
        ypos 0.30
        padding (30, 24)
        background None
        hover_background Solid("#d9a05f18")
        action Function(smell_do, "air")
        text "空气" size 16 color "#e8dcc8"

    ## 气味浮层：压在画面左上，不挡她的脸
    if smell_line:
        frame:
            xpos 90
            ypos 150
            xsize 720
            padding (26, 20)
            background Solid("#0b0805e0")

            vbox:
                spacing 8
                text smell_note size 15 color "#d9a05f"
                text smell_line size 21 color "#e8e0d4"

    ## 计数器 + 离开。
    ## 旧版把这一条 hbox 放在 yalign 0.94，被前景桌面层的暗部吃掉，
    ## 用户看到的就是"没有关闭按钮" → 卡关。现在锁在屏幕底部安全区，
    ## 并且给「起身」一个看得见的边框。
    frame:
        xalign 0.5
        yalign 0.955
        padding (34, 16)
        background Solid("#0b0805d8")

        hbox:
            spacing 44

            text "闻到 [smells_found] / 4" size 16 color "#b9ac9a" yalign 0.5

            textbutton "起身":
                text_size 17
                text_color "#cfc3b2"
                text_hover_color "#f6e9d6"
                background Solid("#d9a05f22")
                hover_background Solid("#d9a05f55")
                padding (22, 8)
                action Return()
