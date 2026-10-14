"""Tests for the vanilla game-data layer.

These need the optional ``gamedata`` extra (``pip install mc-skin[gamedata]``)
and are skipped without it. Assertions pin facts that come from the game --
vanilla tint colors, the shape of a style family, the Bedrock skin schema -- so
a bad data mapping fails here instead of silently painting the wrong colors.
"""

import pytest

from skinlib import gamedata as G

pytest.importorskip("minebase")

V = G.latest()


# ---------------------------------------------------------------------------
# family_of -- the style-family heuristic
# ---------------------------------------------------------------------------
def test_family_of_strips_color_and_shape_tokens():
    assert G.family_of("red_sandstone") == "sandstone"
    assert G.family_of("white_wool") == "wool"
    assert G.family_of("dark_oak_planks") == "oak"
    assert G.family_of("polished_blackstone_bricks") == "blackstone"
    assert G.family_of("waxed_oxidized_copper_grate") == "copper"
    assert G.family_of("calibrated_sculk_sensor") == "sculk"


def test_family_of_keeps_unknown_prefixes_apart():
    # A material that is not a recognised modifier keeps its own family rather
    # than being merged into a neighbour.
    assert G.family_of("nether_bricks") == "nether"
    assert G.family_of("end_stone_bricks") == "end"
    assert G.family_of("stone") == "stone"


def test_family_of_collapses_spawn_eggs():
    assert G.family_of("allay_spawn_egg") == "spawn_egg"
    assert G.family_of("zombie_spawn_egg") == "spawn_egg"


def test_family_of_absorbs_treatment_adjectives():
    # Adjectives on the modifier list must merge into the material family they
    # qualify, otherwise generation targeting e.g. "amethyst" silently misses
    # budding_amethyst.
    assert G.family_of("carved_pumpkin") == "pumpkin"
    assert G.family_of("tinted_glass") == "glass"
    assert G.family_of("gilded_blackstone") == "blackstone"
    assert G.family_of("budding_amethyst") == "amethyst"
    assert G.family_of("medium_amethyst_bud") == "amethyst"
    assert G.family_of("reinforced_deepslate") == "deepslate"
    assert G.family_of("frosted_ice") == "ice"
    assert G.family_of("popped_chorus_fruit") == "chorus"


def test_family_of_leaves_subjects_alone():
    # Subjects and head nouns name the thing; stripping them would merge
    # unrelated content into one family.
    assert G.family_of("zombie_head") == "zombie"
    assert G.family_of("breeze_rod") == "breeze"
    assert G.family_of("ink_sac") == "ink"


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------
def test_versions_and_latest():
    vs = G.versions()
    assert vs and V in vs
    for edition in G.EDITIONS:
        assert G.latest(edition) in G.versions(edition)


def test_resolve_defaults_to_latest():
    assert G.resolve() == V
    assert G.resolve("latest") == V
    assert G.resolve(V) == V


def test_unknown_version_and_edition_raise():
    with pytest.raises(ValueError, match="unknown version"):
        G.resolve("99.99")
    with pytest.raises(ValueError, match="unknown edition"):
        G.versions("nintendo64")


def test_info_reports_protocol():
    info = G.info(V)
    assert info.version == V
    assert info.edition == G.PC
    assert info.protocol and info.protocol > 0
    assert info.release_type == "release"


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
def test_registries_are_populated_and_typed():
    assert any(b.name == "stone" for b in G.blocks(V))
    assert all(isinstance(b, G.Block) for b in G.blocks(V))
    assert all(isinstance(i, G.Item) for i in G.items(V))
    assert all(isinstance(e, G.Entity) for e in G.entities(V))
    assert all(isinstance(p, G.Particle) for p in G.particles(V))
    assert all(isinstance(b, G.Biome) for b in G.biomes(V))


def test_block_glow_and_family():
    block = G.find_block("sculk_sensor", V)
    assert block is not None
    assert block.glows and block.emit_light > 0
    assert block.family == "sculk"
    assert isinstance(block.material, str) and block.material

    stone = G.find_block("stone", V)
    assert stone is not None and not stone.glows


def test_find_unknown_returns_none():
    assert G.find_block("definitely_not_a_block", V) is None
    assert G.find_item("definitely_not_an_item", V) is None
    assert G.find_entity("definitely_not_an_entity", V) is None


def test_entity_carries_dimensions_and_category():
    warden = G.find_entity("warden", V)
    assert warden is not None
    assert warden.height > 0 and warden.width > 0
    assert warden.category


def test_language_table():
    assert G.translate("block.minecraft.sculk", V) == "Sculk"


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
def test_sculk_family_membership():
    sculk = G.style("sculk", V)
    assert sculk.block_names == ("calibrated_sculk_sensor", "sculk",
                                 "sculk_catalyst", "sculk_sensor",
                                 "sculk_shrieker", "sculk_vein")
    assert sculk.glow == ("calibrated_sculk_sensor", "sculk_catalyst",
                          "sculk_sensor")
    assert sculk.tint_group is None


def test_styles_merge_colour_variants():
    # Every dye colour and both oak species land in one family.
    glass = G.styles(V)["glass"]
    assert "red_stained_glass" in glass.block_names
    assert "blue_stained_glass" in glass.block_names
    oak = G.styles(V)["oak"]
    assert "dark_oak_planks" in oak.block_names
    assert "oak_planks" in oak.block_names


def test_min_members_is_a_lower_bound():
    loose = G.styles(V, min_members=4)
    tight = G.styles(V, min_members=20)
    assert set(tight) < set(loose)
    assert all(len(s.blocks) + len(s.items) >= 20 for s in tight.values())
    assert all(len(s.blocks) + len(s.items) >= 4 for s in loose.values())


def test_styles_are_ordered_biggest_first():
    sizes = [len(s.blocks) + len(s.items) for s in G.styles(V).values()]
    assert sizes == sorted(sizes, reverse=True)


def test_unknown_style_raises():
    with pytest.raises(ValueError, match="unknown style"):
        G.style("not_a_real_style", V)


def test_style_attaches_entity_members():
    # Entities join a family by shared name token rather than defining one.
    cherry = G.styles(V)["cherry"]
    assert any(e.name == "cherry_boat" for e in cherry.entities)


# ---------------------------------------------------------------------------
# texture_spec -- what generating one texture needs
# ---------------------------------------------------------------------------
def test_texture_spec_block_facts():
    spec = G.texture_spec("sculk_sensor", V)
    assert spec.name == "sculk_sensor"
    assert spec.display_name == "Sculk Sensor"
    # Both registries carry the name; the block wins.
    assert G.find_item("sculk_sensor", V) is not None
    assert spec.kind == "block"
    assert spec.size == 16
    assert spec.emissive
    assert not spec.transparent
    assert spec.material == "mineable/hoe"
    assert spec.style == "sculk"
    # Only the biome-tint families carry a tint group.
    assert spec.tint_group is None


def test_texture_spec_family_is_the_style_family():
    spec = G.texture_spec("sculk_sensor", V)
    assert spec.family == ("calibrated_sculk_sensor", "sculk",
                           "sculk_catalyst", "sculk_sensor",
                           "sculk_shrieker", "sculk_vein")
    assert spec.family == G.style("sculk", V).names


def test_texture_spec_item_has_no_block_facts():
    spec = G.texture_spec("echo_shard", V)
    assert spec.name == "echo_shard"
    assert spec.display_name == "Echo Shard"
    assert spec.kind == "item"
    assert spec.size == 16
    assert not spec.emissive
    assert not spec.transparent
    assert spec.material is None
    assert spec.tint_group is None
    assert spec.states == ()
    # "echo" is a one-member family: it is still reported, because that is the
    # honest answer to "who shares this look" (nobody).
    assert spec.style == "echo"
    assert spec.family == ("echo_shard",)


def test_texture_spec_transparent_block():
    spec = G.texture_spec("glass", V)
    assert spec.kind == "block"
    assert spec.transparent
    assert not spec.emissive
    # Glass ships no block states, so a single texture covers it.
    assert spec.states == ()
    assert spec.style == "glass"
    # The family spans the dye colours and the panes.
    assert "red_stained_glass" in spec.family


def test_texture_spec_states_shape():
    spec = G.texture_spec("sculk_sensor", V)
    assert [name for name, _ in spec.states] == ["power", "sculk_sensor_phase",
                                                 "waterlogged"]
    assert ("power", tuple(str(i) for i in range(16))) in spec.states
    assert ("sculk_sensor_phase",
            ("inactive", "active", "cooldown")) in spec.states
    # bool states ship no value list.
    assert ("waterlogged", ()) in spec.states


def test_texture_spec_reports_biome_tint_group():
    # The grass family is tiny -- grass_block is its only member -- but it is
    # the block the generator must draw greyscale, because in game the grass
    # palette tints it. Dropping small families here would double-tint the
    # texture instead of flagging it.
    spec = G.texture_spec("grass_block", V)
    assert spec.style == "grass"
    assert spec.family == ("grass_block",)
    assert spec.tint_group == "grass"
    assert not spec.emissive


def test_texture_spec_unknown_name_raises():
    with pytest.raises(ValueError, match="unknown block or item"):
        G.texture_spec("definitely_not_a_block", V)


# ---------------------------------------------------------------------------
# theme -- curated cross-registry groupings
# ---------------------------------------------------------------------------
def test_theme_reaches_content_that_never_says_its_name():
    # The point of a theme: the warden, the biome, the effect and the loot all
    # belong to sculk without carrying the word.
    sculk = G.theme("sculk", V)
    assert [e.name for e in sculk["entity"]] == ["warden"]
    assert [b.name for b in sculk["biome"]] == ["deep_dark"]
    assert [e.name for e in sculk["effect"]] == ["Darkness"]
    assert [e.name for e in sculk["enchantment"]] == ["swift_sneak"]
    items = {i.name for i in sculk["item"]}
    assert {"echo_shard", "disc_fragment_5", "music_disc_5",
            "recovery_compass"} <= items


def test_theme_is_a_superset_of_the_style_sharing_its_name():
    theme = {b.name for b in G.theme("sculk", V)["block"]}
    assert theme >= set(G.style("sculk", V).block_names)
    assert "reinforced_deepslate" in theme      # not in the style, still sculk


def test_theme_groups_every_kind_that_has_members():
    sculk = G.theme("sculk", V)
    assert set(sculk) == {"block", "item", "entity", "particle", "biome",
                          "effect", "enchantment"}
    assert all(sculk[kind] for kind in sculk)   # no empty groups


def test_theme_entries_carry_their_registry_facts():
    sculk = G.theme("sculk", V)
    warden = next(e for e in sculk["entity"] if e.name == "warden")
    assert warden.properties["category"] == "Hostile mobs"
    assert warden.properties["height"] == 2.9
    sensor = next(b for b in sculk["block"] if b.name == "sculk_sensor")
    assert sensor.properties["emit_light"] == 1


def test_unknown_theme_raises():
    with pytest.raises(ValueError, match="unknown theme"):
        G.theme("not_a_real_theme", V)


def test_themes_reports_the_curated_names_sorted():
    names = G.themes()
    assert "sculk" in names
    assert list(names) == sorted(names)


def test_redstone_family_carries_tints():
    redstone = G.styles(V)["redstone"]
    assert redstone.tint_group == "redstone"
    assert redstone.tint_colors
    assert all(isinstance(t, G.TintEntry) for t in redstone.tint_colors)


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
def test_biome_colors_match_vanilla_values():
    grass = G.biome_colors("grass", V)
    assert grass["badlands"] == "#90814d"
    assert grass["cherry_grove"] == "#b6db61"
    assert "#3f76e4" in G.biome_colors("water", V).values()
    assert G.biome_colors("foliage", V)


def test_biome_colors_skip_the_no_override_entry():
    # Biomes without an explicit tint carry a zero color in the data; reporting
    # those as black would be a silent painting bug.
    for group in ("grass", "foliage", "water"):
        assert "#000000" not in G.biome_colors(group, V).values()
    assert "plains" not in G.biome_colors("grass", V)


def test_biome_colors_filter_by_dimension():
    nether = G.biome_colors("water", V, dimension="nether")
    assert nether
    assert set(nether) <= {b.name for b in G.biomes(V) if b.dimension == "nether"}


def test_unknown_tint_group_raises():
    with pytest.raises(ValueError, match="unknown tint group"):
        G.biome_colors("chartreuse", V)


def test_tint_color_lookup():
    assert G.tint_color("grass", "cherry_grove", V) == 0xB6DB61
    assert G.tint_color("grass", "not_a_biome", V) is None


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
def test_search_spans_registries_and_styles():
    hits = G.search("sculk", V)
    kinds = {h.kind for h in hits}
    assert {"style", "block", "item"} <= kinds
    assert any(h.kind == "style" and h.name == "sculk" for h in hits)
    assert any(h.kind == "block" and h.name == "sculk_sensor" for h in hits)


def test_search_respects_kinds_and_limit():
    only_blocks = G.search("wool", V, kinds=("block",))
    assert only_blocks
    assert {h.kind for h in only_blocks} == {"block"}
    assert len(G.search("a", V, limit=3)) == 3


def test_search_matches_display_names():
    hits = G.search("Elytra", V)
    assert any(h.name == "elytra" for h in hits)


# ---------------------------------------------------------------------------
# Skin formats
# ---------------------------------------------------------------------------
def test_bedrock_skin_format_parsed_from_sample():
    fmt = G.skin_formats()[G.BEDROCK]
    assert fmt.image == (256, 256)
    assert fmt.arm_size == "wide"
    assert fmt.geometry_format == "1.14.0"
    assert "SkinData" in fmt.fields
    assert "CapeData" in fmt.fields
    assert fmt.animated_frames >= 1
    # The raw base64 blobs must be summarized, not copied wholesale.
    assert fmt.sample["SkinData"]["base64_chars"] > 1000
    assert "value" not in fmt.sample["SkinData"]


def test_bedrock_geometry_is_decoded():
    fmt = G.skin_formats()[G.BEDROCK]
    assert "SkinResourcePatch" in fmt.sample
    assert isinstance(fmt.sample["SkinResourcePatch"]["json"], dict)


def test_java_skin_format_uses_profile_schema():
    fmt = G.skin_formats()[G.PC]
    assert fmt.schema == "game_profile"
    assert fmt.edition == G.PC
    assert "properties[].value" in fmt.fields
    assert isinstance(fmt.sample["game_profile"], list)


# ---------------------------------------------------------------------------
# Raw dataset access and editions
# ---------------------------------------------------------------------------
def test_dataset_passthrough():
    assert "grass" in G.dataset("tints", V)
    assert G.dataset("materials", V)
    assert G.dataset("blocks", V)[0]["name"] == "air"


def test_unknown_dataset_raises():
    with pytest.raises(ValueError, match="unknown dataset"):
        G.dataset("dragons", V)


def test_kinds_cover_the_registries():
    kinds = G.kinds(V)
    assert {"blocks", "items", "entities", "particles", "biomes",
            "materials", "language", "tints", "protocol"} <= set(kinds)


def test_raw_returns_shared_cached_mapping():
    assert G.raw(V) is G.raw(V)


def test_bedrock_edition():
    bv = G.latest(G.BEDROCK)
    assert bv != V
    assert G.blocks(bv, G.BEDROCK)
    # Serialized skin samples only exist for Bedrock.
    assert "steve" in G.kinds(bv, G.BEDROCK)
    assert "steve" not in G.kinds(V, G.PC)


def test_overview_counts():
    ov = G.overview(V)
    assert ov["version"] == V
    assert ov["edition"] == G.PC
    assert ov["datasets"]["blocks"] == len(G.blocks(V))
    assert ov["versions"] >= 1
