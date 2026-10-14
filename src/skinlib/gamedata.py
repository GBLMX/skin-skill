"""Vanilla Minecraft game-data access, backed by minebase (PrismarineJS
minecraft-data).

Skin and texture generation has to line up with the game's own art direction,
which means knowing what actually exists in a given version: the full block /
item / entity / particle registries, which material family each belongs to,
what glows, what is transparent, the biome tint palettes, and the limits of the
skin formats themselves (image sizes, arm models, capes, animation frames,
geometry).

``minebase`` embeds all of minecraft-data and installs to roughly 330 MB, so it
is an **optional extra**::

    pip install "mc-skin[gamedata]"

Design notes:
    1. Importing this module never imports minebase. Everything is loaded
       lazily inside functions, and a missing dependency raises ``ImportError``
       with the install hint. A 330 MB data package must not slow down
       ``import skinlib``.
    2. Loaded data is cached per ``(edition, version)``. minecraft-data is
       static and read-only; the returned mappings are shared, so do not mutate
       them.
    3. Beyond the raw registries this exposes four generation-facing views:
       :func:`styles` (vanilla material/biome families such as ``sculk``,
       ``copper``, ``deepslate``, ``cherry``), :func:`search` (one phrase across
       every registry), :func:`biome_colors` (verified per-biome tint palettes)
       and :func:`skin_formats` (skin format facts parsed out of the data).
"""

from __future__ import annotations

import base64
import json
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field as _field
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Editions
# ---------------------------------------------------------------------------
PC = "pc"
"""Java Edition (minecraft-data edition name)."""

BEDROCK = "bedrock"
"""Bedrock Edition (minecraft-data edition name)."""

EDITIONS: Tuple[str, ...] = (PC, BEDROCK)
DEFAULT_EDITION = PC

#: Raised verbatim as the ``ImportError`` message when the extra is missing.
INSTALL_HINT = (
    'the vanilla data layer needs minebase (it embeds PrismarineJS '
    'minecraft-data, ~330 MB):\n'
    '    pip install "mc-skin[gamedata]"\n'
    'Then `from skinlib import gamedata` works as documented.'
)

# ---------------------------------------------------------------------------
# Style-family tokens
# ---------------------------------------------------------------------------
#: The 16 dye colors, stripped from the front of a name (``red_sandstone`` ->
#: ``sandstone``, ``white_wool`` -> ``wool``).
COLOR_TOKENS: Tuple[str, ...] = (
    "black", "blue", "brown", "cyan", "gray", "green", "light_blue",
    "light_gray", "lime", "magenta", "orange", "pink", "purple", "red",
    "white", "yellow",
)

#: Shade prefixes that qualify a color rather than naming a material
#: (``dark_oak`` -> ``oak``, ``pale_oak`` -> ``oak``).
SHADE_TOKENS: Tuple[str, ...] = ("dark", "light", "pale")

#: Adjectives that qualify a material rather than naming one, stripped from the
#: front of a name: ``polished_blackstone`` -> ``blackstone``,
#: ``cobbled_deepslate`` -> ``deepslate``, ``waxed_oxidized_copper`` ->
#: ``copper``, ``calibrated_sculk_sensor`` -> ``sculk``.
#:
#: Kept to genuine adjectives -- colour (see :data:`COLOR_TOKENS`), size,
#: condition, treatment and orientation. Subjects (``zombie_head``,
#: ``wolf_armor``), proper names (``spire_armor_trim_smithing_template``) and
#: head nouns (``ink_sac``, ``breeze_rod``) are deliberately absent: they name
#: the thing itself, so they keep their own family.
MODIFIER_TOKENS: Tuple[str, ...] = (
    # condition / state
    "attached", "broken", "budding", "calibrated", "chipped", "cracked",
    "crying", "damaged", "dead", "dripping", "exposed", "flowering",
    "flowing", "frosted", "gilded", "infested", "moving", "petrified",
    "poisonous", "popped", "powered", "reinforced", "sticky", "tipped",
    "trapped", "wet", "written", "writable",
    # size / amount
    "large", "medium", "small",
    # treatment / finish
    "activator", "baked", "carved", "chiseled", "cobbled", "coarse", "cut",
    "decorated", "detector", "filled", "glazed", "glistering", "lingering",
    "mossy", "ochre", "oxidized", "pearlescent", "polished", "potted", "raw",
    "rooted", "smooth", "splash", "stained", "stripped", "tinted", "verdant",
    "waxed", "weathered",
    # position / orientation
    "twisting", "wall", "weeping",
)

_LEAD_TOKENS = frozenset(COLOR_TOKENS + SHADE_TOKENS + MODIFIER_TOKENS)


def family_of(name: str) -> str:
    """Return the vanilla material family of a block/item ``name``.

    Strips leading color, shade and shape tokens, then keeps the first
    remaining token: ``waxed_oxidized_copper_grate`` -> ``copper``,
    ``dark_oak_planks`` -> ``oak``, ``calibrated_sculk_sensor`` -> ``sculk``.
    Spawn eggs collapse to a single ``spawn_egg`` family.

    This is a naming heuristic, not a registry field -- minecraft-data carries
    no family attribute. It is deliberately conservative: unrecognised prefixes
    keep their own family rather than being merged into a neighbour.
    """
    if name.endswith("_spawn_egg"):
        return "spawn_egg"
    tokens = name.split("_")
    while len(tokens) > 1 and tokens[0] in _LEAD_TOKENS:
        tokens.pop(0)
    return tokens[0]


#: Curated keyword sets, one per :func:`theme` name. Matching is a
#: case-insensitive substring test against both the registry id and the display
#: name, so a theme can reach content that never says its name.
#:
#: These are not vanilla data -- minecraft-data carries no theme field -- they
#: are a search vocabulary, and they are additive: extend the tuple to reach
#: more, add a key to support another theme.
THEMES: Dict[str, Tuple[str, ...]] = {
    # Deep Dark. "sculk" alone finds six blocks; the rest of the theme is the
    # warden, the echo shard family, the biome, and what the ancient city hands
    # out (Swift Sneak, music disc 5, darkness).
    "sculk": (
        "sculk", "warden", "echo", "disc_fragment", "music_disc_5",
        "deep_dark", "darkness", "swift_sneak", "reinforced_deepslate",
        "sonic_boom", "recovery_compass",
    ),
}


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class VersionInfo:
    """A Minecraft version, as advertised by minecraft-data."""

    version: str
    edition: str
    protocol: Optional[int] = None
    data_version: Optional[int] = None
    major: Optional[str] = None
    release_type: Optional[str] = None
    netty: Optional[bool] = None


@dataclass(frozen=True)
class BlockState:
    """A block-state property (``power``, ``waterlogged``, ...)."""

    name: str
    type: str
    num_values: int = 0
    values: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Block:
    """A block from the version's block registry."""

    name: str
    display_name: str
    id: int
    material: str = "default"
    hardness: float = 0.0
    resistance: float = 0.0
    stack_size: int = 64
    diggable: bool = False
    transparent: bool = False
    emit_light: int = 0
    filter_light: int = 0
    bounding_box: str = "block"
    default_state: int = 0
    min_state_id: int = 0
    max_state_id: int = 0
    states: Tuple[BlockState, ...] = ()
    drops: Tuple[int, ...] = ()

    @property
    def family(self) -> str:
        """Vanilla material family, see :func:`family_of`."""
        return family_of(self.name)

    @property
    def glows(self) -> bool:
        """True when the block emits light -- an emissive texture candidate."""
        return self.emit_light > 0


@dataclass(frozen=True)
class Item:
    """An item from the version's item registry."""

    name: str
    display_name: str
    id: int
    stack_size: int = 64

    @property
    def family(self) -> str:
        return family_of(self.name)


@dataclass(frozen=True)
class Entity:
    """An entity (mob, vehicle, projectile, ...)."""

    name: str
    display_name: str
    id: int
    internal_id: Optional[int] = None
    width: float = 0.0
    height: float = 0.0
    kind: str = "other"
    category: str = ""


@dataclass(frozen=True)
class Particle:
    """A particle type."""

    name: str
    id: int


@dataclass(frozen=True)
class Biome:
    """A biome.

    ``color`` is the raw integer minecraft-data ships, and it is **not** the
    vanilla biome color: checked against the game's own palette it reports
    roughly ``#78a7ff`` for every overworld biome and ``#000000`` for the End.
    It is kept as a passthrough only -- for colors you can actually paint with,
    use :func:`biome_colors` (the verified tint table).
    """

    name: str
    display_name: str
    id: int
    category: str = ""
    dimension: str = ""
    temperature: float = 0.0
    has_precipitation: bool = False
    color: int = 0

    @property
    def hex(self) -> str:
        """Raw shipped ``color`` as ``#rrggbb``; not the vanilla biome color."""
        return "#%06x" % (self.color & 0xFFFFFF)

    @property
    def rgb(self) -> Tuple[int, int, int]:
        """Raw shipped ``color`` as an ``(r, g, b)`` triple."""
        return ((self.color >> 16) & 0xFF, (self.color >> 8) & 0xFF,
                self.color & 0xFF)


@dataclass(frozen=True)
class TintEntry:
    """One biome-tint rule: the biomes it applies to and the resulting color."""

    biomes: Tuple[str, ...]
    color: int

    @property
    def hex(self) -> str:
        return "#%06x" % (self.color & 0xFFFFFF)

    @property
    def rgb(self) -> Tuple[int, int, int]:
        return ((self.color >> 16) & 0xFF, (self.color >> 8) & 0xFF,
                self.color & 0xFF)


@dataclass(frozen=True)
class Hit:
    """A :func:`search` result."""

    kind: str
    name: str
    display_name: str
    id: int


@dataclass(frozen=True)
class Style:
    """A vanilla style family: the content that shares one look.

    Built from the registries by :func:`styles` -- membership is derived from
    the names (plus, for entities/particles, token overlap), so it tracks
    whatever the version actually ships instead of a hand-written list.
    """

    name: str
    version: str
    edition: str
    blocks: Tuple[Block, ...] = ()
    items: Tuple[Item, ...] = ()
    entities: Tuple[Entity, ...] = ()
    particles: Tuple[Particle, ...] = ()
    tint_group: Optional[str] = None

    @property
    def block_names(self) -> Tuple[str, ...]:
        return tuple(b.name for b in self.blocks)

    @property
    def item_names(self) -> Tuple[str, ...]:
        return tuple(i.name for i in self.items)

    @property
    def names(self) -> Tuple[str, ...]:
        """Every distinct member name, sorted (blocks and items often share one)."""
        return tuple(sorted(set(self.block_names) | set(self.item_names)))

    @property
    def display_names(self) -> Tuple[str, ...]:
        return tuple(sorted({b.display_name for b in self.blocks}
                            | {i.display_name for i in self.items}))

    @property
    def materials(self) -> Tuple[str, ...]:
        """Distinct block ``material`` groups in this family."""
        return tuple(sorted({b.material for b in self.blocks}))

    @property
    def glow(self) -> Tuple[str, ...]:
        """Members that emit light -- the family's emissive texture targets."""
        return tuple(sorted(b.name for b in self.blocks if b.glows))

    @property
    def transparent(self) -> bool:
        """True when any member renders with transparency."""
        return any(b.transparent for b in self.blocks)

    @property
    def tint_colors(self) -> Tuple[TintEntry, ...]:
        """Biome-tint colors attached to this family, if any.

        Only the families that vanilla actually tints (``grass``, ``foliage``,
        ``water``, ``redstone``, ``constant``) carry these.
        """
        if not self.tint_group:
            return ()
        return tints(self.version, self.edition).get(self.tint_group, ())

    def __len__(self) -> int:
        return (len(self.blocks) + len(self.items) + len(self.entities)
                + len(self.particles))


@dataclass(frozen=True)
class TextureSpec:
    """What you have to know before generating one texture -- see
    :func:`texture_spec`.

    minecraft-data ships no texture paths and no texture dimensions, so this is
    derived from registry metadata: the entry's name and display name, whether
    a block or an item carries it, what emits light, what renders transparent,
    which biome tint applies, which material group it is mined under, and which
    family shares its look (see :func:`family_of`). ``family`` includes
    ``name`` itself, and a one-member family is reported as such instead of
    being dropped.

    ``size`` is fixed at 16: every vanilla block and item texture is 16x16
    (skins are the exception and have their own generator).
    """

    name: str
    display_name: str
    kind: str
    size: int = 16
    emissive: bool = False
    transparent: bool = False
    tint_group: Optional[str] = None
    material: Optional[str] = None
    style: Optional[str] = None
    family: Tuple[str, ...] = ()
    states: Tuple[Tuple[str, Tuple[str, ...]], ...] = ()


@dataclass(frozen=True)
class SkinFormat:
    """Facts about a skin format, parsed out of minecraft-data.

    For Bedrock these come from the serialized-skin sample minecraft-data ships
    (``steve.json``); for Java from the ``game_profile`` protocol type that
    carries the base64 ``textures`` property.
    """

    edition: str
    version: str
    schema: str
    fields: Tuple[str, ...] = ()
    image: Optional[Tuple[int, int]] = None
    arm_size: Optional[str] = None
    cape_image: Optional[Tuple[int, int]] = None
    geometry_format: Optional[str] = None
    persona: Optional[bool] = None
    animated_frames: int = 0
    sample: Mapping[str, Any] = _field(default_factory=dict)


@dataclass(frozen=True)
class ThemeEntry:
    """One registry entry that belongs to a theme -- see :func:`theme`."""

    kind: str
    name: str
    display_name: str
    properties: Mapping[str, Any] = _field(default_factory=dict)


# ---------------------------------------------------------------------------
# Backend plumbing (lazy, cached)
# ---------------------------------------------------------------------------
def available() -> bool:
    """True when minebase is importable, i.e. the data layer can be used."""
    try:
        import minebase  # noqa: F401
    except ImportError:
        return False
    return True


@lru_cache(maxsize=1)
def _minebase():
    try:
        import minebase
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(INSTALL_HINT) from exc
    return minebase


def source() -> str:
    """Filesystem path of the embedded minecraft-data checkout."""
    return str(_minebase().DATA_PATH)


def _edition(edition: str):
    name = str(edition).lower()
    if name not in EDITIONS:
        raise ValueError(f"unknown edition {edition!r}; choices: {sorted(EDITIONS)}")
    return _minebase().Edition(name)


@lru_cache(maxsize=4)
def _versions(edition: str) -> Tuple[str, ...]:
    return tuple(_minebase().supported_versions(_edition(edition)))


@lru_cache(maxsize=4)
def _common(edition: str) -> Mapping[str, Any]:
    return _minebase().load_common_data(_edition(edition))


@lru_cache(maxsize=16)
def _raw(edition: str, version: str) -> Mapping[str, Any]:
    """Cached raw minecraft-data for one edition/version. Treat as read-only."""
    return _minebase().load_version(version, _edition(edition))


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------
def versions(edition: str = DEFAULT_EDITION) -> Tuple[str, ...]:
    """Every version this data layer can load, oldest first."""
    return _versions(str(edition).lower())


def resolve(version: Optional[str] = None, edition: str = DEFAULT_EDITION) -> str:
    """Resolve ``None``/``"latest"`` to a concrete loadable version.

    Raises ``ValueError`` for a version minecraft-data has no data for.
    """
    edition = str(edition).lower()
    known = versions(edition)
    if version in (None, "", "latest"):
        return latest(edition)
    version = str(version)
    if version not in known:
        raise ValueError(
            f"unknown version {version!r} for edition {edition!r}; "
            f"{len(known)} available, latest is {known[-1]!r}"
        )
    return version


def latest(edition: str = DEFAULT_EDITION) -> str:
    """Newest loadable release for ``edition``.

    Prefers the highest data version among releases that minecraft-data
    actually ships data for, falling back to the last advertised version.
    """
    edition = str(edition).lower()
    known = versions(edition)
    in_data = set(known)
    best, best_key = None, None
    for entry in _common(edition).get("protocolVersions") or ():
        name = entry.get("minecraftVersion")
        if entry.get("releaseType") != "release" or name not in in_data:
            continue
        key = entry.get("dataVersion") or entry.get("version") or 0
        if best_key is None or key > best_key:
            best, best_key = name, key
    return best or known[-1]


def protocol_versions(edition: str = DEFAULT_EDITION) -> Tuple[VersionInfo, ...]:
    """Every protocol version known to minecraft-data, snapshots included."""
    edition = str(edition).lower()
    out: List[VersionInfo] = []
    for entry in _common(edition).get("protocolVersions") or ():
        name = entry.get("minecraftVersion")
        if not name:
            continue
        out.append(VersionInfo(
            version=name,
            edition=edition,
            protocol=entry.get("version"),
            data_version=entry.get("dataVersion"),
            major=entry.get("majorVersion"),
            release_type=entry.get("releaseType"),
            netty=entry.get("usesNetty"),
        ))
    return tuple(out)


def info(version: Optional[str] = None, edition: str = DEFAULT_EDITION) -> VersionInfo:
    """Protocol / data-version details for one version."""
    edition = str(edition).lower()
    version = resolve(version, edition)
    block = dict(_raw(edition, version).get("version") or {})
    extra = next(
        (e for e in _common(edition).get("protocolVersions") or ()
         if e.get("minecraftVersion") == version),
        {},
    )
    protocol = block.get("version", extra.get("version"))
    data_version = block.get("dataVersion", extra.get("dataVersion"))
    return VersionInfo(
        version=version,
        edition=edition,
        protocol=protocol if isinstance(protocol, int) else None,
        data_version=data_version if isinstance(data_version, int) else None,
        major=block.get("majorVersion") or extra.get("majorVersion"),
        release_type=block.get("releaseType") or extra.get("releaseType"),
        netty=extra.get("usesNetty"),
    )


# ---------------------------------------------------------------------------
# Raw dataset access
# ---------------------------------------------------------------------------
def kinds(version: Optional[str] = None, edition: str = DEFAULT_EDITION) -> Tuple[str, ...]:
    """Dataset names available for one version, sorted."""
    version = resolve(version, edition)
    return tuple(sorted(_raw(str(edition).lower(), version)))


def dataset(kind: str, version: Optional[str] = None,
            edition: str = DEFAULT_EDITION) -> Any:
    """Raw minecraft-data for one dataset, exactly as shipped.

    Use this for the datasets that have no typed accessor (``recipes``,
    ``protocol``, ``sounds``, ...). The returned object is the cached one --
    read it, do not mutate it.
    """
    edition = str(edition).lower()
    version = resolve(version, edition)
    data = _raw(edition, version)
    if kind not in data:
        raise ValueError(
            f"unknown dataset {kind!r} for {edition}/{version}; "
            f"choices: {sorted(data)}"
        )
    return data[kind]


def raw(version: Optional[str] = None,
        edition: str = DEFAULT_EDITION) -> Mapping[str, Any]:
    """Every dataset for one version, as a mapping. Read-only."""
    version = resolve(version, edition)
    return _raw(str(edition).lower(), version)


# ---------------------------------------------------------------------------
# Typed registries
# ---------------------------------------------------------------------------
def _states(raw_states: Iterable[Mapping[str, Any]]) -> Tuple[BlockState, ...]:
    return tuple(
        BlockState(
            name=s.get("name", ""),
            type=s.get("type", ""),
            num_values=s.get("num_values", 0),
            values=tuple(str(v) for v in s.get("values") or ()),
        )
        for s in raw_states
    )


@lru_cache(maxsize=16)
def _blocks(edition: str, version: str) -> Tuple[Block, ...]:
    return tuple(
        Block(
            name=b["name"],
            display_name=b.get("displayName", b["name"]),
            id=b.get("id", -1),
            material=b.get("material") or "default",
            hardness=b.get("hardness") or 0.0,
            resistance=b.get("resistance") or 0.0,
            stack_size=b.get("stackSize", 64),
            diggable=bool(b.get("diggable")),
            transparent=bool(b.get("transparent")),
            emit_light=b.get("emitLight") or 0,
            filter_light=b.get("filterLight") or 0,
            bounding_box=b.get("boundingBox") or "block",
            default_state=b.get("defaultState", 0),
            min_state_id=b.get("minStateId", 0),
            max_state_id=b.get("maxStateId", 0),
            states=_states(b.get("states") or ()),
            drops=tuple(b.get("drops") or ()),
        )
        for b in _raw(edition, version).get("blocks", ())
    )


@lru_cache(maxsize=16)
def _items(edition: str, version: str) -> Tuple[Item, ...]:
    return tuple(
        Item(
            name=i["name"],
            display_name=i.get("displayName", i["name"]),
            id=i.get("id", -1),
            stack_size=i.get("stackSize", 64),
        )
        for i in _raw(edition, version).get("items", ())
    )


@lru_cache(maxsize=16)
def _entities(edition: str, version: str) -> Tuple[Entity, ...]:
    return tuple(
        Entity(
            name=e["name"],
            display_name=e.get("displayName", e["name"]),
            id=e.get("id", -1),
            internal_id=e.get("internalId"),
            width=e.get("width") or 0.0,
            height=e.get("height") or 0.0,
            kind=e.get("type") or "other",
            category=e.get("category") or "",
        )
        for e in _raw(edition, version).get("entities", ())
    )


@lru_cache(maxsize=16)
def _particles(edition: str, version: str) -> Tuple[Particle, ...]:
    return tuple(
        Particle(name=p["name"], id=p.get("id", -1))
        for p in _raw(edition, version).get("particles", ())
    )


@lru_cache(maxsize=16)
def _biomes(edition: str, version: str) -> Tuple[Biome, ...]:
    return tuple(
        Biome(
            name=b["name"],
            display_name=b.get("displayName", b["name"]),
            id=b.get("id", -1),
            category=b.get("category") or "",
            dimension=b.get("dimension") or "",
            temperature=b.get("temperature") or 0.0,
            has_precipitation=bool(b.get("has_precipitation")),
            color=b.get("color") or 0,
        )
        for b in _raw(edition, version).get("biomes", ())
    )


def blocks(version: Optional[str] = None,
           edition: str = DEFAULT_EDITION) -> Tuple[Block, ...]:
    """The version's block registry."""
    edition = str(edition).lower()
    return _blocks(edition, resolve(version, edition))


def items(version: Optional[str] = None,
          edition: str = DEFAULT_EDITION) -> Tuple[Item, ...]:
    """The version's item registry."""
    edition = str(edition).lower()
    return _items(edition, resolve(version, edition))


def entities(version: Optional[str] = None,
             edition: str = DEFAULT_EDITION) -> Tuple[Entity, ...]:
    """The version's entity registry."""
    edition = str(edition).lower()
    return _entities(edition, resolve(version, edition))


def particles(version: Optional[str] = None,
              edition: str = DEFAULT_EDITION) -> Tuple[Particle, ...]:
    """The version's particle registry."""
    edition = str(edition).lower()
    return _particles(edition, resolve(version, edition))


def biomes(version: Optional[str] = None,
           edition: str = DEFAULT_EDITION) -> Tuple[Biome, ...]:
    """The version's biome registry, with vanilla map colors."""
    edition = str(edition).lower()
    return _biomes(edition, resolve(version, edition))


def materials(version: Optional[str] = None,
              edition: str = DEFAULT_EDITION) -> Mapping[str, Dict[int, float]]:
    """Material groups: ``{group: {block_id: hardness}}``."""
    return dataset("materials", version, edition)


def language(version: Optional[str] = None,
             edition: str = DEFAULT_EDITION) -> Mapping[str, str]:
    """Translation table: ``{"block.minecraft.sculk": "Sculk", ...}``."""
    return dataset("language", version, edition)


def translate(key: str, version: Optional[str] = None,
              edition: str = DEFAULT_EDITION) -> Optional[str]:
    """Look up one translation key, or ``None``."""
    return language(version, edition).get(key)


def tints(version: Optional[str] = None,
          edition: str = DEFAULT_EDITION) -> Dict[str, Tuple[TintEntry, ...]]:
    """Biome-tint rules grouped by kind (``grass``, ``foliage``, ``water``...).

    These are the colors vanilla multiplies grass/foliage/water textures by;
    the packing is the registry's own integer form (``0xRRGGBB``).
    """
    version = resolve(version, edition)
    out: Dict[str, Tuple[TintEntry, ...]] = {}
    for group, payload in (_raw(str(edition).lower(), version).get("tints") or {}).items():
        entries = payload.get("data") if isinstance(payload, Mapping) else payload
        out[group] = tuple(
            TintEntry(biomes=tuple(e.get("keys") or ()), color=e.get("color") or 0)
            for e in entries or ()
        )
    return out


def tint_color(group: str, biome: str, version: Optional[str] = None,
               edition: str = DEFAULT_EDITION) -> Optional[int]:
    """Tint color applied to ``group`` (``grass``, ``water``...) in ``biome``."""
    for entry in tints(version, edition).get(group, ()):
        if biome in entry.biomes:
            return entry.color
    return None


def biome_colors(group: str = "grass", version: Optional[str] = None,
                 edition: str = DEFAULT_EDITION,
                 dimension: Optional[str] = None,
                 category: Optional[str] = None) -> Dict[str, str]:
    """``{biome: "#rrggbb"}`` vanilla tint colors for one tint group.

    This is the trustworthy per-biome palette: it comes from the tint table the
    game actually multiplies grass/foliage/water by, and it matches the vanilla
    values (badlands grass ``#90814d``, cherry grove grass ``#b6db61``, water
    ``#3f76e4``). Groups are ``grass``, ``foliage``, ``water``, ``redstone``
    and ``constant``.

    Biomes with no explicit override are omitted rather than reported as black
    -- in the data they carry a zero color, meaning "use the group default".
    """
    version = resolve(version, edition)
    table = tints(version, edition)
    if group not in table:
        raise ValueError(f"unknown tint group {group!r}; choices: {sorted(table)}")
    keep = None
    if dimension or category:
        keep = {
            b.name for b in biomes(version, edition)
            if (not dimension or b.dimension == dimension)
            and (not category or b.category == category)
        }
    out: Dict[str, str] = OrderedDict()
    for entry in table[group]:
        if entry.color == 0:
            continue
        for name in entry.biomes:
            if keep is None or name in keep:
                out[name] = entry.hex
    return out


def find_block(name: str, version: Optional[str] = None,
               edition: str = DEFAULT_EDITION) -> Optional[Block]:
    """Look up one block by name (``"sculk_sensor"``), or ``None``."""
    return _index_blocks(version, str(edition).lower()).get(name)


def find_item(name: str, version: Optional[str] = None,
              edition: str = DEFAULT_EDITION) -> Optional[Item]:
    """Look up one item by name, or ``None``."""
    return _index_items(version, str(edition).lower()).get(name)


def find_entity(name: str, version: Optional[str] = None,
                edition: str = DEFAULT_EDITION) -> Optional[Entity]:
    """Look up one entity by name, or ``None``."""
    return _index_entities(version, str(edition).lower()).get(name)


@lru_cache(maxsize=16)
def _index_blocks(version: Optional[str], edition: str) -> Mapping[str, Block]:
    return {b.name: b for b in blocks(version, edition)}


@lru_cache(maxsize=16)
def _index_items(version: Optional[str], edition: str) -> Mapping[str, Item]:
    return {i.name: i for i in items(version, edition)}


@lru_cache(maxsize=16)
def _index_entities(version: Optional[str], edition: str) -> Mapping[str, Entity]:
    return {e.name: e for e in entities(version, edition)}


# ---------------------------------------------------------------------------
# Generation-facing views
# ---------------------------------------------------------------------------
#: Materials that vanilla actually tints (see :func:`tints`).
TINT_GROUPS: Tuple[str, ...] = ("grass", "foliage", "water", "redstone", "constant")


@lru_cache(maxsize=16)
def _styles(edition: str, version: str) -> Mapping[str, Style]:
    bl = _blocks(edition, version)
    it = _items(edition, version)

    fam_blocks: Dict[str, List[Block]] = defaultdict(list)
    fam_items: Dict[str, List[Item]] = defaultdict(list)
    for block in bl:
        fam_blocks[family_of(block.name)].append(block)
    for item in it:
        fam_items[family_of(item.name)].append(item)

    known = set(fam_blocks) | set(fam_items)
    fam_entities: Dict[str, List[Entity]] = defaultdict(list)
    fam_particles: Dict[str, List[Particle]] = defaultdict(list)
    # Entities and particles join a family when their name shares a token with
    # it ("copper_golem" -> copper, "cherry_boat" -> cherry, "sculk_soul" ->
    # sculk); they never define one on their own.
    for entity in _entities(edition, version):
        for token in entity.name.split("_"):
            if token in known:
                fam_entities[token].append(entity)
    for particle in _particles(edition, version):
        for token in particle.name.split("_"):
            if token in known:
                fam_particles[token].append(particle)

    out: Dict[str, Style] = OrderedDict()
    for name in sorted(known, key=lambda n: (-(len(fam_blocks[n]) + len(fam_items[n])), n)):
        out[name] = Style(
            name=name,
            version=version,
            edition=edition,
            blocks=tuple(sorted(fam_blocks[name], key=lambda b: b.name)),
            items=tuple(sorted(fam_items[name], key=lambda i: i.name)),
            entities=tuple(sorted(fam_entities[name], key=lambda e: e.name)),
            particles=tuple(sorted(fam_particles[name], key=lambda p: p.name)),
            tint_group=name if name in TINT_GROUPS else None,
        )
    return out


def styles(version: Optional[str] = None, edition: str = DEFAULT_EDITION,
           min_members: int = 4) -> Dict[str, Style]:
    """Vanilla style families, biggest first.

    A family is the content that shares one look -- ``sculk``, ``copper``,
    ``deepslate``, ``cherry``, ``glass``, ``terracotta`` -- derived from the
    registries themselves (see :func:`family_of`), so it follows the version
    rather than a hand-maintained list. ``min_members`` drops the long tail of
    single-item families.

    Example: generate "sculk" and pull the full target set first::

        s = gamedata.styles("1.21.6")["sculk"]
        s.block_names   # ('calibrated_sculk_sensor', 'sculk', 'sculk_catalyst', ...)
        s.glow          # ('calibrated_sculk_sensor', 'sculk_catalyst', 'sculk_sensor')
    """
    edition = str(edition).lower()
    version = resolve(version, edition)
    return {
        name: style
        for name, style in _styles(edition, version).items()
        if len(style.blocks) + len(style.items) >= min_members
    }


def style(name: str, version: Optional[str] = None, edition: str = DEFAULT_EDITION,
          min_members: int = 1) -> Style:
    """One style family by name; raises ``ValueError`` if unknown."""
    found = styles(version, edition, min_members=min_members)
    if name not in found:
        raise ValueError(
            f"unknown style {name!r}; choices: {sorted(found)[:40]}"
            + (f" (+{len(found) - 40} more)" if len(found) > 40 else "")
        )
    return found[name]


def texture_spec(name: str, version: Optional[str] = None,
                 edition: str = DEFAULT_EDITION) -> TextureSpec:
    """Everything needed to generate one texture for ``name``.

    minecraft-data carries no texture paths or dimensions, so the spec comes
    from registry metadata plus the style families this module derives from it:

    1. ``name`` is looked up in the block registry first, then in the item
       registry. A name both registries carry (``"sculk_sensor"``) reports
       ``kind="block"``; a name in neither raises ``ValueError``.
    2. ``emissive`` is true when the block emits light (``emitLight > 0``).
       Membership in the style family's glow set counts too (see
       :meth:`Style.glow`); in practice that is the same set of blocks, since
       the family glow is derived from ``emitLight`` in the first place.
    3. ``transparent`` is the block's own transparency flag, always false for
       items.
    4. ``tint_group``, ``style``, ``family`` and ``material`` all come from the
       name's family (:func:`family_of`, resolved against :func:`styles` with
       ``min_members=1``) rather than from a second guess. ``family`` always
       contains the name itself, and a one-member family is still reported --
       ``"echo_shard"`` gets ``style="echo"`` and ``family=("echo_shard",)``,
       which says what the data says: there is no sibling to share a palette
       with. Both stay empty only when no family can be computed at all.
       ``style`` is a family name, not a promise that the default
       :func:`styles` view lists it: that view drops families below its own
       ``min_members``. ``material`` is ``None`` for items, and is passed
       through verbatim for blocks (``"mineable/hoe"``, or the data's bare
       ``"default"``).
    5. ``states`` is ``((state name, values), ...)`` -- how many variants a
       texture needs. States the data ships as plain ``bool``/``int``
       properties carry no value list and report ``()``; items have no states
       at all.

    Example::

        s = gamedata.texture_spec("sculk_sensor")
        s.kind, s.emissive, s.material, s.style
        # ('block', True, 'mineable/hoe', 'sculk')
        s.family        # the six sculk block names, sorted
        s.states        # (('power', (...)), ('sculk_sensor_phase', (...)), ...)
    """
    edition = str(edition).lower()
    version = resolve(version, edition)

    block = find_block(name, version, edition)
    if block is not None:
        kind = "block"
        display_name = block.display_name
        transparent = block.transparent
        material: Optional[str] = block.material
        states = tuple((s.name, s.values) for s in block.states)
        emits = block.emit_light > 0
    else:
        item = find_item(name, version, edition)
        if item is None:
            raise ValueError(
                f"unknown block or item {name!r}; nothing by that name in "
                f"{edition} {version}"
            )
        kind = "item"
        display_name = item.display_name
        transparent = False
        material = None
        states = ()
        emits = False

    family = styles(version, edition, min_members=1).get(family_of(name))
    return TextureSpec(
        name=name,
        display_name=display_name,
        kind=kind,
        size=16,
        emissive=emits or (family is not None and name in family.glow),
        transparent=transparent,
        tint_group=family.tint_group if family else None,
        material=material,
        style=family.name if family else None,
        family=family.names if family else (),
        states=states,
    )


def _theme_entry(kind: str, raw: Mapping[str, Any]) -> "ThemeEntry":
    """One registry entry, reduced to what an artist needs to know."""
    props: Dict[str, Any] = {}
    if kind == "block":
        props = {
            "material": raw.get("material") or "default",
            "hardness": raw.get("hardness") or 0.0,
            "emit_light": raw.get("emitLight") or 0,
            "transparent": bool(raw.get("transparent")),
        }
    elif kind == "entity":
        props = {
            "category": raw.get("category") or "",
            "width": raw.get("width") or 0.0,
            "height": raw.get("height") or 0.0,
        }
    elif kind == "biome":
        props = {
            "dimension": raw.get("dimension") or "",
            "temperature": raw.get("temperature") or 0.0,
        }
    elif kind == "effect":
        props = {"type": raw.get("type") or ""}
    elif kind == "enchantment":
        props = {"max_level": raw.get("maxLevel")}
    elif kind == "item":
        props = {"stack_size": raw.get("stackSize", 64)}
    return ThemeEntry(
        kind=kind,
        name=raw.get("name") or "",
        display_name=raw.get("displayName") or raw.get("name") or "",
        properties=props,
    )


#: Registry keys behind each :func:`theme` kind.
_THEME_KINDS: Tuple[Tuple[str, str], ...] = (
    ("block", "blocks"), ("item", "items"), ("entity", "entities"),
    ("particle", "particles"), ("biome", "biomes"), ("effect", "effects"),
    ("enchantment", "enchantments"),
)


def theme(name: str, version: Optional[str] = None,
          edition: str = DEFAULT_EDITION) -> Dict[str, Tuple["ThemeEntry", ...]]:
    """Everything belonging to one vanilla theme, grouped by registry kind.

    A theme is not a registry field -- minecraft-data has no "sculk" flag. This
    matches the curated keyword sets in :data:`THEMES` against every registry,
    which is the whole point: most of a theme's content does not carry its name.
    The literal ``sculk`` family is six blocks, and :func:`styles` finds exactly
    those; the *theme* also contains the warden, echo shards, the deep dark, the
    darkness effect, Swift Sneak, reinforced deepslate and music disc 5 -- none
    of which says "sculk".

    Returns ``{kind: (ThemeEntry, ...)}`` over the kinds in :data:`_THEME_KINDS`.
    """
    key = str(name).lower()
    if key not in THEMES:
        raise ValueError(f"unknown theme {name!r}; choices: {sorted(THEMES)}")
    tokens = THEMES[key]
    data = _raw(str(edition).lower(), resolve(version, edition))

    def matches(raw: Mapping[str, Any]) -> bool:
        hay = f"{raw.get('name', '')} {raw.get('displayName', '')}".lower()
        return any(token in hay for token in tokens)

    out: Dict[str, Tuple[ThemeEntry, ...]] = OrderedDict()
    for kind, dataset_key in _THEME_KINDS:
        entries = tuple(_theme_entry(kind, raw)
                        for raw in data.get(dataset_key, ()) if matches(raw))
        if entries:
            out[kind] = entries
    return out


def themes() -> Tuple[str, ...]:
    """The theme names :func:`theme` understands."""
    return tuple(sorted(THEMES))


def search(phrase: str, version: Optional[str] = None,
           edition: str = DEFAULT_EDITION, kinds: Optional[Sequence[str]] = None,
           limit: Optional[int] = None) -> Tuple[Hit, ...]:
    """Find ``phrase`` across every registry, plus matching style families.

    Case-insensitive substring match on both the identifier and the display
    name. ``kinds`` restricts the search (``("block", "item")``).
    """
    edition = str(edition).lower()
    version = resolve(version, edition)
    needle = phrase.lower()
    wanted = set(kinds) if kinds else {"style", "block", "item", "entity",
                                       "particle", "biome"}

    def matches(name: str, display: str) -> bool:
        return needle in name.lower() or needle in display.lower()

    hits: List[Hit] = []
    if "style" in wanted:
        for fam in styles(version, edition, min_members=1):
            if needle in fam:
                hits.append(Hit(kind="style", name=fam, display_name=fam, id=-1))
    if "block" in wanted:
        hits.extend(Hit("block", b.name, b.display_name, b.id)
                    for b in _blocks(edition, version) if matches(b.name, b.display_name))
    if "item" in wanted:
        hits.extend(Hit("item", i.name, i.display_name, i.id)
                    for i in _items(edition, version) if matches(i.name, i.display_name))
    if "entity" in wanted:
        hits.extend(Hit("entity", e.name, e.display_name, e.id)
                    for e in _entities(edition, version) if matches(e.name, e.display_name))
    if "particle" in wanted:
        hits.extend(Hit("particle", p.name, p.name, p.id)
                    for p in _particles(edition, version) if needle in p.name.lower())
    if "biome" in wanted:
        hits.extend(Hit("biome", b.name, b.display_name, b.id)
                    for b in _biomes(edition, version) if matches(b.name, b.display_name))
    return tuple(hits[:limit] if limit else hits)


def _summarize_b64(text: str, limit: int = 32) -> Dict[str, Any]:
    """Describe a base64 blob instead of dumping it into the console."""
    try:
        payload = base64.b64decode(text, validate=False)
    except Exception:  # noqa: BLE001 - malformed sample data, just report it
        return {"base64_chars": len(text), "decoded": None}
    info: Dict[str, Any] = {"base64_chars": len(text), "decoded_bytes": len(payload)}
    if limit and len(text) <= limit:
        info["value"] = text
    stripped = payload.lstrip()[:1]
    if stripped in (b"{", b"["):
        try:
            info["json"] = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            pass
    elif payload and all(32 <= c < 127 for c in payload[:64]):
        text_value = payload.decode("utf-8", "replace")
        if len(text_value) <= 64:
            info["value"] = text_value
    return info


def _bedrock_skin_format(version: str) -> SkinFormat:
    sample = _raw(BEDROCK, version).get("steve") or {}
    geometry = patch = None
    if isinstance(sample.get("SkinGeometryData"), str) and sample["SkinGeometryData"]:
        decoded = _summarize_b64(sample["SkinGeometryData"]).get("json")
        if isinstance(decoded, Mapping):
            geometry = decoded.get("format_version")
    if isinstance(sample.get("SkinResourcePatch"), str) and sample["SkinResourcePatch"]:
        decoded = _summarize_b64(sample["SkinResourcePatch"]).get("json")
        if isinstance(decoded, Mapping):
            patch = decoded

    summarized: Dict[str, Any] = {}
    for key in sorted(sample):
        value = sample[key]
        if isinstance(value, str) and len(value) > 64:
            summarized[key] = _summarize_b64(value)
        elif isinstance(value, list):
            summarized[key] = value if len(value) <= 4 else f"list[{len(value)}]"
        else:
            summarized[key] = value

    types = _raw(BEDROCK, version).get("protocol", {}).get("types", {})
    schema = ", ".join(sorted(n for n in types
                              if any(t in n.lower() for t in ("skin", "cape", "persona"))))

    width, height = sample.get("SkinImageWidth") or 0, sample.get("SkinImageHeight") or 0
    cape_w, cape_h = sample.get("CapeImageWidth") or 0, sample.get("CapeImageHeight") or 0
    if patch is not None:
        summarized["SkinResourcePatch"] = {"base64_chars":
                                           len(sample.get("SkinResourcePatch", "")),
                                           "json": patch}
    return SkinFormat(
        edition=BEDROCK,
        version=version,
        schema=schema or "steve",
        fields=tuple(sorted(sample)),
        image=(width, height) if width and height else None,
        arm_size=sample.get("ArmSize") or None,
        cape_image=(cape_w, cape_h) if cape_w and cape_h else None,
        geometry_format=geometry,
        persona=sample.get("PersonaSkin"),
        animated_frames=len(sample.get("AnimatedImageData") or ()),
        sample=summarized,
    )


def _java_skin_format(version: str) -> SkinFormat:
    types = _raw(PC, version).get("protocol", {}).get("types", {})
    profile = types.get("game_profile")
    return SkinFormat(
        edition=PC,
        version=version,
        schema="game_profile",
        fields=("name", "properties[].name", "properties[].value",
                "properties[].signature"),
        sample={"game_profile": profile,
                "note": "skins travel as a base64 'textures' property on the "
                        "player profile; the value is JSON carrying "
                        "textures.SKIN.url and textures.SKIN.metadata.model"},
    )


def skin_formats(pc_version: Optional[str] = None,
                 bedrock_version: Optional[str] = None) -> Dict[str, SkinFormat]:
    """Skin format facts for both editions, parsed from the data.

    Bedrock reports the real serialized-skin schema and its concrete sample
    values (image size, arm model, cape, geometry version, animation frames);
    Java reports the profile/property schema that carries the ``textures``
    blob. Note that minecraft-data's Bedrock sample is a 256x256 persona skin;
    :mod:`skinlib` itself works in the classic 64x64 / 128x128 spaces.
    """
    return {
        PC: _java_skin_format(resolve(pc_version, PC)),
        BEDROCK: _bedrock_skin_format(resolve(bedrock_version, BEDROCK)),
    }


def overview(version: Optional[str] = None,
             edition: str = DEFAULT_EDITION) -> Dict[str, Any]:
    """Counts per dataset plus the backend location, for discovery/CLI use."""
    edition = str(edition).lower()
    version = resolve(version, edition)
    data = _raw(edition, version)
    counts: Dict[str, Any] = OrderedDict()
    for key in sorted(data):
        value = data[key]
        counts[key] = len(value) if isinstance(value, (list, dict)) else value
    return {
        "edition": edition,
        "version": version,
        "versions": len(versions(edition)),
        "source": source(),
        "datasets": counts,
    }


__all__ = [
    # editions / versions
    "PC", "BEDROCK", "EDITIONS", "DEFAULT_EDITION",
    "TINT_GROUPS", "COLOR_TOKENS", "SHADE_TOKENS", "MODIFIER_TOKENS",
    "THEMES", "INSTALL_HINT",
    "available", "source", "versions", "latest", "resolve", "info",
    "protocol_versions", "kinds", "dataset", "raw", "overview",
    # records
    "VersionInfo", "Block", "BlockState", "Item", "Entity", "Particle",
    "Biome", "TintEntry", "Hit", "Style", "TextureSpec", "SkinFormat",
    "ThemeEntry",
    # registries
    "blocks", "items", "entities", "particles", "biomes", "materials",
    "language", "translate", "tints", "tint_color", "biome_colors",
    "find_block", "find_item", "find_entity",
    # generation-facing
    "family_of", "styles", "style", "texture_spec", "search", "skin_formats",
    "theme", "themes",
]
