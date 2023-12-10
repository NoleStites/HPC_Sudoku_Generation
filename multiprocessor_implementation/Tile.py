
class Tile():
    """
    This class stores data on each individual tile in the tile grid.
    """
    def __init__(self, subsquare, tiles: int, x: int, y: int):
        self.subsquare = subsquare
        self.entropy = [ num+1 for num in range(tiles) ]    # Numbers that are allowed to go in the given Tile
        self.collapsed = False
        self.coord = [x, y]
        self.value = None
