#!/usr/bin/env python3
"""死灵法师皮肤 v3 —— 整合优化版。

四项优化（整合进单一脚本，主题一致）：
1. 配色对比度：暗紫袍从近黑 (22,20,28) 提亮为可读的深紫 (70,50,92)，骨白/亡魂绿点缀更亮
2. 手绘风着色：全部改用 artistic（顶高光→底重阴影 + 领口高光 + 布褶）
3. 死灵主题细节：胸口骷髅徽记（绿眼）、背部符文、破旧袍边、骨甲细节
4. 兜帽与白发融合：深紫兜帽包裹头顶/后脑/两侧，灰白长发从帽下自然垂落

输出：necromancer.png / necromancer_3d.png / necromancer_large.png。
"""

from PIL import Image

from skinlib import Skin, apply_shading, render_3d

# ============================================================
# 配色（提亮 + 更饱和的暗紫）
# ============================================================
PALE_SKIN = (192, 186, 178, 255)  # 死灰肤色
HAIR = (208, 206, 200, 255)  # 灰白长发
HAIR_LIGHT = (238, 236, 230, 255)
HAIR_DARK = (162, 158, 150, 255)
ROBE = (70, 50, 92, 255)  # 深紫袍（可读）
ROBE_LIMB = (58, 42, 78, 255)  # 四肢稍暗
ROBE_LIGHT = (100, 76, 128, 255)
ROBE_DARK = (48, 34, 66, 255)  # 阴影紫（仍是紫，非黑）
HOOD = (66, 44, 88, 255)  # 兜帽
HOOD_LIGHT = (92, 66, 118, 255)
HOOD_DARK = (44, 28, 62, 255)
BONE = (218, 212, 198, 255)  # 骨白
BONE_LIGHT = (240, 236, 226, 255)  # 骨高光
BONE_DARK = (170, 162, 148, 255)  # 骨阴影
BONE_SHAD = (138, 130, 118, 255)  # 骨深影
SOUL = (96, 226, 140, 255)  # 亡魂绿
SOUL_HOT = (206, 255, 222, 255)  # 亮绿高光
SOUL_DIM = (42, 140, 90, 255)  # 暗绿
GOLD = (196, 162, 68, 255)  # 暗金
GOLD_LIGHT = (228, 196, 108, 255)
GOLD_DARK = (132, 106, 44, 255)
BROW = (128, 118, 112, 255)
NOSE = (162, 152, 142, 255)
MOUTH = (122, 104, 100, 255)
RUNE = (64, 94, 78, 255)  # 低饱和暗绿符文
RUNE_DIM = (48, 74, 62, 255)

s = Skin(size=64, model="steve")

# ============================================================
# BASE 层：手绘风着色（artistic）
# ============================================================
apply_shading(s, "head", PALE_SKIN, "base", style="artistic")
apply_shading(
    s, "body", ROBE, "base", style="artistic", bottom_dark=0.45, noise=True, noise_var=4
)
apply_shading(
    s, "right_arm", ROBE_LIMB, "base", style="artistic", bottom_dark=0.45, folds=False
)
apply_shading(
    s, "left_arm", ROBE_LIMB, "base", style="artistic", bottom_dark=0.45, folds=False
)
apply_shading(
    s, "right_leg", ROBE_LIMB, "base", style="artistic", bottom_dark=0.45, folds=False
)
apply_shading(
    s, "left_leg", ROBE_LIMB, "base", style="artistic", bottom_dark=0.45, folds=False
)

# ============================================================
# 白发（BASE）：后脑长发 + 两侧上半 + 刘海，露出面部
# ============================================================
s.paint_face("head", "base", "top", HAIR)
s.paint_face("head", "base", "back", HAIR)
for face in ("left", "right"):
    for u in range(8):
        for v in range(4):
            s.pixel("head", "base", face, u, v, HAIR)
# 前额刘海（v0 整行 + v1 两侧发丝）
for u in range(8):
    s.pixel("head", "base", "front", u, 0, HAIR)
for u in (0, 1, 6, 7):
    s.pixel("head", "base", "front", u, 1, HAIR)

# 发丝纹理（BASE）
for u in (1, 4, 6):
    for v in range(8):
        s.pixel("head", "base", "back", u, v, HAIR_LIGHT)
for face in ("left", "right"):
    for v in range(4):
        s.pixel("head", "base", face, 3, v, HAIR_LIGHT)
        s.pixel("head", "base", face, 6, v, HAIR_DARK)
for u in (3, 4):
    s.pixel("head", "base", "top", u, 0, HAIR_LIGHT)

# ============================================================
# 面部细节（BASE 前脸）
# ============================================================
for u in (1, 6):
    s.pixel("head", "base", "front", u, 3, BROW)
# 亡魂绿发光眼（2px + 高光）
for u in (1, 2, 5, 6):
    s.pixel("head", "base", "front", u, 4, SOUL)
s.pixel("head", "base", "front", 2, 4, SOUL_HOT)
s.pixel("head", "base", "front", 5, 4, SOUL_HOT)
# 眼下阴影（亡灵凹陷）
for u in (1, 2, 5, 6):
    s.pixel("head", "base", "front", u, 5, (150, 140, 132, 255))
# 鼻梁 + 鼻侧阴影
for u in (3, 4):
    s.pixel("head", "base", "front", u, 5, NOSE)
# 嘴（苍白唇线）
for u in (3, 4):
    s.pixel("head", "base", "front", u, 6, MOUTH)
# 下巴阴影
for u in (3, 4):
    s.pixel("head", "base", "front", u, 7, NOSE)

# ============================================================
# 兜帽（OVERLAY）：深紫兜帽包裹 + 白发从帽下垂落
# ============================================================
# 顶部：全兜帽 + 中缝褶皱高光
s.paint_face("head", "overlay", "top", HOOD)
for v in range(4):
    s.pixel("head", "overlay", "top", 3, v, HOOD_LIGHT)
    s.pixel("head", "overlay", "top", 4, v, HOOD_LIGHT)
# 后脑：v0-4 兜帽，v5-7 白发垂落
for u in range(8):
    for v in range(5):
        s.pixel("head", "overlay", "back", u, v, HOOD)
for u in range(8):
    s.pixel("head", "overlay", "back", u, 4, HOOD_DARK)
for u in range(8):
    for v in range(5, 8):
        s.pixel("head", "overlay", "back", u, v, HAIR)
for u in (1, 4, 6):
    for v in range(5, 8):
        s.pixel("head", "overlay", "back", u, v, HAIR_LIGHT)
# 两侧：v0-5 兜帽（包过下颌），v6-7 白发
for face in ("left", "right"):
    for u in range(8):
        for v in range(6):
            s.pixel("head", "overlay", face, u, v, HOOD)
    for u in range(8):
        s.pixel("head", "overlay", face, u, 5, HOOD_DARK)
    for u in range(8):
        for v in range(6, 8):
            s.pixel("head", "overlay", face, u, v, HAIR)
    for v in range(6, 8):
        s.pixel("head", "overlay", face, 3, v, HAIR_LIGHT)
        s.pixel("head", "overlay", face, 6, v, HAIR_DARK)
# 前脸：兜帽边沿（上缘 + 两侧框住脸）+ 刘海露脸
for u in range(8):
    s.pixel("head", "overlay", "front", u, 0, HOOD)
for u in (0, 7):
    for v in range(1, 6):
        s.pixel("head", "overlay", "front", u, v, HOOD)
# 帽沿内阴影
for u in range(8):
    s.pixel("head", "overlay", "front", u, 1, HOOD_DARK)
# 帽沿金饰（两侧）
for u in (0, 7):
    s.pixel("head", "overlay", "front", u, 2, GOLD_DARK)
# 刘海从帽下露出（中心 u2-5，v1-2）
for u in range(2, 6):
    s.pixel("head", "overlay", "front", u, 1, HAIR)
for u in (2, 5):
    s.pixel("head", "overlay", "front", u, 2, HAIR_LIGHT)
for u in (3, 4):
    s.pixel("head", "overlay", "front", u, 2, HAIR)
# 兜帽顶端褶皱高光（前脸顶部）
s.pixel("head", "overlay", "front", 3, 0, HOOD_LIGHT)
s.pixel("head", "overlay", "front", 4, 0, HOOD_LIGHT)

# ============================================================
# 躯干 OVERLAY：骷髅徽记 + 肋骨 + 脊柱 + 符文 + 腰带 + 破袍边
# ============================================================
FB = ("front", "back")  # 8 宽
SD = ("left", "right")  # 4 宽

# 肩部骨片（顶 + 侧面 + 前后顶部）
for face in SD:
    for u in range(4):
        s.pixel("body", "overlay", face, u, 0, BONE)
        s.pixel("body", "overlay", face, u, 1, BONE_DARK)
for face in FB:
    for u in (0, 7):
        s.pixel("body", "overlay", face, u, 0, BONE)
        s.pixel("body", "overlay", face, u, 1, BONE_DARK)

# 胸口骷髅徽记（前，中心 u2-5 / v1-4，绿眼）
for u in (3, 4):
    s.pixel("body", "overlay", "front", u, 1, BONE)  # 颅顶
for u in (2, 3, 4, 5):
    s.pixel("body", "overlay", "front", u, 2, BONE)  # 额头
for u in (3, 4):
    s.pixel("body", "overlay", "front", u, 2, BONE_LIGHT)  # 额头高光
s.pixel("body", "overlay", "front", 2, 3, SOUL)  # 左绿眼
s.pixel("body", "overlay", "front", 5, 3, SOUL)  # 右绿眼
for u in (3, 4):
    s.pixel("body", "overlay", "front", u, 3, BONE)  # 鼻梁
for u in (3, 4):
    s.pixel("body", "overlay", "front", u, 4, BONE_SHAD)  # 下颌
s.pixel("body", "overlay", "front", 3, 4, BONE_LIGHT)  # 齿

# 肋骨（环绕，v5/7/9）
for face in FB:
    for v in (5, 7, 9):
        s.pixel("body", "overlay", face, 1, v, BONE)
        s.pixel("body", "overlay", face, 6, v, BONE)
        s.pixel("body", "overlay", face, 2, v, BONE_DARK)
        s.pixel("body", "overlay", face, 5, v, BONE_DARK)
for face in SD:
    for v in (5, 7, 9):
        s.pixel("body", "overlay", face, 0, v, BONE)
        s.pixel("body", "overlay", face, 3, v, BONE_DARK)

# 后背脊柱（骨白中缝）+ 能量线
for v in range(2, 10):
    s.pixel("body", "overlay", "back", 3, v, BONE)
    s.pixel("body", "overlay", "back", 4, v, BONE_DARK)
for v in (3, 4, 5, 6):
    s.pixel("body", "overlay", "back", 3, v, SOUL_DIM)
    s.pixel("body", "overlay", "back", 4, v, SOUL_DIM)

# 背部符文（肩胛三角 + 下背，低饱和暗绿）
s.pixel("body", "overlay", "back", 0, 2, RUNE_DIM)
s.pixel("body", "overlay", "back", 1, 2, RUNE)
s.pixel("body", "overlay", "back", 0, 3, RUNE)
s.pixel("body", "overlay", "back", 7, 2, RUNE_DIM)
s.pixel("body", "overlay", "back", 6, 2, RUNE)
s.pixel("body", "overlay", "back", 7, 3, RUNE)
s.pixel("body", "overlay", "back", 2, 8, RUNE)
s.pixel("body", "overlay", "back", 5, 8, RUNE_DIM)

# 腰带（环绕腰部 v10-11）+ 金扣
for face in FB:
    for u in range(8):
        s.pixel("body", "overlay", face, u, 10, GOLD)
        s.pixel("body", "overlay", face, u, 11, GOLD_DARK)
for face in SD:
    for u in range(4):
        s.pixel("body", "overlay", face, u, 10, GOLD)
        s.pixel("body", "overlay", face, u, 11, GOLD_DARK)
for u in (3, 4):
    s.pixel("body", "overlay", "front", u, 10, GOLD_LIGHT)  # 金扣

# 破旧袍边（底部 v11 参差缺口）
for face in FB:
    for u in range(8):
        if u % 3 == 0:
            s.pixel("body", "overlay", face, u, 11, ROBE_DARK)

# ============================================================
# 臂 OVERLAY：骨护腕 + 肘骨片 + 符文 + 亡魂指尖
# ============================================================
AF = ("front", "back", "left", "right")
for arm in ("right_arm", "left_arm"):
    # 骨白护腕（环绕 v6-7）
    for face in AF:
        for u in range(4):
            s.pixel(arm, "overlay", face, u, 6, BONE)
            s.pixel(arm, "overlay", face, u, 7, BONE_DARK)
    # 护腕亡魂绿符文
    s.pixel(arm, "overlay", "front", 1, 6, SOUL)
    s.pixel(arm, "overlay", "front", 2, 6, SOUL_DIM)
    # 肘部骨片（环绕 v3）
    for face in AF:
        for u in range(4):
            s.pixel(arm, "overlay", face, u, 3, BONE_DARK)
    # 指尖亡魂绿（环绕 v10-11）
    for face in AF:
        s.pixel(arm, "overlay", face, 1, 10, SOUL)
        s.pixel(arm, "overlay", face, 2, 10, SOUL_HOT)
        s.pixel(arm, "overlay", face, 1, 11, SOUL_DIM)
        s.pixel(arm, "overlay", face, 2, 11, SOUL)

# ============================================================
# 腿 OVERLAY：骨护膝 + 符文 + 鞋尖骨片
# ============================================================
LF = ("front", "back", "left", "right")
for leg in ("right_leg", "left_leg"):
    # 骨白护膝（环绕 v4-5）
    for face in LF:
        for u in range(4):
            s.pixel(leg, "overlay", face, u, 4, BONE)
            s.pixel(leg, "overlay", face, u, 5, BONE_DARK)
    # 护膝亡魂绿符文
    s.pixel(leg, "overlay", "front", 1, 4, SOUL)
    s.pixel(leg, "overlay", "front", 2, 4, SOUL_DIM)
    # 鞋尖骨片（环绕 v10-11）
    for face in LF:
        for u in range(1, 3):
            s.pixel(leg, "overlay", face, u, 10, BONE)
            s.pixel(leg, "overlay", face, u, 11, BONE_DARK)

# ============================================================
# 输出
# ============================================================
s.save("necromancer.png")
render_3d(s, scale=6, pose="natural").save("necromancer_3d.png")
s.img.resize((512, 512), Image.Resampling.NEAREST).save("necromancer_large.png")

print("生成 necromancer.png / necromancer_3d.png / necromancer_large.png")
