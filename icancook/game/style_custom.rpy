##  《我在这儿就能为你下厨了》 — 视觉皮肤
##  覆盖 the_question 模板的 GUI，改成原作那种「底部一条纯深色横条 + 极简文字选项」的样子。

style window:
    xalign 0.5
    xfill True
    yalign gui.textbox_yalign
    ysize gui.textbox_height
    background Solid("#0d0a07dc")

style namebox:
    xpos gui.name_xpos
    xanchor gui.name_xalign
    xsize gui.namebox_width
    ypos gui.name_ypos
    ysize gui.namebox_height
    background None
    padding (0, 0, 0, 0)

style say_label:
    xpos 0
    ypos 0
    color "#d9a05f"
    size 21

style say_dialogue:
    xpos gui.dialogue_xpos
    xsize gui.dialogue_width
    ypos gui.dialogue_ypos
    color gui.text_color
    size gui.text_size
    line_spacing 6
    outlines [ (1, "#00000090", 0, 0) ]
    adjust_spacing False

style choice_vbox:
    xalign 0.5
    ypos 540
    yanchor 0.0
    spacing gui.choice_spacing

style choice_button:
    xsize gui.choice_button_width
    padding (28, 12, 28, 12)
    background None
    hover_background Solid("#d9a05f1c")

style choice_button_text:
    color gui.choice_button_text_idle_color
    hover_color gui.choice_button_text_hover_color
    size 27
    xalign 0.0

style quick_button:
    padding (10, 4, 10, 0)
    background None

style quick_button_text:
    size 14
    idle_color "#6b5c4d"
    hover_color "#d9a05f"

## 覆盖主菜单里的小字，语气更贴作品
define config.main_menu_music = None
