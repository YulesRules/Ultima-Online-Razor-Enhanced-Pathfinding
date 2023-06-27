#Pathfinding Script for Razor Enhanced Client in Ultima Online

This script provides plug and play pathfinding functionality for the game ['Ultima Online'](https://en.wikipedia.org/wiki/Ultima_Online "'Ultima Online'") using the Razor Enhanced client. The script is written in Python and uses an A* algorithm to find a path for the player character from the current location to a target destination.

I needed a solution to automate some behaviours and the existing API seemed to be made redundant by client changes. This is also my foray into Python, best way to learn I guess :p


https://github.com/YulesRules/Ultima-Online-Razor-Enhanced-Pathfinding/assets/110333307/3e90ca0a-361b-4221-a63f-eb053c829564


###Script Configuration
The script is configurable with the following settings:

debug (default is True):  If set to True, will output the iteration attempts at finding a path and the progress of the character as it moves along the route, node by node. 

search_statics (default is True): If set to True, the pathfinder will avoid static objects like trees and rocks.

player_house_filter (default is True): If set to True, the pathfinder will avoid player houses. Set this to False if you wish the pathfinder to operate inside an open player house room without walls.

items_filter (default is {'Enabled': True}): If the 'Enabled' field is set to True, the pathfinder will avoid items that may block the path such as chests, tables etc.

mobiles_filter (default is {'Enabled': True}): If the 'Enabled' field is set to True, the pathfinder will avoid mobiles (e.g., non-static entities like NPCs or animals) that may block the path.

##Usage
To start using the script, target the destination point by clicking on the desired location in the game. A prompt will appear asking "Where do you wish to pathfind?"

After selecting the target location, the script will attempt to find a valid path from the player character's current position to the selected location.

The script will output messages as the player character starts moving along the computed path, providing updates on the current iteration, position, and actions.

If the script encounters an obstacle it can't bypass, it will output an error message and attempt to move again. If the script fails to progress after several attempts, it will stop pathfinding.

When the player character reaches the target location, the script will output a message stating "I have arrived!"

Please note that the check_tile() function is used to determine whether a tile in the game is passable. It checks for static objects, items, and mobiles, using the configuration settings to determine what to avoid. The function returns True if a tile is passable, and False otherwise.

##Limitations
Currently, the script does not support pathfinding in the Z (vertical) direction. Adding support for Z axis is listed as a future task. For now, the pathfinder operates only in the X and Y (horizontal) directions.

Player housing is an issue, by default the script is set to avoid houses altogether though it will work inside a house provided there are no walls to navigate. It will move the character around any items on the floor like tables and furniture, though this also applies to entities you'd typically be able to navigate past. :(  - I can't figure out how to surface the data without making the script needlessly complicated. As is, it's designed to be plug and play.

Also, note that the pathfinding script can only operate within a certain maximum distance (max_distance) and a maximum number of iterations (max_iterations). If the destination is too far, or if finding a path requires more iterations than the maximum allowed, the script may fail to find a path.

##Troubleshooting
If the script fails to find a path, try adjusting the script's configuration settings or select a destination closer to the player character's current position. If the script fails to move the character along a path, ensure that there are no obstacles blocking the path that the script isn't configured to avoid.

Avoid making changes below the line saying "NO TOUCHING BELOW THIS LINE!!!" unless you know what you're doing!
