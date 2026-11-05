##  演出层 —— 「过场」与「镜头」
##
##  这一部戏的表演不在台词里，在【距离】、【光】、【停顿】三件事上。
##  所以这里给的不是特效，是镜头语言：
##
##    letterbox     遮幅。进章节 / 回忆 / 独白时用，一下子就有电影感
##    push_in       缓慢推近（她靠近）
##    pull_out      缓慢退开（你退了一步）
##    rack          焦点漂移：立绘虚一点，环境更实
##    shake         极小幅震动（心跳、惊吓）—— 厚涂图不能晃太狠，会糊
##    flash         一次闪白 / 闪黑，用来切章
##    breath_dark   画面整体压暗再回，模拟烛火被风带动
##
##  原则：所有幅度都小。厚涂一旦剧烈运动，笔触就会被读成"抖动的照片"。

## ——— 遮幅 ———————————————————————————————————————————————
## 两条黑边，各自从画面外滑进来。比"直接盖一个半透明矩形"有呼吸感。
image bar_top = Solid("#000000", xysize=(1920, 120))
image bar_bottom = Solid("#000000", xysize=(1920, 120))
image screen_white = Solid("#ffffff")
image screen_black = Solid("#000000")

transform bar_in_top(t=0.8):
    xalign 0.5 ypos -120          # 完全藏在画面上方
    linear t ypos 0

transform bar_in_bottom(t=0.8):
    xalign 0.5 ypos 1080
    linear t ypos 960

transform bar_out_top(t=0.6):
    linear t ypos -120

transform bar_out_bottom(t=0.6):
    linear t ypos 1080

## ——— 镜头 ———————————————————————————————————————————————
transform push_in(speed=8.0, to=1.14):
    zoom 1.0
    linear speed zoom to

transform pull_out(speed=6.0, to=1.0):
    zoom 1.10
    linear speed zoom to

## 焦点漂移：轻微模糊 + 轻微放大，模拟"视线失焦"
transform rack(d=3.0):
    blur 0.0
    zoom 1.0
    linear d blur 2.2 zoom 1.02
    linear d blur 0.0 zoom 1.0
    repeat

## 极小幅震动（±4px，9Hz 衰减）
transform shake(mag=4, times=7):
    block:
        linear 0.03 xoffset mag yoffset -mag
        linear 0.03 xoffset -mag yoffset mag
        repeat times
    linear 0.06 xoffset 0 yoffset 0

## 长一点的余震（心跳用）
transform throb(mag=2, period=0.85):
    block:
        linear period / 2 xoffset 0 yoffset mag
        linear period / 2 xoffset 0 yoffset 0
        repeat

## 一次闪光
transform flash_cut(color="#ffffff", peak=0.55, d=0.45):
    alpha 0.0
    linear d * 0.25 alpha peak
    linear d * 0.75 alpha 0.0
