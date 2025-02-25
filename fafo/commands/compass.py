"""
Compass direction commands for navigation.
"""
from evennia.commands.default.building import ObjManipCommand

class CompassCommand(ObjManipCommand):
    """Base class for compass direction navigation commands."""
    locks = "cmd:all()"  # Allow all players to use compass commands
    help_category = "Navigation"

    def move_character(self, direction):
        """Common movement code"""
        caller = self.caller
        if not caller.location:
            caller.msg("You have no location to move from!")
            return

        exits = [exit for exit in caller.location.exits 
                if exit.key.lower() == direction.lower()]
        
        if not exits:
            caller.msg(f"You cannot go {direction}.")
            return
            
        # Move through the first matching exit
        exits[0].at_traverse(caller)

class CmdNorth(CompassCommand):
    """
    Move north.
    Usage: n OR north
    """
    key = "north"
    aliases = ("n")
    
    def func(self):
        self.move_character("north")

class CmdSouth(CompassCommand):
    """
    Move south.
    Usage: s OR south
    """
    key = "south"
    aliases = ["s"]
    
    def func(self):
        self.move_character("south")

class CmdEast(CompassCommand):
    """
    Move east.
    Usage: e OR east
    """
    key = "east"
    aliases = ("e")
    
    def func(self):
        self.move_character("east")

class CmdWest(CompassCommand):
    """
    Move west.
    Usage: w OR west
    """
    key = "west"
    aliases = ("w")
    
    def func(self):
        self.move_character("west")

class CmdNortheast(CompassCommand):
    """
    Move northeast.
    Usage: ne OR northeast
    """
    key = "northeast"
    aliases = ["ne"]
    
    def func(self):
        self.move_character("northeast")

class CmdNorthwest(CompassCommand):
    """
    Move northwest.
    Usage: nw OR northwest
    """
    key = "northwest"
    aliases = ["nw"]
    
    def func(self):
        self.move_character("northwest")

class CmdSoutheast(CompassCommand):
    """
    Move southeast.
    Usage: se OR southeast
    """
    key = "southeast"
    aliases = ["se"]
    
    def func(self):
        self.move_character("southeast")

class CmdSouthwest(CompassCommand):
    """
    Move southwest.
    Usage: sw OR southwest
    """
    key = "southwest"
    aliases = ["sw"]
    
    def func(self):
        self.move_character("southwest")