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

#PATH FINDING
max_iterations = 9000 #anything too high (11k-100k might crash your client ;p
max_distance = 600

debug = 1 #output messages, 1 is partial feedback and 2 is everything happening during the pathfinding, set it to 0 for peace and quiet!
maxRetryIterations = 1 #if we get stuck and give up, then try x amount of times to pathfind from the current location



#***************NO TOUCHING BELOW THIS LINE!!!***************
retryIteration = 0
longPause = 5000
shortPause = 150


class Position:
    def __init__(self, x, y):
        self.X = x
        self.Y = y

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.X == other.X and self.Y == other.Y
        else:
            return False

playerStartPosition = Player.Position
goalPosition = Position(0,0)
overrideAsPosition = Position(0,0)



if Misc.CheckSharedValue("pathFindingOverride"):
    override = Misc.ReadSharedValue("pathFindingOverride")
    overrideAsPosition = Position(override[0], override[1])
    
    
    if(goalPosition != overrideAsPosition):
        goalPosition = overrideAsPosition
        if debug > 0:
            Misc.SendMessage(f"Remote pathfinding request detected")  
            Misc.SendMessage(f"Remote pathfinding request to {override[0],override[1]}")



items_filter = Items.Filter()
items_filter.Enabled = config['items_filter']['Enabled']

mobiles_filter = Mobiles.Filter()
mobiles_filter.Enabled = config['mobiles_filter']['Enabled']

items = Items.ApplyFilter(items_filter)
mobiles = Mobiles.ApplyFilter(mobiles_filter)

def check_tile(tile_x, tile_y, items, mobiles):
    flag_name = "Impassable"

    # check if any items are on the tile
    for item in items:
        if item.Position.X == tile_x and item.Position.Y == tile_y and item.OnGround and item.Visible and item.Name != "nodraw":
            return False  # Tile is blocked by an item

    # check if any mobiles are on the tile
    for mobile in mobiles:
        if mobile.Position.X == tile_x and mobile.Position.Y == tile_y and mobile.Visible:
            return False  # Tile is blocked by a mobile

    # Check for statics and houses on the tile
    if config['search_statics']:
        static_land = Statics.GetLandID(tile_x, tile_y, Player.Map)
        if Statics.GetLandFlag(static_land, flag_name):
            return False  # Tile is blocked by a static

        static_tile = Statics.GetStaticsTileInfo(tile_x, tile_y, Player.Map)
        if len(static_tile) > 0: 
            for idx, static in enumerate(static_tile):
                if Statics.GetTileFlag(static.StaticID, flag_name):
                    return False  # Tile is blocked by a static

    if config['player_house_filter']:
        is_blocked_by_house = Statics.CheckDeedHouse(tile_x, tile_y)
        if is_blocked_by_house:
            return False  # Tile is blocked by a house

    # Tile is passable because it's not blocked
    return True

# Usage:
#is_passable = check_tile(Player.Position.X + 1, Player.Position.Y)  # For one tile east
#Misc.SendMessage(f"is_passable = {is_passable}")  # Prints True if the tile is passable, False otherwise




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
    # Apply the filters to get all items and mobiles
    items_filter = Items.Filter()
    items_filter.Enabled = config['items_filter']['Enabled']

    mobiles_filter = Mobiles.Filter()
    mobiles_filter.Enabled = config['mobiles_filter']['Enabled']

    items = Items.ApplyFilter(items_filter)
    mobiles = Mobiles.ApplyFilter(mobiles_filter)
    open_nodes = BinaryHeap()
    closed_nodes = set()
    path = None

    start_node = Node(playerStartPosition.X, playerStartPosition.Y)
    goal_node = Node(goalPosition.X, goalPosition.Y)

    open_nodes.push(start_node)
    if debug > 0:
        Misc.SendMessage("Pathfinding started.")

    for i in range(max_iterations):
        if debug > 1:
            Misc.SendMessage(f"Current iteration: {i}")
        #if i == 2000:
            #Player.HeadMessage(42, "Difficult one...")
        if i == 4000:
            Player.HeadMessage(42, "Difficult one...")   
        #if i == 6000:
            #Player.HeadMessage(42, "Yikes, I need more time...")        
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
            if debug > 0:
                Misc.SendMessage("Pathfinding completed.")
            return path[::-1]

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            next_x, next_y = current_node.x + dx, current_node.y + dy
            if dx != 0 and dy != 0:  # if moving diagonally
                # Check if the tile to the North or South (depending on dy) is passable
                if not check_tile(current_node.x, current_node.y + dy, items, mobiles):
                    continue
                # Check if the tile to the East or West (depending on dx) is passable
                if not check_tile(current_node.x + dx, current_node.y, items, mobiles):
                    continue
            if check_tile(next_x, next_y, items, mobiles) and (next_x, next_y) not in closed_nodes:
                cost = current_node.cost + 0.05 if dx != 0 and dy != 0 else current_node.cost + 1
                next_node = Node(next_x, next_y, cost, heuristic(goal_node, Node(next_x, next_y)), current_node)
                open_nodes.push(next_node)

    Misc.SendMessage("Pathfinding failed")
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
        if debug >1:
            Misc.SendMessage(f"Moving from {current_node} to {next_node} ({i} of {len(path)}")

        # Check the position after each step and wait until the movement is complete
        while (Player.Position.X, Player.Position.Y) != next_node:
            Misc.Pause(shortPause)

            # If the player hasn't moved after a certain amount of time, try moving again
            if (Player.Position.X, Player.Position.Y) == current_node:
                if debug > 1:
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



if goalPosition == Position(0,0):
    goalPosition = Target.PromptGroundTarget("Where do you wish to pathfind?")  

if check_tile(goalPosition.X,goalPosition.Y, items, mobiles):
    if debug > 0:
        Misc.SendMessage(f"Pathfinding to: {goalPosition}")
    Player.HeadMessage(42, "Thinking...");
    path = a_star_pathfinding(Player.Position, goalPosition, check_tile)
else: 
    path = 0    
if path == 0:
    Player.HeadMessage(42, "That's inaccessible!")
    if debug > 0:
        Misc.SendMessage(f"Invalid Area")
elif not path:
    Player.HeadMessage(42, "I can't figure out how to get there!")
    if debug > 0:
        Misc.SendMessage(f"No valid path found.")
        Misc.SendMessage(f"Failed after {max_iterations} attempts")
   
        
else:
    Player.HeadMessage(42, "Here we go!");
    for node in path:
        if debug > 1:
            Misc.SendMessage(f"Node in path: {node}")
    move_player_along_path(path)  # Moved outside the loop
    
    
   

if Player.Position == goalPosition:    
    Player.HeadMessage(42, "I have arrived!")  
    Misc.SendMessage(f"Movement complete")

if Misc.CheckSharedValue("pathFindingOverride"):
    Misc.SetSharedValue("pathFindingOverride", (0,0))#reset shared value to allow for normal targeting prompt

        