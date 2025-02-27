"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""
import json
import os
import random
from evennia.objects.objects import DefaultExit
from evennia.utils import lazy_property
from django.utils import timezone
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
    Base exit class with common functionality for all exit types.
    Handles basic coordinate validation but no visibility/degradation.
    """
    
    def at_traverse(self, traversing_object, target_location, **kwargs):
        """
        Called when an object traverses this exit.
        
        Args:
            traversing_object (Object): Object traversing the exit.
            target_location (Object): Where exit leads to.
            **kwargs: Additional keywords passed from the command.
            
        Returns:
            bool: If traverse should be performed or not.
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
        
        return super().at_traverse(traversing_object, target_location, **kwargs)

    def at_post_traverse(self, traversing_object, source_location):
        """Called after an object has successfully traversed."""
        super().at_post_traverse(traversing_object, source_location)


class StaticExit(Exit):
    """
    A basic exit that is always visible and doesn't change.
    Useful for permanent connections like doors between buildings
    or static dungeon entrances.
    """
    
    def at_object_creation(self):
        """
        Called when exit is first created.
        """
        super().at_object_creation()
        self.db.hidden = False  # Static exits are always visible


class DegradingExit(Exit):
    """
    An exit that changes its appearance based on usage and can become hidden
    over time. The exit name includes directional indicators that reflect
    how well-traveled the path is.
    """
    
    @lazy_property
    def exit_settings(self):
        """Load exit settings from JSON file."""
        settings_path = os.path.join('world', 'exits.json')
        try:
            with open(settings_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "degradation_rate": 1,
                "wear_levels": {
                    "0": {"patterns": ["a faint trail to the {direction}"]}
                }
            }

    def at_object_creation(self):
        """Called when exit is first created."""
        super().at_object_creation()
        
        # Initialize attributes
        self.db.hidden = True  # Exits start hidden
        self.db.traverse_count = 0  # Track number of traversals
        self.db.last_traverse = timezone.now()  # For degradation tracking
        self.db.base_name = self.key  # Store original direction name
        
        # Set initial exit name
        self.update_wear_level()

    def update_wear_level(self):
        """Update the exit's display name based on current traverse count."""
        count = self.db.traverse_count
        direction = self.db.base_name
        wear_levels = self.exit_settings['wear_levels']
        
        # Find the highest threshold that's less than or equal to current count
        current_level = "0"
        for threshold in sorted(map(int, wear_levels.keys())):
            if count >= threshold:
                current_level = str(threshold)
            else:
                break
                
        # Get patterns for current wear level
        level_data = wear_levels[current_level]
        patterns = level_data['patterns']
        
        # Randomly select a pattern and format with direction
        self.key = random.choice(patterns).format(direction=direction)

    def update_degradation(self):
        """Calculate and apply degradation based on time since last traverse."""
        if not self.db.last_traverse:
            return
            
        now = timezone.now()
        hours_passed = (now - self.db.last_traverse).total_seconds() / 3600
        degradation = int(hours_passed * self.exit_settings['degradation_rate'])
        
        if degradation > 0:
            self.db.traverse_count = max(0, self.db.traverse_count - degradation)
            self.db.last_traverse = now
            
            # If count reaches 0, hide the exit again
            if self.db.traverse_count == 0:
                self.db.hidden = True
                
            self.update_wear_level()

    def at_traverse(self, traversing_object, target_location, **kwargs):
        """Called when an object traverses this exit."""
        # First check coordinate adjacency
        if not super().at_traverse(traversing_object, target_location, **kwargs):
            return False
            
        # Update degradation before incrementing count
        self.update_degradation()
        
        # Increment traverse count and update timestamp
        self.db.traverse_count += 1
        self.db.last_traverse = timezone.now()
        self.db.hidden = False  # Exit becomes visible after use
        
        # Update exit name based on new count
        self.update_wear_level()
        
        return True

    def return_appearance(self, looker, **kwargs):
        """This formats a description for the exit."""
        if self.db.hidden:
            return ""
            
        return super().return_appearance(looker, **kwargs)
