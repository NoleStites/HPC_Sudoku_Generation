from Tile import Tile
from Snapshot import Snapshot
from math import isqrt, floor
from random import choice
from time import perf_counter
import sys
import datetime
from multiprocessing import Pool


def askForBoardSize():
    '''
    This function will prompt the user to choose a 
    board size and return

    'tiles_for_width': number of tiles/mini squares making up the width
    'subsquares_along_width': number of larger groups of squares making up the width
    '''
    print("\nChoose your Sudoku size:")
    print("- 4x4   (enter \'4\')")
    print("- 9x9   (enter \'9\')   (STANDARD)")
    print("- 16x16 (enter \'16\')")
    print("- 25x25 (enter \'25\')")
    print("- 36x36 (enter \'36\')")
    print("- 49x49 (enter \'49\')")

    tiles_for_width = int(input("\nChoice: "))
    subsquares_along_width = isqrt(tiles_for_width)
    print()

    return tiles_for_width, subsquares_along_width


def populateGrid():
    '''
    Creates all of the Tile objects to put in the grid and initializes
    them with no value and max entropy. Returns the tile grid list.
    '''
    global tiles_for_width
    tile_grid = {} # Dictionary. Key = column num.; Value = list of Tiles in column
    prev_sub_x = 0

    for column in range(tiles_for_width):
        temp = []
        prev_sub_y = 0
        for row in range(tiles_for_width):
            # Calculate which subsquare the Tile is in
            sub_x = column // isqrt(tiles_for_width)
            sub_y = row // isqrt(tiles_for_width)
            subsquare_coord = (sub_x, sub_y)

            # Check if we have moved down to a new subsquare
            if sub_y != prev_sub_y:
                prev_sub_y = sub_y
            if sub_x != prev_sub_x:
                prev_sub_x = sub_x

            # Create the Tile object and add to list of Tiles
            new_tile = Tile(subsquare_coord, tiles_for_width, column, row) # tiles_for_width used to initialize entropy
            temp.append(new_tile)


        tile_grid[column] = temp

    return tile_grid


def generateSudoku():
    '''
    Will continually collapse tiles, backtracking when necessary,
    until the entire Sudoku board has been populated with numbers.
    ''' 
    global tiles_for_width, tile_grid

    start = True # To make the first collapsed Tile be in the center
    backtracking = False # To keep track if we choose the Tile to collapse or not
    history = []

    while True:
        """
        Choosing the tile based on if this is the first time running the method,
        if we are actively backtracking, or if we are proceeding normally.
        """
        if start: # Start with collapsing the Tile in the center
            x = tiles_for_width // 2
            y = tiles_for_width // 2
            chosen_tile = tile_grid[x][y]

        elif backtracking:
            chosen_tile = last_snapshot.collapsed_tile

        else: # Get tuple containing random Tile object to populate and value to populate with
            chosen_tile = randomTile()


        if chosen_tile == None:
            break   # No more uncollapsed Tiles, so the board is filled and the loop can end
        
        start = False

        # Choose the value to assign to the Tile based on if we are backtracking or proceeding normally.
        if backtracking:
            chosen_value = chooseRandomValue(chosen_tile, last_snapshot.collapsed_values)

        else:
            chosen_value = chooseRandomValue(chosen_tile)


        if chosen_value == None: # After exclusions, no entropy can be chosen; time to backtrack.
            # Extract the last snapshot and the coord and value
            last_snapshot = history[-1]
            history.pop(-1)
            backtrack_tile = last_snapshot.collapsed_tile
            entropy_val_to_reverse = backtrack_tile.value

            # Reset the Tile that needs to be changed
            backtrack_tile.collapsed = False
            backtrack_tile.value = None

            # Go through the Tile grid and restore the entropy from the last snapshot
            reverseEntropy(backtrack_tile, entropy_val_to_reverse)
            backtracking = True

            continue


        # Mark equivalent Tile in grid as collapsed and assign value to it
        if not(start):
            x = chosen_tile.coord[0]
            y = chosen_tile.coord[1]
        
        tile_grid[x][y].collapsed = True
        tile_grid[x][y].value = chosen_value

        # Add the new change to history
        if backtracking:
            last_snapshot.collapsed_values.append(chosen_value)
            history.append(last_snapshot)
        else:
            history.append(Snapshot(chosen_tile, chosen_value))

        backtracking = False

        # Backtrack if a tile will have zero entropy after propagation
        if searchZeroEntropyPropagation(chosen_tile, chosen_value) == 1:
            # Acquire the latest snapshot for backtracking
            last_snapshot = history[-1]
            history.pop(-1)

            # Reset the Tile that needs to be changed
            tile_grid[x][y].collapsed = False
            tile_grid[x][y].value = None

            # Start the cycle again with new exclusions for the values
            backtracking = True
            continue


        # Propagate the entropy of affected Tiles
        propagateEntropy(chosen_tile, chosen_value)


def assignProcessors():
    '''
    Assigns processors in the pool to each column of the tile_grid for
    per-column per-tile processsing.
    '''
    global tiles_for_width

    pool = Pool(tiles_for_width)
    


def propagateEntropy(tile, value):
    '''
    Will change the entropy of Tiles surrounding the given Tile based on
    the given value.
    '''
    global tiles_for_width, tile_grid

    # Iterate through every Tile in the grid
    for column in range(tiles_for_width):
        for row in range(tiles_for_width):
            curr_tile = tile_grid[column][row]
            if (curr_tile.coord[0] == tile.coord[0]) or (curr_tile.coord[1] == tile.coord[1]) or (curr_tile.subsquare == tile.subsquare):
                if curr_tile.entropy.count(value) != 0:
                    curr_tile.entropy.remove(value)


def searchZeroEntropyPropagation(tile, propagation_value):
    '''
    Given a Tile soon to be collapsed and a value to ignore, searches the board to see
    if any Tile has zero entropy. If so, return 1, else return 0.
    '''
    global tile_grid

    size = len(tile_grid)

    for column in range(size):
        for row in range(size):

            curr_tile = tile_grid[column][row]

            if (curr_tile.coord[0] == tile.coord[0]) or (curr_tile.coord[1] == tile.coord[1]) or (curr_tile.subsquare == tile.subsquare):
                if curr_tile.collapsed == False:
                    if (len(curr_tile.entropy) == 0):
                        print("This case shouldn't happen. We should be catching at length 1.")
                        raise Exception("0 Entropy.")
                        return 1
                    elif (len(curr_tile.entropy) == 1) and (curr_tile.entropy.count(propagation_value) > 0):
                        return 1
    return 0


def reverseEntropy(tile, entropy_value):
    '''
    Given a reference Tile and a value, this method will add to all
    necessary Tile's entropy lists the value of entropy_value.
    For going back in time for backtracking.
    '''
    global tile_grid

    size = len(tile_grid)

    # Acquire a list of rows, columns, and subsquares that shouldn't be reversed
    exclude_columns = []
    exclude_rows = []
    exclude_subsquares = []

    for column in range(size):
        for row in range(size):
            curr_tile = tile_grid[column][row]
            if curr_tile.value == entropy_value:
                exclude_columns.append(curr_tile.coord[0])
                exclude_rows.append(curr_tile.coord[1])
                exclude_subsquares.append(curr_tile.subsquare)

    # Reverse the entropy of Tiles not included in the constraints of the row, column, and subsquare lists
    for column in range(size):
        for row in range(size):
            curr_tile = tile_grid[column][row]
            if (curr_tile.coord[0] == tile.coord[0]) or (curr_tile.coord[1] == tile.coord[1]) or (curr_tile.subsquare == tile.subsquare):
                if (exclude_columns.count(curr_tile.coord[0]) == 0) and (exclude_rows.count(curr_tile.coord[1]) == 0) and (exclude_subsquares.count(curr_tile.subsquare) == 0):
                    if curr_tile.entropy.count(entropy_value) == 0:
                        curr_tile.entropy.append(entropy_value)


def randomTile():
    """
    Given the two-dimensional list of Tiles, determines
    which tiles are uncollapsed and have the lowest entropy.

    Returns a random Tile.
    If there are no uncollasped Tiles, return None.
    """
    global tile_grid

    # Get a list of uncollapsed Tiles with the lowest entropy to choose from
    valid_tiles = getValidTiles()
    if valid_tiles == None:
        return None

    # Choose random Tile to be returned
    tile = chooseRandomTile(valid_tiles)

    return tile


def getValidTiles():
    """
    Iterates through each Tile in the grid and determines if it
    has collapsed or not, then returns a list of uncollapsed Tiles
    with the lowest entropy; if all are collapsed, returns None.
    """
    global tiles_for_width, tile_grid

    grid_size = tiles_for_width
    
    valid_tiles = []
    lowest_entropy = grid_size

    for column in range(grid_size):
        for row in range(grid_size):
            tile = tile_grid[column][row]
            if not(tile.collapsed):
                valid_tiles.append(tile)
                # Update lowest entropy if new lowest is found
                if (len(tile.entropy) < lowest_entropy) and (len(tile.entropy) != 0):
                    lowest_entropy = len(tile.entropy)


    # Before returning the list, verify that it isn't empty
    if len(valid_tiles) == 0:
        return None

    # Only return the Tiles with entropy = lowest_entropy
    new_valid_tiles = []
    for tile in valid_tiles:
        if len(tile.entropy) == lowest_entropy:
            new_valid_tiles.append(tile)

    if len(new_valid_tiles) == 0:
        return None

    return new_valid_tiles


def chooseRandomValue(tile, exclude=[]):
    '''
    Given a Tile, will return a random value from its entropy list
    that is not included in the exclude list.

    Returns None if there are no values to choose from after the exclusions.
    '''
    # Before choosing, remove values that must be excluded
    smaller_entropy_list = tile.entropy.copy()
    for val_to_remove in exclude:
        while smaller_entropy_list.count(val_to_remove) > 0:
            smaller_entropy_list.remove(val_to_remove)

    # Verify that list isn't empty
    if len(smaller_entropy_list) == 0:
        return None

    # Choose and return a random value from the new entropy list
    random_value = choice(smaller_entropy_list)
    return random_value


def chooseRandomTile(valid_tiles):
    """
    Given a list of uncollapsed tiles, this method will choose a
    random tile.
    """
    random_tile = choice(valid_tiles)

    return random_tile


def printGeneratedSudoku(subsquare_count):
    '''
    Prints the completed sudoku board to the terminal.
    '''
    global tiles_for_width, tile_grid

    digit_count = len(str(tiles_for_width))

    # Dynamically size the printed divider based on board size
    horizontal_divider_length = subsquare_count*(((digit_count+1)*subsquare_count)+2)+1
    horizontal_divider = ""
    for i in range(horizontal_divider_length):
        horizontal_divider += "-"
    print(horizontal_divider)

    # Print the contents of the grid
    for column in range(tiles_for_width):
        string_to_print = "| "
        for row in range(tiles_for_width):
            tile = tile_grid[column][row]
            string_to_print += str(tile.value)

            # Determine paddings to make up for lower-digit numbers
            digits_in_val = len(str(tile.value))
            for j in range(digit_count - digits_in_val + 1):
                string_to_print += " "

            if tile.coord[1] % subsquare_count == (subsquare_count-1): # Last number in the subsquare
                string_to_print += "| "

        print(string_to_print)
        if column % subsquare_count == (subsquare_count-1):
            print(horizontal_divider)


def log_data(date_time, test_count, time_result_list):
    '''
    Logs the average time, longest time, and shortest time given
    the results of all tests.

    Data is logged to "results.txt"
    '''
    global tiles_for_width

    # Calculate the average, longest, and shortest times
    longest = round(max(time_result_list), 5)
    shortest = round(min(time_result_list), 5)
    
    total_sum = 0
    for result in time_result_list:
        total_sum += result
    average = round(total_sum / test_count, 5)

    # Determine size of divider
    divider = ""
    for i in range(len(str(date_time))-6):
        divider += "-"

    # Extract date and time from datetime
    date = date_time.strftime("%x")
    time = date_time.strftime("%I:%M:%S %p")

    # Open and append to log file
    open_file = open("results.txt", "a")

    open_file.write(f'{date} {time}\n')
    open_file.write(divider + "\n")
    open_file.write(f'Board Size: {tiles_for_width}x{tiles_for_width}\n')
    open_file.write(f'Test Count: {test_count}\n')
    open_file.write(f'Average:    {average} s\n')
    open_file.write(f'Longest:    {longest} s\n')
    open_file.write(f'Shortest:   {shortest} s\n\n\n')

    open_file.close()


def main():
    # Extract test count from command line
    if len(sys.argv) == 2:
        try:
            test_count = int(sys.argv[1])
        except:
            raise Exception("Second argument must be a positive non-zero integer!")
    
        if test_count <= 0:
            raise Exception("Second argument must be a positive non-zero integer!")
        number_of_tests = test_count
    else:
        number_of_tests = 1

    # Get the board size information
    global tiles_for_width
    tiles_for_width, subsquares_along_width = askForBoardSize()

    # Verify that chosen board size is valid
    if tiles_for_width not in [4, 9, 16, 25, 36, 49]:
        raise Exception("Invalid Board Size!") 
    
    # Get the current date and time for logging
    date_and_time = datetime.datetime.now()

    # Initialize a result list
    result_times = []

    # Time the generation attempt
    for n in range(number_of_tests):
        # Initialize empty grid of tiles
        global tile_grid
        tile_grid = populateGrid()
        
        start = perf_counter()
        generateSudoku()
        end = perf_counter()
        
        execution_time = end - start # Time in seconds
        result_times.append(execution_time)

        """Uncomment below to print completed Sudoku boards"""
        printGeneratedSudoku(subsquares_along_width)

    # Log the testing results in "results.txt"
    log_data(date_and_time, number_of_tests, result_times)

    # Print success
    if number_of_tests == 1:
        print(f'Successfully ran {number_of_tests} test!')
    else:
        print(f'Successfully ran {number_of_tests} tests!')

    print("Results can be found in \"results.txt\"\n")








if __name__ == "__main__":
    main()
