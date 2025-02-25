"""
Room building commands for creating rooms and room layouts.
"""
from evennia import create_object, DefaultExit
from evennia.commands.default.building import ObjManipCommand
from evennia import settings, GLOBAL_SCRIPTS

def get_next_block_number():
    """Get and increment the next available block number"""
    return GLOBAL_SCRIPTS.room_block_manager.get_next_block()

class CmdBuildRoom(ObjManipCommand):
    """
    Build a single room in a given direction.

    Usage:
      buildroom <direction>

    Creates a new room one step in the given direction and links
    it with an exit from your current location. Also creates a
    return exit from the new room.

    Example:
      buildroom north
      buildroom southwest
    """

    key = "buildroom"
    locks = "cmd:perm(build) or perm(Builder)"
    help_category = "Building"

    def func(self):
        """Create the room."""
        caller = self.caller
        if not self.args:
            caller.msg("Usage: buildroom <direction>")
            return

        direction = self.args.strip().lower()
        valid_directions = ["north", "northeast", "east", "southeast", 
                          "south", "southwest", "west", "northwest",
                          "n", "ne", "e", "se", "s", "sw", "w", "nw"]
        
        if direction not in valid_directions:
            caller.msg(f"Invalid direction. Use one of: {', '.join(valid_directions)}")
            return

        # Get full name for short directions
        direction_map = {"n": "north", "ne": "northeast", "e": "east", "se": "southeast",
                        "s": "south", "sw": "southwest", "w": "west", "nw": "northwest"}
        alias_map = {v: k for k, v in direction_map.items()}  # reverse mapping
        full_direction = direction_map.get(direction, direction)
        
        # Get the opposite direction
        opposites = {"north": "south", "northeast": "southwest", "east": "west", 
                    "southeast": "northwest", "south": "north", "southwest": "northeast",
                    "west": "east", "northwest": "southeast"}
        back_direction = opposites[full_direction]

        # Create room
        roomtype = settings.BASE_ROOM_TYPECLASS
        room = create_object(roomtype, key=f"{direction.title()} Room")
        
        # Create forward exit with both forms as aliases
        aliases = []
        if direction != full_direction:  # if we used short form, add long form
            aliases.append(full_direction)
        elif direction in alias_map:  # if we used long form, add short form
            aliases.append(alias_map[direction])
            
        create_object(DefaultExit, key=direction,
                     aliases=aliases,
                     location=caller.location,
                     destination=room)
        
        # Create return exit with both forms as aliases
        back_aliases = []
        back_short = alias_map.get(back_direction)
        if back_short:  # always add short form for return direction
            back_aliases.append(back_short)
            
        create_object(DefaultExit, key=back_direction,
                     aliases=back_aliases,
                     location=room,
                     destination=caller.location)
        
        caller.msg(f"Created room {room.key} to the {full_direction}.")

class CmdBuildGrid(ObjManipCommand):
    """
    Build a grid of rooms in given dimensions.

    Usage:
      buildgrid <direction> <number> <direction2> <number2>

    Creates a grid of rooms extending in two directions.
    The first room is created in direction1, then the grid 
    expands in direction2. All rooms in the grid share the
    same block number for future reference.

    Example:
      buildgrid west 4 north 3
      buildgrid south 2 east 5
    """

    key = "buildgrid"
    locks = "cmd:perm(build) or perm(Builder)"
    help_category = "Building"

    def func(self):
        """Create the grid of rooms."""
        caller = self.caller
        if not self.args or len(self.args.split()) != 4:
            caller.msg("Usage: buildgrid <direction> <number> <direction2> <number2>")
            return

        dir1, num1, dir2, num2 = self.args.split()
        
        try:
            num1 = int(num1)
            num2 = int(num2)
            if num1 < 1 or num2 < 1:
                raise ValueError
        except ValueError:
            caller.msg("The number of rooms must be positive integers.")
            return

        valid_directions = ["north", "east", "south", "west", 
                          "n", "e", "s", "w"]
        dir1 = dir1.lower()
        dir2 = dir2.lower()
        
        if dir1 not in valid_directions or dir2 not in valid_directions:
            caller.msg(f"Invalid direction. Use one of: {', '.join(valid_directions)}")
            return

        # Convert short directions to full names and get aliases
        dir_map = {
            "n": "north", 
            "e": "east", 
            "s": "south", 
            "w": "west"
        }
        alias_map = {v: k for k, v in dir_map.items()}  # reverse mapping
        dir1_full = dir_map.get(dir1, dir1)
        dir2_full = dir_map.get(dir2, dir2)

        if dir1 == dir2:
            caller.msg("The two directions must be different.")
            return

        # Get opposite directions and their aliases
        opposites = {
            "north": "south",
            "east": "west",
            "south": "north",
            "west": "east"
        }
        
        # Get block number for this grid
        block_num = get_next_block_number()
        
        # Create first row
        start_room = caller.location
        prev_room = start_room
        first_row = [start_room]
        
        for i in range(num1):
            new_room = create_object(settings.BASE_ROOM_TYPECLASS, 
                                   key=f"Grid Room ({i+1},0)")
            # Set block number
            new_room.db.room_block = block_num
            
            # Link rooms with both forms as aliases
            dir1_aliases = []
            if dir1 != dir1_full:  # if we used short form, add long form
                dir1_aliases.append(dir1_full)
            elif dir1 in alias_map:  # if we used long form, add short form
                dir1_aliases.append(alias_map[dir1])
                
            create_object(DefaultExit, key=dir1,
                        aliases=dir1_aliases,
                        location=prev_room,
                        destination=new_room)
                        
            # Create return exit with both forms
            back_dir = opposites[dir1_full]
            back_aliases = []
            back_short = alias_map.get(back_dir)
            if back_short:
                back_aliases.append(back_short)
                
            create_object(DefaultExit, key=back_dir,
                        aliases=back_aliases,
                        location=new_room,
                        destination=prev_room)
            
            first_row.append(new_room)
            prev_room = new_room

        # Create additional rows
        for j in range(num2):
            prev_row = first_row
            new_row = []
            
            for i, base_room in enumerate(prev_row):
                new_room = create_object(settings.BASE_ROOM_TYPECLASS,
                                       key=f"Grid Room ({i},{j+1})")
                # Set block number
                new_room.db.room_block = block_num
                
                # Link to room above/below with both forms as aliases
                dir2_aliases = []
                if dir2 != dir2_full:  # if we used short form, add long form
                    dir2_aliases.append(dir2_full)
                elif dir2 in alias_map:  # if we used long form, add short form
                    dir2_aliases.append(alias_map[dir2])
                    
                create_object(DefaultExit, key=dir2,
                            aliases=dir2_aliases,
                            location=base_room,
                            destination=new_room)
                            
                # Create return exit with both forms
                back_dir = opposites[dir2_full]
                back_aliases = []
                back_short = alias_map.get(back_dir)
                if back_short:
                    back_aliases.append(back_short)
                    
                create_object(DefaultExit, key=back_dir,
                            aliases=back_aliases,
                            location=new_room,
                            destination=base_room)
                
                # Link to previous room in row if it exists
                if new_row:
                    # Create forward exit with aliases
                    dir1_aliases = []
                    if dir1 != dir1_full:  # if we used short form, add long form
                        dir1_aliases.append(dir1_full)
                    elif dir1 in alias_map:  # if we used long form, add short form
                        dir1_aliases.append(alias_map[dir1])
                    
                    create_object(DefaultExit, key=dir1,
                                aliases=dir1_aliases,
                                location=new_row[-1],
                                destination=new_room)
                                
                    # Create return exit with aliases
                    back_dir = opposites[dir1_full]
                    back_aliases = []
                    back_short = alias_map.get(back_dir)
                    if back_short:
                        back_aliases.append(back_short)
                    
                    create_object(DefaultExit, key=back_dir,
                                aliases=back_aliases,
                                location=new_room,
                                destination=new_row[-1])
                
                new_row.append(new_room)
            
            first_row = new_row

        caller.msg(f"Created a grid {num1}x{num2} rooms extending {dir1} and {dir2} (block #{block_num}).")

class CmdBuildMaze(ObjManipCommand):
    """
    Build a randomly connected maze of rooms.

    Usage:
      buildmaze <direction> <number>

    Creates a collection of randomly connected rooms in the given
    direction. The first room connects to your current location.
    All rooms in the maze share the same block number.

    Example:
      buildmaze north 10
      buildmaze west 5
    """

    key = "buildmaze"
    locks = "cmd:perm(build) or perm(Builder)"
    help_category = "Building"

    def func(self):
        """Create the maze of rooms."""
        import random
        
        caller = self.caller
        if not self.args or len(self.args.split()) != 2:
            caller.msg("Usage: buildmaze <direction> <number>")
            return

        direction, number = self.args.split()
        
        try:
            number = int(number)
            if number < 1:
                raise ValueError
        except ValueError:
            caller.msg("The number of rooms must be a positive integer.")
            return

        valid_directions = ["north", "northeast", "east", "southeast", 
                          "south", "southwest", "west", "northwest",
                          "n", "ne", "e", "se", "s", "sw", "w", "nw"]
        direction = direction.lower()
        
        if direction not in valid_directions:
            caller.msg(f"Invalid direction. Use one of: {', '.join(valid_directions)}")
            return

        # Convert short directions to full names and get aliases
        dir_map = {
            "n": "north", "ne": "northeast", "e": "east", "se": "southeast",
            "s": "south", "sw": "southwest", "w": "west", "nw": "northwest"
        }
        alias_map = {v: k for k, v in dir_map.items()}  # reverse mapping
        full_direction = dir_map.get(direction, direction)

        # Get opposite directions
        opposites = {
            "north": "south", "northeast": "southwest",
            "east": "west", "southeast": "northwest",
            "south": "north", "southwest": "northeast",
            "west": "east", "northwest": "southeast"
        }

        # Get block number for this maze
        block_num = get_next_block_number()

        # Create rooms
        rooms = [caller.location]
        for i in range(number):
            new_room = create_object(settings.BASE_ROOM_TYPECLASS,
                                   key=f"Maze Room {i+1}")
            # Set block number
            new_room.db.room_block = block_num
            
            rooms.append(new_room)

            # Always connect to at least one previous room
            if i == 0:
                # First room connects to starting location
                source = caller.location
            else:
                # Randomly select a previous room to connect from
                source = random.choice(rooms[:-1])
            
            # Create exits between rooms
            if source == caller.location:
                # Use specified direction for first room with both forms as aliases
                aliases = []
                if direction != full_direction:  # if we used short form, add long form
                    aliases.append(full_direction)
                elif direction in alias_map:  # if we used long form, add short form
                    aliases.append(alias_map[direction])
                    
                create_object(DefaultExit, key=direction,
                            aliases=aliases,
                            location=source,
                            destination=new_room)
                            
                # Create return exit with both forms
                back_dir = opposites[full_direction]
                back_aliases = []
                back_short = alias_map.get(back_dir)
                if back_short:
                    back_aliases.append(back_short)
                    
                create_object(DefaultExit, key=back_dir,
                            aliases=back_aliases,
                            location=new_room,
                            destination=source)
            else:
                # Random direction for other connections
                rand_dir = random.choice(list(opposites.keys()))
                rand_aliases = []
                rand_short = alias_map.get(rand_dir)
                if rand_short:
                    rand_aliases.append(rand_short)
                    
                create_object(DefaultExit, key=rand_dir,
                            aliases=rand_aliases,
                            location=source,
                            destination=new_room)
                            
                # Create return exit with both forms
                back_dir = opposites[rand_dir]
                back_aliases = []
                back_short = alias_map.get(back_dir)
                if back_short:
                    back_aliases.append(back_short)
                    
                create_object(DefaultExit, key=back_dir,
                            aliases=back_aliases,
                            location=new_room,
                            destination=source)

            # 30% chance to create an additional connection
            if i > 0 and random.random() < 0.3:
                other_room = random.choice(rooms[:-1])
                if other_room != source:
                    rand_dir = random.choice(list(opposites.keys()))
                    rand_aliases = []
                    rand_short = alias_map.get(rand_dir)
                    if rand_short:
                        rand_aliases.append(rand_short)
                        
                    create_object(DefaultExit, key=rand_dir,
                                aliases=rand_aliases,
                                location=other_room,
                                destination=new_room)
                                
                    # Create return exit with both forms
                    back_dir = opposites[rand_dir]
                    back_aliases = []
                    back_short = alias_map.get(back_dir)
                    if back_short:
                        back_aliases.append(back_short)
                        
                    create_object(DefaultExit, key=back_dir,
                                aliases=back_aliases,
                                location=new_room,
                                destination=other_room)

        caller.msg(f"Created a maze of {number} rooms starting {direction} (block #{block_num}).")