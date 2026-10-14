"""Write a Java resource pack from generated textures.

A texture generator is only half the job: for Minecraft to use the PNGs they
have to sit in a resource pack at the paths the client loads, next to a
``pack.mcmeta`` saying which versions the pack is for.  This module writes that
pack.

``build_pack`` accepts a directory or a ``.zip`` and writes::

    pack.mcmeta
    assets/<ns>/textures/block/<name>_<face>.png     # one file per block face
    assets/<ns>/models/block/<name>.json
    assets/<ns>/blockstates/<name>.json
    assets/<ns>/textures/item/<name>.png             # item icons
    assets/<ns>/models/item/<name>.json

A resource pack cannot add new blocks or items, only replace what the game
ships, so the default namespace is ``minecraft``: the pack overrides vanilla
models and block states too -- that is what makes the generated textures show
up.  Two consequences worth knowing:

* a block whose vanilla model depends on block states (stairs, doors, ...)
  loses those state variants here: every state renders the generated model;
* the pack writes ``models/block/<name>.json``, so the block's *item* form
  (vanilla points its item model at the block model) is retextured as well.

``pack_format`` is version-dependent.  The table below is transcribed from
https://minecraft.wiki/w/Pack_format (resource packs, fetched 2026-10-14) and
covers the releases listed there; anything else -- snapshots, modded versions --
has to be given explicitly.  Since 1.21.9 the number is split into
``min_format``/``max_format``; the writer follows the version, not the number.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Mapping, Tuple, Union

from .texture import Texture

# ---------------------------------------------------------------------------
# Version -> resource pack format
# ---------------------------------------------------------------------------
# (first release, last release, resource pack format).  Releases only: a
# snapshot (``25w31a``) or a modded version is not in this table on purpose.
_PACK_FORMATS: Tuple[Tuple[str, str, float], ...] = (
    ("1.6.1", "1.8.9", 1),
    ("1.9", "1.10.2", 2),
    ("1.11", "1.12.2", 3),
    ("1.13", "1.14.4", 4),
    ("1.15", "1.16.1", 5),
    ("1.16.2", "1.16.5", 6),
    ("1.17", "1.17.1", 7),
    ("1.18", "1.18.2", 8),
    ("1.19", "1.19.2", 9),
    ("1.19.3", "1.19.3", 12),
    ("1.19.4", "1.19.4", 13),
    ("1.20", "1.20.1", 15),
    ("1.20.2", "1.20.2", 18),
    ("1.20.3", "1.20.4", 22),
    ("1.20.5", "1.20.6", 32),
    ("1.21", "1.21.1", 34),
    ("1.21.2", "1.21.3", 42),
    ("1.21.4", "1.21.4", 46),
    ("1.21.5", "1.21.5", 55),
    ("1.21.6", "1.21.6", 63),
    ("1.21.7", "1.21.8", 64),
    ("1.21.9", "1.21.10", 69.0),
    ("1.21.11", "1.21.11", 75.0),
    ("26.1", "26.1.2", 84.0),
    ("26.2", "26.2", 88.0),
    ("26.3", "26.3", 97.1),
)

# From this release on, pack.mcmeta carries min_format/max_format instead of
# pack_format (the 25w31a change, first shipped in 1.21.9).
_MIN_MAX_FROM = (1, 21, 9)

_MISSING_FORMAT_HINT = ("no resource pack format is known for {version!r} "
                        "(snapshots are not in the table); pass the number "
                        "explicitly")


def _ver(text: str) -> Tuple[int, ...]:
    parts = str(text).strip().split(".")
    if not parts or not all(p.isdigit() for p in parts):
        raise ValueError(_MISSING_FORMAT_HINT.format(version=text))
    return tuple(int(p) for p in parts)


def pack_format(version: str) -> float:
    """The resource pack format for a Java release, e.g. ``"1.21.6" -> 63``.

    Raises ``ValueError`` for a version the table does not list.
    """
    v = _ver(version)
    for first, last, fmt in _PACK_FORMATS:
        if _ver(first) <= v <= _ver(last):
            return fmt
    raise ValueError(_MISSING_FORMAT_HINT.format(version=version))


def _uses_min_max(version: str) -> bool:
    """Whether pack.mcmeta takes min_format/max_format for this version.

    A version we cannot parse at all (a snapshot, a modded version) gets the
    legacy ``pack_format`` field: it is the shape the widest range of clients
    accepts, and a caller that knows better can still pass ``format``.
    """
    try:
        return _ver(version) >= _MIN_MAX_FROM
    except ValueError:
        return False


def pack_meta(version: str, fmt: float = None, description: str = None) -> Dict:
    """The ``pack.mcmeta`` contents for a version (and optional format)."""
    fmt = pack_format(version) if fmt is None else fmt
    text = f"skinlib textures for {version}" if version else "skinlib textures"
    pack = {"description": description or text}
    if _uses_min_max(version):
        pack["min_format"] = fmt
        pack["max_format"] = fmt
    else:
        pack["pack_format"] = fmt
    return {"pack": pack}


# ---------------------------------------------------------------------------
# Models and block states
# ---------------------------------------------------------------------------
def _block_model(namespace: str, name: str, tex: Texture) -> Dict:
    """A block model pointing at ``<name>_<face>.png``, or a clear error.

    Only the two shapes our generators emit are supported: the three faces a
    cube needs (``top``/``side``/``bottom``) and a single sprite.
    """
    ref = lambda face: f"{namespace}:block/{name}_{face}"  # noqa: E731
    if tuple(tex.faces) == ("top", "side", "bottom"):
        side = ref("side")
        return {
            "parent": "minecraft:block/cube",
            "textures": {"up": ref("top"), "down": ref("bottom"),
                         "north": side, "south": side, "east": side,
                         "west": side, "particle": side},
        }
    if len(tex.faces) == 1:
        return {"parent": "minecraft:block/cube_all",
                "textures": {"all": ref(tex.faces[0])}}
    raise ValueError(
        f"block {name!r} has faces {list(tex.faces)}; the pack writer knows the "
        f"cube set ('top', 'side', 'bottom') and single-face textures")


def _item_model(namespace: str, name: str) -> Dict:
    return {"parent": "minecraft:item/generated",
            "textures": {"layer0": f"{namespace}:item/{name}"}}


def _blockstate(namespace: str, name: str) -> Dict:
    return {"variants": {"": {"model": f"{namespace}:block/{name}"}}}


# ---------------------------------------------------------------------------
# The pack itself
# ---------------------------------------------------------------------------
def _write_textures(root: Path, namespace: str, blocks: Mapping[str, Texture],
                    items: Mapping[str, Texture]) -> None:
    for name, tex in blocks.items():
        tex.save_faces(root / "assets" / namespace / "textures" / "block", name)
    for name, tex in items.items():
        if len(tex.faces) != 1:
            raise ValueError(f"item {name!r} has faces {list(tex.faces)}; "
                             f"an item icon is a single sprite")
        path = root / "assets" / namespace / "textures" / "item"
        path.mkdir(parents=True, exist_ok=True)
        tex.save(path / f"{name}.png")


def _write_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def build_pack(target: Union[str, Path], blocks: Mapping[str, Texture] = None,
               items: Mapping[str, Texture] = None, *,
               namespace: str = "minecraft", version: str = None,
               format: float = None, description: str = None) -> Path:
    """Write a resource pack for ``blocks``/``items`` (mappings of name->texture).

    ``target`` is a directory (written as a folder pack) or a path ending in
    ``.zip`` (written as a zip with ``pack.mcmeta`` at its root).  ``version``
    selects ``pack_format`` from the table; ``format`` overrides it for a
    version the table does not know.  Returns the path written.
    """
    blocks = dict(blocks or ())
    items = dict(items or ())
    if not blocks and not items:
        raise ValueError("a pack needs at least one block or item texture")
    if version is None and format is None:
        raise ValueError("pass version= (to look the format up) or format=")
    meta = pack_meta(version or "", format, description)

    target = Path(target)
    zipping = target.suffix.lower() == ".zip"
    root = Path(tempfile.mkdtemp(prefix="skinlib-pack-")) if zipping else target
    try:
        _write_json(root / "pack.mcmeta", meta)
        _write_textures(root, namespace, blocks, items)
        for name, tex in blocks.items():
            _write_json(root / "assets" / namespace / "models" / "block"
                        / f"{name}.json", _block_model(namespace, name, tex))
            _write_json(root / "assets" / namespace / "blockstates"
                        / f"{name}.json", _blockstate(namespace, name))
        for name in items:
            _write_json(root / "assets" / namespace / "models" / "item"
                        / f"{name}.json", _item_model(namespace, name))
        if zipping:
            target.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
                for path in sorted(root.rglob("*")):
                    if path.is_file():
                        zf.write(path, path.relative_to(root).as_posix())
    finally:
        if zipping:
            shutil.rmtree(root, ignore_errors=True)
    return target
