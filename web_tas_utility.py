import colorsys
import itertools
import copy

NORTH, EAST, SOUTH, WEST = range(4)

WHITE = "#ffffff"
GREY = "#a0a0a0"
RED = "#ff0000"
LIGHT_RED = "#ff6666"


class Tile:
    def __init__(self, name="", label="", glue_strengths=None, glue_labels=None, color="#ffffff"):
        self.name = name
        self.label = label
        self.glue_strengths = (
            glue_strengths if glue_strengths else [""] * 4
        )  # North, East, South, West
        self.glue_labels = glue_labels if glue_labels else [""] * 4
        self.color = color

    def __str__(self):
        return (
            f"Tile(name={self.name}, label={self.label}, "
            f"glue_strengths={self.glue_strengths}, glue_labels={self.glue_labels}, color={self.color})"
        )

    @classmethod
    def from_string(cls, tile_string):
        tile = cls()
        lines = tile_string.strip().split("\n")
        attributes = {
                line.split(" ")[0]: lines.split(" ")[1] for line in lines
        }
        tile.name = attributes.get("TILENAME", "")
        tile.label = attributes.get("LABEL", "")
        tile.glue_strengths = [
            attributes.get("NORTHBIND", ""),
            attributes.get("EASTBIND", ""),
            attributes.get("SOUTHBIND", ""),
            attributes.get("WESTBIND", ""),
        ]
        tile.glue_labels = [
            attributes.get("NORTHLABEL", ""),
            attributes.get("EASTLABEL", ""),
            attributes.get("SOUTHLABEL", ""),
            attributes.get("WESTLABEL", ""),
        ]
        tile.color = attributes.get("TILECOLOR", WHITE)
        return tile

    def to_string(self):
        components = [
            f"TILENAME {self.name}",
            f"LABEL {self.label}",
        ]
        directions = ["NORTH", "EAST", "SOUTH", "WEST"]
        for i, direction in enumerate(directions):
            if self.glue_strengths[i] and self.glue_labels[i]:
                components.append(f"{direction}BIND {self.glue_strengths[i]}")
                components.append(f"{direction}LABEL {self.glue_labels[i]}")
        components.append(f"TILECOLOR {self.color}")
        components.append("CREATE")
        return "\n".join(components)

    def _modify_attributes(self, name_suffix, glue_suffix, hue_shift):
        if name_suffix:
            self.name += name_suffix
        if glue_suffix:
            self.glue_labels = [glue + glue_suffix for glue in self.glue_labels]
        if hue_shift:
            r, g, b = [int(self.color[i:i+2]) for i in (1, 3, 5)]
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            h = (h + hue_shift) % 1
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            self.color = "#{:02x}{:02x}{:02x}".format(
                int(r * 255), int(g * 255), int(b * 255)
            )

    def permute(self, order, name_suffix="_perm", glue_suffix=None, hue_shift=0.0):
        self.glue_strengths = [self.glue_strengths[i] for i in order]
        self.glue_labels = [self.glue_labels[i] for i in order]
        self._modify_attributes(name_suffix, glue_suffix, hue_shift)

    def rotate(self, n=1, name_suffix="_rot", glue_suffix=None, hue_shift=0.0):
        self.permute(
            [(4 + i - n) % 4 for i in range(4)], name_suffix, glue_suffix, hue_shift
        )

    def flip_horizontal(self, name_suffix="_flipped_h", glue_suffix=None, hue_shift=0.0):
        self.permute([0, 3, 2, 1], name_suffix, glue_suffix, hue_shift)

    def flip_vertical(self, name_suffix="_flipped_v", glue_suffix=None, hue_shift=0.0):
        self.permute([2, 1, 0, 3], name_suffix, glue_suffix, hue_shift)

    def permuted(self, order, name_suffix="_perm", glue_suffix=None, hue_shift=0.0):
        return copy.deepcopy(self).permute(order, name_suffix, glue_suffix, hue_shift)

    def rotated(self, n=1, name_suffix="_rot", glue_suffix=None, hue_shift=0.0):
        return copy.deepcopy(self).rotate(n, name_suffix, glue_suffix, hue_shift)

    def flipped_horizontal(self, name_suffix="_flipped_h", glue_suffix=None, hue_shift=0.0):
        return copy.deepcopy(self).flip_horizontal(name_suffix, glue_suffix, hue_shift)

    def flipped_vertical(self, name_suffix="_flipped_v", glue_suffix=None, hue_shift=0.0):
        return copy.deepcopy(self).flip_vertical(name_suffix, glue_suffix, hue_shift)


class TileSet:
    def __init__(self):
        self.tiles = []
        self.unique_glue_counter = 0

    def __str__(self):
        tile_strings = [str(tile) for tile in self.tiles]
        return "TileSet(tiles=[\n    " + "\n    ".join(tile_strings) + "\n])"

    def get_unique_glue(self):
        glue = f"_{self.unique_glue_counter:0>2}"
        self.unique_glue_counter += 1
        return glue

    def find_color(self, color):
        return next(tile for tile in self.tiles if tile.color == color)

    def find_name(self, name):
        return next(tile for tile in self.tiles if tile.name == name)

    @classmethod
    def from_string(cls, tile_set_string):
        tiles = [
            Tile.from_string(tile_string)
            for tile_string in tile_set_string.split("\n\n")
        ]
        tile_set = cls()
        tile_set.tiles = tiles
        glues = [itertools.chain.from_iterable(tile.glue_labels) for tile in tiles]
        unique_glue_ids = [
            int(l[1:]) for l in glues if l.startswith("_") and l[1:].isnumeric()
        ]
        tile_set.unique_glue_counter = max(unique_glue_ids) + 1
        return tile_set

    def to_string(self):
        return "\n\n".join(tile.to_string() for tile in self.tiles)

    @classmethod
    def from_file(cls, file):
        with open(file_path, "r") as file:
            content = file.read()
        return cls().from_string(content)

    def to_file(self, file_path):
        with open(file_path, "w") as file:
            file.write(self.to_string())

    def permute(self, order, name_suffix="_perm", glue_suffix=None, hue_shift=0.0):
        for tile in self.tiles:
            tile.permute(order, name_suffix, glue_suffix, hue_shift)
        return self

    def rotate(self, n=1, name_suffix="_rot", glue_suffix=None, hue_shift=0.0):
        for tile in self.tiles:
            tile.rotate(n, name_suffix, glue_suffix, hue_shift)
        return self

    def flip_horizontal(self, name_suffix="_flipped_h", glue_suffix=None, hue_shift=0.0):
        for tile in self.tiles:
            tile.flip_horizontal(name_suffix, glue_suffix, hue_shift)
        return self

    def flip_vertical(self, name_suffix="_flipped_v", glue_suffix=None, hue_shift=0.0):
        for tile in self.tiles:
            tile.flip_vertical(name_suffix, glue_suffix, hue_shift)
        return self

    def permuted(self, order, name_suffix="_perm", glue_suffix=None, hue_shift=0.0):
        return copy.deepcopy(self).permute(order, name_suffix, glue_suffix, hue_shift)

    def rotated(self, n=1, name_suffix="_rot", glue_suffix=None, hue_shift=0.0):
        return copy.deepcopy(self).rotate(n, name_suffix, glue_suffix, hue_shift)

    def flipped_horizontal(self, name_suffix="_flipped_h", glue_suffix=None, hue_shift=0.0):
        return copy.deepcopy(self).flip_horizontal(name_suffix, glue_suffix, hue_shift)

    def flipped_vertical(self, name_suffix="_flipped_v", glue_suffix=None, hue_shift=0.0):
        return copy.deepcopy(self).flip_vertical(name_suffix, glue_suffix, hue_shift)

def compatible_tiles(tileset1, tileset2):
    compatible_pairs = []
    for tile_a, tile_b in itertools.product(tileset1.tiles, tileset2.tiles):
        for dir, opposite_dir in [(0, 2), (1, 3), (2, 0), (3, 1)]:
            if (
                tile_a.glue_strengths[dir]
                and tile_a.glue_labels[dir]
                and tile_a.glue_strengths[dir] == tile_b.glue_strengths[opposite_dir]
                and tile_a.glue_labels[dir] == tile_b.glue_labels[opposite_dir]
            ):
                compatible_pairs.append((tile_a, tile_b))
    return compatible_pairs


def concat_tilesets(*tilesets):
    new_tileset = TileSet()
    new_tileset.tiles = sum((tileset.tiles for tileset in tilesets), start=[])
    new_tileset.unique_glue_counter = max(
        tileset.unique_glue_counter for tileset in tilesets
    )
    return new_tileset
