class Snapshot():
    '''
    Defines everything stored inside a snapshot.
    To be used when backtracking.
    '''
    def __init__(self, tile, attempted_value):
        self.collapsed_tile = tile                  # The Tile that was collapsed
        self.collapsed_values  = [attempted_value]  # A list of values that have been tried for this Tile
