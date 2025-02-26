"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""

from evennia.objects.objects import DefaultExit
from .objects import ObjectParent
from evennia import GLOBAL_SCRIPTS

def are_coords_adjacent(coord1, coord2):
    """
    Check if two sets of coordinates are exactly one step apart.
    
    Args:
        coord1 (tuple): (x, y, z) coordinates of first position
        coord2 (tuple): (x, y, z) coordinates of second position
        
    Returns:
        bool: True if coordinates are exactly one step apart
    """
    x1, y1, z1 = coord1
    x2, y2, z2 = coord2
    
    # Check if coordinates differ by at most 1 in each dimension
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    dz = abs(z2 - z1)
    
    # Valid if exactly one step in one or two directions (for diagonals)
    # and no change in z (we don't do up/down in the maze)
    if dz != 0:
        return False
        
    if dx > 1 or dy > 1:
        return False
        
    # For cardinal directions: one coord differs by 1, other by 0
    if (dx == 1 and dy == 0) or (dx == 0 and dy == 1):
        return True
        
    # For diagonal directions: both coords differ by 1
    if dx == 1 and dy == 1:
        return True
        
    return False

class Exit(ObjectParent, DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they defines the `destination` property and overrides some hooks
    and methods to represent the exits.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects child classes like this.

    """

    def at_object_creation(self):
        """Called when exit is first created"""
        super().at_object_creation()
        # Add any custom exit setup here

    def at_traverse(self, traversing_object, target_location):
        """
        Called when someone is traversing this exit.
        
        Args:
            traversing_object (Object): Object traversing us
            target_location (Object): Where target is going
            
        Returns:
            bool: True if traverse is allowed
        """
        # Check coordinate adjacency if both rooms have coordinates
        coord_map = GLOBAL_SCRIPTS.coord_map_manager
        source_coords = coord_map.get_room_coords(self.location)
        dest_coords = coord_map.get_room_coords(target_location)
        
        if source_coords and dest_coords:
            if not are_coords_adjacent(source_coords, dest_coords):
                if traversing_object.is_superuser:
                    traversing_object.msg("Warning: This exit connects non-adjacent rooms!")
                else:
                    traversing_object.msg("You cannot traverse this exit - rooms are not adjacent!")
                    return False
        
        # If we get here, either coords are valid or rooms don't have coordinates
        return super().at_traverse(traversing_object, target_location)

    def at_post_traverse(self, traversing_object, source_location):
        """Called after an object has successfully traversed."""
        super().at_post_traverse(traversing_object, source_location)
