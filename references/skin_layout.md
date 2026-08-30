# Minecraft Skin UV Layout Reference

This documents the standard Minecraft skin UV mapping, including the second
(overlay) layer used for hats, jackets, sleeves, and pants.

## Canvas

- Classic skin: **64 x 64** pixels
- HD skin: **128 x 128** pixels (all coordinates below are x2)

Each body part has two layers:

| Layer | Purpose |
|-------|---------|
| `base` | Inner layer drawn on the body mesh |
| `overlay` | Outer layer (hat/jacket/sleeve/pants); may use transparency |

## Part Keys

`head`, `body`, `right_arm`, `left_arm`, `right_leg`, `left_leg`

## Faces

Each part/layer is composed of six faces: `front`, `right`, `top`, `bottom`,
`back`, `left`.

## Base Layer Coordinates (64x64)

### Head (base)
| Face   | Box (x, y, w, h) |
|--------|------------------|
| front  | (8, 8, 8, 8)     |
| right  | (0, 8, 8, 8)     |
| top    | (8, 0, 8, 8)     |
| bottom | (16, 0, 8, 8)    |
| back   | (24, 8, 8, 8)    |
| left   | (16, 8, 8, 8)    |

### Head (overlay / hat)
| Face   | Box (x, y, w, h) |
|--------|------------------|
| front  | (40, 8, 8, 8)    |
| right  | (32, 8, 8, 8)    |
| top    | (40, 0, 8, 8)    |
| bottom | (48, 0, 8, 8)    |
| back   | (56, 8, 8, 8)    |
| left   | (48, 8, 8, 8)    |

## Common Regions (base -> overlay pairs)

### Body (torso)
| Layer | Face  | Box (x, y, w, h) |
|-------|-------|------------------|
| base front   | (20, 20, 8, 12) |
| base back    | (32, 20, 8, 12) |
| base sides   | (16, 20, 4, 12) / (28, 20, 4, 12) |
| base top     | (20, 16, 8, 4)  |
| base bottom  | (28, 16, 8, 4)  |
| over front   | (20, 36, 8, 12) |
| over back    | (32, 36, 8, 12) |
| over sides   | (16, 36, 4, 12) / (28, 36, 4, 12) |
| over top     | (20, 32, 8, 4)  |
| over bottom  | (28, 32, 8, 4)  |

### Arms (right / left)
Arms are 4x12 per face.

**Right arm base:**
| Face   | Box (x, y, w, h) |
|--------|------------------|
| front  | (44, 20, 4, 12)  |
| right  | (40, 20, 4, 12)  |
| top    | (44, 16, 4, 4)   |
| bottom | (48, 16, 4, 4)   |
| back   | (52, 20, 4, 12)  |
| left   | (48, 20, 4, 12)  |

**Right arm overlay (sleeve):** shift y by +16 (i.e. 36, 32).

**Left arm base:**
| Face   | Box (x, y, w, h) |
|--------|------------------|
| front  | (36, 52, 4, 12)  |
| right  | (32, 52, 4, 12)  |
| top    | (36, 48, 4, 4)   |
| bottom | (40, 48, 4, 4)   |
| back   | (44, 52, 4, 12)  |
| left   | (40, 52, 4, 12)  |

**Left arm overlay (sleeve):** shift x by +16 (i.e. 52, 48, 60, 56).

### Legs (right / left)
Legs are 4x12 per face.

**Right leg base:**
| Face   | Box (x, y, w, h) |
|--------|------------------|
| front  | (4, 20, 4, 12)   |
| right  | (0, 20, 4, 12)   |
| top    | (4, 16, 4, 4)    |
| bottom | (8, 16, 4, 4)    |
| back   | (12, 20, 4, 12)  |
| left   | (8, 20, 4, 12)   |

**Right leg overlay (pants):** shift y by +16.

**Left leg base:**
| Face   | Box (x, y, w, h) |
|--------|------------------|
| front  | (20, 52, 4, 12)  |
| right  | (16, 52, 4, 12)  |
| top    | (20, 48, 4, 4)   |
| bottom | (24, 48, 4, 4)   |
| back   | (28, 52, 4, 12)  |
| left   | (24, 52, 4, 12)  |

**Left leg overlay (pants):**
| Face   | Box (x, y, w, h) |
|--------|------------------|
| front  | (4, 52, 4, 12)   |
| right  | (0, 52, 4, 12)   |
| top    | (4, 48, 4, 4)    |
| bottom | (8, 48, 4, 4)    |
| back   | (12, 52, 4, 12)  |
| left   | (8, 52, 4, 12)   |

## Alex vs Steve

- **Steve** (default): arms are 4 px wide.
- **Alex** (slim): arms are 3 px wide. The UV layout differs slightly for
  slim arms; this tool targets the default Steve 4-px arms. For Alex skins,
  the arm regions shrink to 3 px wide.

## Cape (separate file)

A cape is a separate **64 x 32** PNG, not part of the skin file.
