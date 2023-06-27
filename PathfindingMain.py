#To do - add Z axis (this might be more complicated than it sounds when it comes to pathfinding, but for an item/mob tile check it's fine)

"""
Ultima Online Razor Enhanced Pathfinding
Author: Yulia.M
Github: https://github.com/YulesRules/Ultima-Online-Razor-Enhanced-Pathfinding

This Python script provides an implementation of the A* pathfinding algorithm for use with the Razor Enhanced client in Ultima Online. 
It allows player characters to navigate around obstacles in the game world such as items, mobiles (NPCs), player houses, and more. 

The pathfinding algorithm uses configurable filters to identify potential obstacles, 
and checks each tile along the path to determine if it is passable or not. 

The goal position for pathfinding is set interactively by the player using the in-game target prompt. 

Please refer to the README at https://github.com/YulesRules/Ultima-Online-Razor-Enhanced-Pathfinding/blob/main/README.md for detailed instructions and configuration options.

Date: June 2023

Note: This is a work in progress and may be updated or changed in future versions.
"""

# Configuration Variables
config = {
    'search_statics': True,  # look for blockable statics like trees, rocks (not blocked by sittable tree trunks) etc...
    'player_house_filter': True,  # avoid player houses - make this False if you need to use inside a large open player house room without walls
    'items_filter': {
        'Enabled': True,  # look for items which may block the tile, chests, tables (but is also stopped by objects like chairs and cups) etc...
    },
    'mobiles_filter': {
        'Enabled': True,  # look for MOBS which may block the tile (lambs, ancient dragons) etc...
    },
}

debug = False #output iteration messages, set it to False for peace and quiet!


#***************NO TOUCHING BELOW THIS LINE!!!***************
longPause = 5000
shortPause = 100


class Position:
    def __init__(self, x, y):
        self.X = x
        self.Y = y

playerStartPosition = Player.Position
goalPosition = Position(0,0)

def check_tile(tile_x, tile_y):    
    
    items_filter = Items.Filter()
    items_filter.Enabled = config['items_filter']['Enabled']

    mobiles_filter = Mobiles.Filter()
    mobiles_filter.Enabled = config['mobiles_filter']['Enabled']
    
    max_distance = 100
    is_tile_blocked = False  

    # Apply the filters to get all items and mobiles
    items = Items.ApplyFilter(items_filter)
    mobiles = Mobiles.ApplyFilter(mobiles_filter)

    def check_properties(obj, properties):
        for prop, value in properties.items():
            if isinstance(value, dict):
                if not check_properties(getattr(obj, prop, None), value):
                    return False
            else:
                if prop == 'Name':
                    if getattr(obj, prop, None) == value:
                        return False
                else:
                    if getattr(obj, prop, None) != value:
                        return False
        return True

    properties_to_check = {
        'Position': {
            'X': tile_x,
            'Y': tile_y
        },
        'OnGround': True,
        'Visible': True,
        'Name': "nodraw"  
    }

    # Check for items and mobiles on the target tile
    for item in items:
        if check_properties(item, properties_to_check):
            #Misc.SendMessage(f"{item.Name} detected on tile - is it passable?! Who knows, better play it safe!")
            is_tile_blocked = True

    for mobile in mobiles:
        if mobile.Position.X == tile_x and mobile.Position.Y == tile_y:
            #Misc.SendMessage(f"Found mobile {mobile.Name} with ID {mobile.Serial} on target tile", 33)
            is_tile_blocked = True

    if config['search_statics']:   
        flag_name = "Impassable"
        static_land = Statics.GetLandID(tile_x, tile_y, Player.Map)
        if Statics.GetLandFlag(static_land, flag_name):
            is_tile_blocked = True

        static_tile = Statics.GetStaticsTileInfo(tile_x, tile_y, Player.Map)
        if len(static_tile) > 0: 
            for i, static in enumerate(static_tile):
                #Misc.SendMessage(f"Static Info: {hex(static.StaticID)}", 33)
                #Misc.SendMessage(f"Static {i} is Impassable: {Statics.GetTileFlag(static.StaticID, flag_name)}", 33)
                if Statics.GetTileFlag(static.StaticID, flag_name):
                    is_tile_blocked = True
        #else:
            #Misc.SendMessage(f"No other static tile info detected on this tile")

    if config['player_house_filter']:
        is_blocked_by_house = Statics.CheckDeedHouse(tile_x, tile_y)
        if is_blocked_by_house:
            #Misc.SendMessage(f"Blocked by house: {is_blocked_by_house}") 
            is_tile_blocked = True

    if is_tile_blocked:
        #Misc.SendMessage(f"||The tile in front is blocked by either statics, mobiles or items with unknown impassability||")
        return False  # Tile is not passable because it's blocked
    else:
        #Misc.SendMessage(f"The tile in front is passable")
        return True  # Tile is passable because it's not blocked

# Usage:
#is_passable = check_tile(Player.Position.X + 1, Player.Position.Y)  # For one tile east
#Misc.SendMessage(f"is_passable = {is_passable}")  # Prints True if the tile is passable, False otherwise

#PATH FINDING
max_iterations = 1200
max_distance = 100


class Node:
    def __init__(self, x, y, cost=0, heur=0, prev=None):
        self.x = x
        self.y = y
        self.cost = cost
        self.heur = heur
        self.prev = prev

    def __lt__(self, other):
        return self.cost + self.heur < other.cost + other.heur

class BinaryHeap:
    def __init__(self):
        self.heap = []

    def push(self, k):
        self.heap.append(k)
        self._siftup(len(self.heap) - 1)

    def pop(self):
        if len(self.heap) == 1:
            return self.heap.pop()
        smallest = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._siftdown(0)
        return smallest

    def _siftup(self, i):
        while i > 0 and self.heap[self._parent(i)] > self.heap[i]:
            self.heap[i], self.heap[self._parent(i)] = self.heap[self._parent(i)], self.heap[i]
            i = self._parent(i)

    def _siftdown(self, i):
        smallest = i
        left, right = self._left(i), self._right(i)
        if left < len(self.heap) and self.heap[i] > self.heap[left]:
            smallest = left
        if right < len(self.heap) and self.heap[smallest] > self.heap[right]:
            smallest = right
        if smallest != i:
            self.heap[i], self.heap[smallest] = self.heap[smallest], self.heap[i]
            self._siftdown(smallest)

    def _parent(self, i):
        return (i - 1) // 2

    def _left(self, i):
        return 2 * i + 1

    def _right(self, i):
        return 2 * i + 2

def heuristic(a, b):
    return abs(b.x - a.x) + abs(b.y - a.y)

def a_star_pathfinding(playerStartPosition, goalPosition, check_tile, max_iterations=10000, max_distance=None):
    open_nodes = BinaryHeap()
    closed_nodes = set()
    path = None

    start_node = Node(playerStartPosition.X, playerStartPosition.Y)
    goal_node = Node(goalPosition.X, goalPosition.Y)

    open_nodes.push(start_node)

    Misc.SendMessage("Pathfinding started.")

    for i in range(max_iterations):
        if debug == True:
            Misc.SendMessage(f"Current iteration: {i}")
        if i == 500:
            Player.HeadMessage(42, "Difficult one...")
        if i == 800:
            Player.HeadMessage(42, "Let's see...")   
        if i == 1100:
            Player.HeadMessage(42, "Yikes, I need more time...")        
        if len(open_nodes.heap) == 0:
            Misc.SendMessage("Pathfinding failed: no valid path found.")
            return None

        current_node = open_nodes.pop()
        closed_nodes.add((current_node.x, current_node.y))

        # Check if current node is beyond max_distance
        if max_distance is not None and heuristic(start_node, current_node) > max_distance:
            Misc.SendMessage(f"Node {current_node.x}, {current_node.y} is beyond max distance. Skipping.")
            continue

        if current_node.x == goal_node.x and current_node.y == goal_node.y:
            path = []
            while current_node:
                path.append((current_node.x, current_node.y))
                current_node = current_node.prev

            Misc.SendMessage("Pathfinding completed.")
            return path[::-1]

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            next_x, next_y = current_node.x + dx, current_node.y + dy
            if dx != 0 and dy != 0:  # if moving diagonally
                # Check if the tile to the North or South (depending on dy) is passable
                if not check_tile(current_node.x, current_node.y + dy):
                    continue
                # Check if the tile to the East or West (depending on dx) is passable
                if not check_tile(current_node.x + dx, current_node.y):
                    continue
            if check_tile(next_x, next_y) and (next_x, next_y) not in closed_nodes:
                cost = current_node.cost + 0.05 if dx != 0 and dy != 0 else current_node.cost + 1
                next_node = Node(next_x, next_y, cost, heuristic(goal_node, Node(next_x, next_y)), current_node)
                open_nodes.push(next_node)

    Misc.SendMessage("Pathfinding failed: maximum iterations reached.")
    return path
    
###################CHARACTER MOVEMENT#################

def move_player_along_path(path):
    direction_map = {
    (0, 1): 'South',
    (0, -1): 'North',
    (1, 0): 'East',
    (-1, 0): 'West',
    (-1, -1): 'Up',
    (1, 1): 'Down',
    (1, -1): 'Right',
    (-1, 1): 'Left'
}
    stuckCount = 0
    stop_moving = False  # Add a stop flag

    for i in range(len(path)-1):
        if stop_moving:  # Check the stop flag at the start of every loop
            break

        current_node, next_node = path[i], path[i + 1]
        dx = next_node[0] - current_node[0]
        dy = next_node[1] - current_node[1]
        direction = direction_map.get((dx, dy))

        if direction and Player.Direction != direction:
            Player.Run(direction)
            Misc.Pause(shortPause)

        Player.Run(direction)
        Misc.Pause(shortPause)

        # Output the step
        if debug == True:
            Misc.SendMessage(f"Moving from {current_node} to {next_node} ({i} of {len(path)}")

        # Check the position after each step and wait until the movement is complete
        while (Player.Position.X, Player.Position.Y) != next_node:
            Misc.Pause(shortPause)

            # If the player hasn't moved after a certain amount of time, try moving again
            if (Player.Position.X, Player.Position.Y) == current_node:
                if debug == True:
                    Misc.SendMessage(f"Player stuck at {current_node}, trying to move again.")
                Player.Run(direction)
                Misc.Pause(shortPause)
                stuckCount += 1
                Player.HeadMessage(42, "oops...thinking..!")
                if stuckCount > 5:
                    Player.HeadMessage(42, "I give up!")
                    stop_moving = True  # Set the stop flag
                    break
            # Break the loop if the player is close enough to the goal
            elif abs(Player.Position.X - next_node[0]) <= 1 and abs(Player.Position.Y - next_node[1]) <= 1:
                break


    
    
goalPosition = Target.PromptGroundTarget("Where do you wish to pathfind?")    
if check_tile(goalPosition.X,goalPosition.Y):
    Misc.SendMessage(f"Pathfinding to: {goalPosition}")
    Player.HeadMessage(42, "Thinking...");
    path = a_star_pathfinding(Player.Position, goalPosition, check_tile, max_iterations=max_iterations)
else: 
    path = 0    
if path is not 0:
    Player.HeadMessage(42, "Here we go!");
    for node in path:
        if debug == True:
            Misc.SendMessage(f"Node in path: {node}")
    move_player_along_path(path)  # Moved outside the loop
else:
    if debug == True:
        Misc.SendMessage(f"No valid path found.")
        Player.HeadMessage(42, "I can't figure out how to get there!")
        
if path == 0:
    Player.HeadMessage(42, "That's inaccessible!")
if Player.Position == goalPosition:    
    Player.HeadMessage(42, "I have arrived!")