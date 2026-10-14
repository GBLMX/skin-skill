"""Tests for generic textures: the canvas, the block/icon generators, and the
minebase bridge.

Pinned here are the vanilla *conventions* (16x16, cube face lighting, greyscale
tint-ready, silhouette icons) and the canvas contract the painting primitives
rely on: a pass runs once per face the canvas declares.
"""

import pytest

from skinlib import FACES, Skin, Texture, block, icon, texture_size
from skinlib import from_spec
from skinlib.model import canvas_faces
from skinlib.overlay import scratches
from skinlib.texture import BLOCK_FACES, ICON_ART, TEXTURE_SIZES

BASE = (42, 77, 74, 255)


# -- canvas contract --------------------------------------------------------
def test_skin_declares_every_face_texture_only_its_own():
    assert canvas_faces(Skin()) == FACES
    assert canvas_faces(Texture(16, 16)) == ("front",)
    assert canvas_faces(block(BASE)) == BLOCK_FACES


def test_faces_are_laid_out_side_by_side():
    t = Texture(16, 16, faces=("top", "side", "bottom"))
    assert t.img.size == (48, 16)
    assert t.region("all", "base", "top") == (0, 0, 16, 16)
    assert t.region("all", "base", "side") == (16, 0, 16, 16)
    assert t.region("all", "base", "bottom") == (32, 0, 16, 16)
    t.pixel("all", "base", "bottom", 0, 0, (1, 2, 3, 255))
    assert t.img.getpixel((32, 0)) == (1, 2, 3, 255)


def test_single_face_answers_any_face_name_multi_face_raises():
    one = Texture(16, 16)
    one.pixel("all", "base", "back", 0, 0, (9, 9, 9, 255))  # only one face
    assert one.img.getpixel((0, 0)) == (9, 9, 9, 255)

    three = Texture(16, 16, faces=("top", "side", "bottom"))
    with pytest.raises(KeyError):
        three.pixel("all", "base", "front", 0, 0, (0, 0, 0, 255))


def test_pixel_out_of_bounds_raises():
    with pytest.raises(ValueError):
        Texture(16, 16).pixel("all", "base", "front", 16, 0, (0, 0, 0, 255))


def test_per_face_overlay_runs_once_per_declared_face():
    """A pass must paint each face the canvas declares, once.

    Painting a one-face canvas six times (once per skin face) would stack the
    overlay on the same pixels, so the first face of a three-face sheet and the
    only face of a one-face sheet have to come out identical.
    """
    one = Texture(16, 16, fill=BASE)
    three = Texture(16, 16, faces=("top", "side", "bottom"), fill=BASE)
    for tex in (one, three):
        scratches(tex, "all", (0, 0, 0, 255), count=8, seed=7)
    assert one.img.tobytes() == three.face_image("all", "base", "top").tobytes()


# -- block generator --------------------------------------------------------
def test_block_face_lighting_is_vanilla_order():
    t = block(BASE, style="minimal")
    top = t.get_pixel("all", "base", "top", 8, 8)
    side = t.get_pixel("all", "base", "side", 8, 8)
    bottom = t.get_pixel("all", "base", "bottom", 8, 8)
    assert top[0] > side[0] > bottom[0]
    assert top[1] > side[1] > bottom[1]


def test_block_glow_keeps_face_ordering():
    t = block(BASE, style="minimal", glow=True)
    top = t.get_pixel("all", "base", "top", 8, 8)[1]
    side = t.get_pixel("all", "base", "side", 8, 8)[1]
    bottom = t.get_pixel("all", "base", "bottom", 8, 8)[1]
    assert top > side > bottom          # the cube convention survives the lift
    assert side > block(BASE, style="minimal").get_pixel(
        "all", "base", "side", 8, 8)[1]  # ... and the sheet got lighter


def test_block_tint_ready_is_greyscale():
    t = block((120, 200, 90, 255), style="combined", noise=4, tint_ready=True)
    for face in t.faces:
        for u in range(16):
            r, g, b, a = t.get_pixel("all", "base", face, u, 6)
            assert r == g == b
            assert a == 255


def test_block_alpha_touches_painted_pixels_only():
    t = block(BASE, alpha=180)
    assert t.get_pixel("all", "base", "side", 3, 3)[3] == 180


def test_block_accepts_a_style_profile_and_a_material():
    profiled = block(BASE, style="mottled", noise=0)
    material = block((138, 138, 150, 255), material="metal")
    assert profiled.img.size == material.img.size == (48, 16)
    # metal draws a bright specular streak down the middle of each face
    assert material.get_pixel("all", "base", "side", 8, 8)[1] > \
        material.get_pixel("all", "base", "side", 1, 8)[1]


def test_block_rejects_unknown_style():
    with pytest.raises(ValueError):
        block(BASE, style="nope")


# -- icon generator ---------------------------------------------------------
def test_icon_archetypes_are_16x16_art():
    for name, art in ICON_ART.items():
        assert len(art) == 16, name
        assert all(len(row) == 16 for row in art), name
        assert set("".join(art)) <= {".", "#"}, name


def test_icon_keeps_a_transparent_margin_and_masks_the_rest():
    t = icon(BASE, shape="gem")
    edge = [(u, v) for u in range(16) for v in (0, 15)] + \
           [(u, v) for u in (0, 15) for v in range(16)]
    assert all(t.get_pixel("all", "base", "front", u, v)[3] == 0
               for u, v in edge)
    assert t.get_pixel("all", "base", "front", 8, 6)[3] == 255


def test_icon_honours_a_custom_mask():
    t = icon(BASE, mask=lambda u, v: u == 8 and v == 8)
    assert t.get_pixel("all", "base", "front", 8, 8)[3] == 255
    assert t.get_pixel("all", "base", "front", 7, 8)[3] == 0


def test_icon_rejects_unknown_shape():
    with pytest.raises(ValueError):
        icon(BASE, shape="nope")


# -- size table and IO ------------------------------------------------------
def test_texture_size_table_matches_vanilla_conventions():
    assert texture_size("block") == texture_size("item") == (16, 16)
    assert texture_size("cape") == texture_size("armor_layer") == (64, 32)
    with pytest.raises(ValueError):
        texture_size("nope")
    assert set(TEXTURE_SIZES) >= {"block", "item", "cape"}


def test_save_faces_writes_one_png_per_face(tmp_path):
    t = block(BASE)
    written = t.save_faces(tmp_path, "sculk", scale=2)
    assert [p.name for p in written] == [
        "sculk_top.png", "sculk_side.png", "sculk_bottom.png"]
    assert all(p.exists() for p in written)
    reloaded = Texture.load(written[0])
    assert (reloaded.width, reloaded.height) == (32, 32)


def test_load_splits_a_sheet_into_faces(tmp_path):
    t = block(BASE)
    path = t.save(tmp_path / "sheet.png")
    reloaded = Texture.load(path, faces=("top", "side", "bottom"))
    assert reloaded.faces == ("top", "side", "bottom")
    assert reloaded.img.tobytes() == t.img.tobytes()
    with pytest.raises(ValueError):
        Texture.load(path, faces=("a", "b"))


# -- registry bridge --------------------------------------------------------
class _Spec:
    """Stand-in for gamedata.TextureSpec (the bridge is duck-typed)."""

    def __init__(self, **kw):
        self.name = "x"
        self.display_name = "X"
        self.kind = "block"
        self.size = 16
        self.emissive = False
        self.transparent = False
        self.tint_group = None
        self.material = None
        self.style = None
        self.family = ()
        self.states = ()
        self.__dict__.update(kw)


def test_from_spec_draws_biome_tinted_blocks_greyscale():
    t = from_spec(_Spec(tint_group="grass"), (120, 200, 90, 255), style="flat")
    r, g, b, _ = t.get_pixel("all", "base", "top", 8, 8)
    assert r == g == b


def test_from_spec_glow_follows_emit_light_and_can_be_overridden():
    emissive = from_spec(_Spec(emissive=True), BASE, style="minimal")
    plain = from_spec(_Spec(emissive=False), BASE, style="minimal")
    assert emissive.get_pixel("all", "base", "side", 8, 8)[1] > \
        plain.get_pixel("all", "base", "side", 8, 8)[1]
    forced = from_spec(_Spec(emissive=True), BASE, style="minimal", glow=False)
    assert forced.img.tobytes() == plain.img.tobytes()


def test_from_spec_items_get_one_face_blocks_get_three():
    assert from_spec(_Spec(kind="item"), BASE).faces == ("front",)
    assert from_spec(_Spec(kind="block"), BASE).faces == BLOCK_FACES


def test_apply_fade_defaults_to_the_canvas_faces():
    """A texture fades every face it declares; a skin keeps its four sides."""
    from skinlib import apply_fade

    tex = block((100, 100, 100, 255), style="minimal")
    apply_fade(tex, "all", 2, 6, [(1, 2, 3, 255)])
    for face in tex.faces:
        assert tex.get_pixel("all", "base", face, 3, 2) == (1, 2, 3, 255)
        assert tex.get_pixel("all", "base", face, 3, 7)[0] != 1  # outside band

    skin = Skin()
    skin.paint_part("body", (100, 100, 100, 255))
    apply_fade(skin, "body", 2, 6, [(1, 2, 3, 255)])
    assert skin.get_pixel("body", "base", "front", 3, 2) == (1, 2, 3, 255)
    assert skin.get_pixel("body", "base", "top", 3, 2) != (1, 2, 3, 255)


def test_icon_scales_the_archetype_and_keeps_the_margin():
    t = icon(BASE, shape="gem", size=32, style="minimal")
    assert t.img.size == (32, 32)
    assert t.get_pixel("all", "base", "front", 0, 0)[3] == 0      # margin
    assert t.get_pixel("all", "base", "front", 31, 31)[3] == 0    # margin
    assert t.get_pixel("all", "base", "front", 16, 12)[3] == 255  # silhouette


def test_generate_uses_the_registry():
    pytest.importorskip("minebase")
    from skinlib import generate

    tex = generate("sculk", (29, 59, 58, 255))
    assert tex.faces == BLOCK_FACES
    assert generate("echo_shard", (41, 223, 235, 255)).faces == ("front",)
