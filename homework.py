import itertools

from web_tas_utility import *

def generate_tower(width, height):
    tower = TileSet()

    # First row: hardcode height as binary string
    binary_string = f"{2**width - (height//2):0>{width}b}"
    first_row = [Tile(f"seed_bit_{width-i-1:0>2}", bit) for i, bit in enumerate(binary_string)]
    first_row[-1].color = RED  # seed tile
    # unique glues for hardcoding
    for tile_a, tile_b in itertools.pairwise(first_row):
        tile_a.glue_strengths[EAST] = tile_b.glue_strengths[WEST] = "2"
        tile_a.glue_labels[EAST] = tile_b.glue_labels[WEST] = tower.get_unique_glue()
    # north labels
    first_row[0].glue_labels[NORTH] = "left_inc_" + first_row[0].label[NORTH]
    first_row[0].glue_strengths[NORTH] = "1"
    for tile in first_row[1:-1]:
        tile.glue_labels[NORTH] = "inc_" + tile.label
        tile.glue_strengths[NORTH] = "1"
    first_row[-1].glue_labels[NORTH] = "right_inc_" + first_row[-1].label[NORTH]
    first_row[-1].glue_strengths[NORTH] = "2"
    tower.tiles.extend(first_row)

    # Increment tiles: flip the right-most bit and carry to the left
    increment_tiles = [
        Tile("left_inc_0", "0", ["2", "1", "1", ""], ["left_copy_0", "no_carry", "left_inc_0", ""]),
        Tile("left_inc_0_c", "1", ["2", "1", "1", ""], ["left_copy_1", "carry", "left_inc_0", ""]),
        Tile("left_inc_1", "1", ["2", "1", "1", ""], ["left_copy_1", "no_carry", "left_inc_1", ""]),
        Tile("left_inc_1_c", "0", ["2", "1", "1", ""], ["rollover", "carry", "left_inc_1", ""], WHITE if height % 2 else LIGHT_RED),
        Tile("inc_0", "0", ["1", "1", "1", "1"], ["copy_0", "no_carry", "inc_0", "no_carry"]),
        Tile("inc_0_c", "1", ["1", "1", "1", "1"], ["copy_1", "carry", "inc_0", "no_carry"]),
        Tile("inc_1", "1", ["1", "1", "1", "1"], ["copy_1", "no_carry", "inc_1", "no_carry"]),
        Tile("inc_1_c", "0", ["1", "1", "1", "1"], ["copy_0", "carry", "inc_1", "carry"]),
        Tile("right_inc_0", "1", ["1", "", "2", "1"], ["right_copy_1", "", "right_inc_0", "no_carry"]),
        Tile("right_inc_1", "0", ["1", "", "2", "1"], ["right_copy_0", "", "right_inc_1", "carry"]),
    ]
    tower.tiles.extend(increment_tiles)

    # Copy tiles: create a row with the same labels to move the double glue back to the right
    copy_tiles = [
        Tile("left_copy_0", "0", ["1", "1", "2", ""], ["left_inc_0", "copy", "left_copy_0", ""]),
        Tile("left_copy_1", "1", ["1", "1", "2", ""], ["left_inc_1", "copy", "left_copy_1", ""]),
        Tile("copy_0", "0", ["1", "1", "1", "1"], ["inc_0", "copy", "copy_0", "copy"]),
        Tile("copy_1", "1", ["1", "1", "1", "1"], ["inc_1", "copy", "copy_1", "copy"]),
        Tile("right_copy_0", "0", ["2", "", "1", "1"], ["right_inc_0", "", "right_copy_0", "copy"]),
        Tile("right_copy_1", "1", ["2", "", "1", "1"], ["right_inc_1", "", "right_copy_1", "copy"]),
    ]
    tower.tiles.extend(copy_tiles)

    # Extra row: as rows come in two, we have to add an extra one if we want to have an odd height
    if height % 2:
        extra_row = [
                Tile("left_extra", "0", ["", "1", "2", ""], ["", "extra", "rollover", ""], LIGHT_RED),
                Tile("extra", "0", ["", "1", "1", "1"], ["", "extra", "copy_0", "extra"]),
                Tile("right_extra", "0", ["", "", "1", "1"], ["", "", "right_copy_0", "extra"]),
        ]
        tower.tiles.extend(extra_row)

    # For prettyness
    for tile in tower.tiles:
        if tile.color == WHITE and tile.label == "1":
            tile.color = GREY

    return tower

def spell_gamma(n):
    tower_1 = generate_tower(n,     2**n+n).flip_horizontal(name_suffix="_t1")
    tower_2 = generate_tower(n, 2**(n-1)+n).permute([1, 0, 3, 2], name_suffix="_t2")
    tower_3 = generate_tower(n,          n).permute([2, 1, 0, 3], name_suffix="_t3", glue_suffix="'")
    gamma   = concat_tilesets(tower_1, tower_2, tower_3)

    # connect the towers
    tile_a, tile_b = tower_1.find_color(LIGHT_RED), tower_2.find_color(RED)
    tile_a.glue_strengths[EAST] = tile_b.glue_strengths[WEST] = 2
    tile_a.glue_labels[EAST]    = tile_b.glue_labels[WEST]    = gamma.get_unique_glue()

    tile_c, tile_d = tower_2.find_color(LIGHT_RED), tower_3.find_color(RED)
    tile_c.glue_strengths[SOUTH] = tile_d.glue_strengths[NORTH] = 2
    tile_c.glue_labels[SOUTH]    = tile_d.glue_labels[NORTH]    = gamma.get_unique_glue()

    return gamma

def busy_tiles(n):
    # initial tower
    towers = [ generate_tower(n, 2**(n+1)) ]

    # secondary towers
    for i in range(1, 4):
        # rotate counter-clockwise
        towers.append(towers[0].rotated(n=4-i, name_suffix="_t"+str(i), glue_suffix="_t"+str(i)))
        # remove base layer
        towers[-1].tiles = [ tile for tile in towers[-1].tiles if "seed" not in tile.name ]
        # add base layer glues to side of previous tower
        for tile in towers[-2].tiles:
            if "left" in tile.name:
                tile.glue_labels[(4-i)%4] = "inc_0_t"+str(i)
                tile.glue_strengths[(4-i)%4] = 1
        # right-most bit of a secondary tower is the top-left tile of the previous tower
        right_base = towers[-2].find_color(LIGHT_RED)
        right_base.glue_labels[(4-i)%4] = "right_inc_0_t"+str(i)
        right_base.glue_strengths[(4-i)%4] = 2

    # use tiles from the initial base row as the left-most bits of the secondary towers
    seed_tiles = [ tile for tile in towers[0].tiles if "seed" in tile.name ]
    right_seed_tile = min(seed_tiles, key=lambda t: t.name)
    left_seed_tile  = max(seed_tiles, key=lambda t: t.name)

    left_seed_tile.glue_labels[WEST] = "left_inc_0_t1"
    left_seed_tile.glue_strengths[WEST] = 1

    for tile in seed_tiles:
        tile.glue_labels[SOUTH] = "inc_0_t2"
        tile.glue_strengths[SOUTH] = 1
    right_seed_tile.glue_labels[SOUTH] = "left_inc_0_t2"
    right_seed_tile.glue_strengths[SOUTH] = 1

    right_seed_tile.glue_labels[EAST] = "left_inc_0_t3"
    right_seed_tile.glue_strengths[EAST] = 1

    return concat_tilesets(*towers)

if __name__ == "__main__":
    spell_gamma(4).to_file("gamma_4.tds")
    busy_tiles(2).to_file("busy_tiles_2.tds")
