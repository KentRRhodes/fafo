"""
Room building commands for creating rooms and room layouts.
"""
from django.core.exceptions import ObjectDoesNotExist
from evennia import create_object, DefaultExit, search_tag
from evennia.commands.default.building import ObjManipCommand
from evennia import settings, GLOBAL_SCRIPTS
import random

def get_next_block_number():
    """Get and increment the next available block number"""
    return GLOBAL_SCRIPTS.room_block_manager.get_next_block()

def get_coord_map():
    """Get the coordinate map script"""
    return GLOBAL_SCRIPTS.coord_map_manager

def create_exit_if_none(exit_key, aliases, source, destination):
    """
    Create an exit only if one doesn't already exist with the same key or alias.
    
    Args:
        exit_key (str): The main key for the exit
        aliases (list): List of aliases for the exit
        source (Object): The location where the exit will be created
        destination (Object): Where the exit leads to
        
    Returns:
        bool: True if exit was created, False if it already existed
    """
    # Check for existing exits with same key or aliases
    existing_exits = [exit for exit in source.exits 
                     if exit.key.lower() == exit_key.lower() or
                     any(alias.lower() == exit_key.lower() for alias in exit.aliases.all())]
    
    # Also check if any of our new aliases match existing exit keys/aliases
    for alias in aliases:
        matching_exits = [exit for exit in source.exits 
                         if exit.key.lower() == alias.lower() or
                         any(existing_alias.lower() == alias.lower() 
                             for existing_alias in exit.aliases.all())]
        existing_exits.extend(matching_exits)
    
    if existing_exits:
        return False
        
    # No matching exit found, create new one
    create_object(DefaultExit, key=exit_key,
                 aliases=aliases,
                 location=source,
                 destination=destination)
    return True

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

def set_room_block(room, block_num):
    """
    Set the block number for a room using tags.
    
    Args:
        room (Object): The room to tag
        block_num (int): The block number to assign
    """
    # Remove any existing block tags
    for tag, category in room.tags.all(return_key_and_category=True):
        if category == "room_block":
            room.tags.remove(tag, category=category)
    # Add new block tag
    room.tags.add(f"room_block_{block_num}", category="room_block")

class CmdBuildRoom(ObjManipCommand):
    """
    Build a single room in a given direction or at specific coordinates.

    Usage:
      buildroom <direction>
      buildroom <x> <y> [z]

    Creates a new room either:
    1. One step in the given direction from your current location
    2. At the specific coordinates provided

    If using coordinates, z is optional and defaults to your current z-coordinate.
    The room will be connected to your current location if coordinates are adjacent.

    Example:
      buildroom north
      buildroom southwest
      buildroom 997 1000 901
      buildroom 997 1000
    """

    key = "buildroom"
    locks = "cmd:perm(build) or perm(Builder)"
    help_category = "Building"

    # Direction mappings
    dir_map = {
        "n": "north", "ne": "northeast", "e": "east", "se": "southeast",
        "s": "south", "sw": "southwest", "w": "west", "nw": "northwest"
    }
    opposites = {
        "north": "south", "northeast": "southwest",
        "east": "west", "southeast": "northwest",
        "south": "north", "southwest": "northeast",
        "west": "east", "northwest": "southeast"
    }

    def func(self):
        """Create the room."""
        caller = self.caller
        if not self.args:
            caller.msg("Usage: buildroom <direction> OR buildroom <x> <y> [z]")
            return

        if not caller.location:
            caller.msg("You must be in a room to build!")
            return

        # Get coordinate manager
        coord_map = get_coord_map()
        created_room = None  # Will store reference to created room
        
        # Parse arguments
        args = self.args.strip().split()
        
        # Check if we're dealing with coordinates
        if len(args) >= 2 and all(arg.replace("-","").isdigit() for arg in args[:2]):
            try:
                x = int(args[0])
                y = int(args[1])
                # If z is provided use it, otherwise check existing or current room's z or 0
                if len(args) > 2:
                    z = int(args[2])
                else:
                    current_coords = coord_map.get_room_coords(caller.location)
                    if not current_coords:
                        caller.msg("The coordinate system hasn't been initialized! Use initcoords first.")
                        return
                    z = current_coords[2]
                
                new_coords = (x, y, z)
                
                # Check if room exists at these coordinates
                existing_room = coord_map.get_room_at_coords(x, y, z)
                if (existing_room):
                    caller.msg(f"There is already a room ({existing_room.key}) at those coordinates!")
                    return
                
                # Create room at specified coordinates
                roomtype = settings.BASE_ROOM_TYPECLASS
                room = create_object(roomtype, key="placeholder")
                room.key = f"Room{room.id}"
                coord_map.set_room_coords(room, x, y, z)
                created_room = room
                
                # Check if new room is adjacent to current room
                current_coords = coord_map.get_room_coords(caller.location)
                if current_coords and are_coords_adjacent(current_coords, new_coords):
                    # Find the direction that connects these rooms
                    direction = None
                    for dir_name, opposite in self.dir_map.items():
                        test_coords = coord_map.calculate_next_coords(caller.location, dir_name)
                        if test_coords == new_coords:
                            direction = dir_name
                            break
                    
                    if direction:
                        # Create connecting exits
                        aliases = []
                        if direction != self.dir_map.get(direction):  # if short form
                            aliases.append(self.dir_map.get(direction))
                            
                        if create_exit_if_none(direction, aliases, caller.location, room):
                            back_dir = self.opposites[self.dir_map.get(direction)]
                            back_aliases = []
                            back_short = {v: k for k, v in self.dir_map.items()}.get(back_dir)
                            if back_short:
                                back_aliases.append(back_short)
                            
                            create_exit_if_none(back_dir, back_aliases, room, caller.location)
                
                caller.msg(f"Created room {room.key} at coordinates ({x}, {y}, {z})")
                
            except ValueError:
                caller.msg("Coordinates must be valid integers.")
                return

        else:  # Direction-based mode
            direction = args[0].lower()
            valid_directions = ["north", "northeast", "east", "southeast", 
                              "south", "southwest", "west", "northwest",
                              "n", "ne", "e", "se", "s", "sw", "w", "nw"]
            
            if direction not in valid_directions:
                caller.msg(f"Invalid direction or coordinates. Use either a direction ({', '.join(valid_directions)}) or x y [z] coordinates.")
                return

            # Get coordinate manager
            coord_map = get_coord_map()
            
            # Check if current room has coordinates
            current_coords = coord_map.get_room_coords(caller.location)
            if not current_coords:
                caller.msg("The current room has no coordinates set! Use initcoords first.")
                return
            
            # Calculate coordinates for new room
            new_coords = coord_map.calculate_next_coords(caller.location, direction)
            if not new_coords:
                caller.msg(f"Could not calculate valid coordinates in direction {direction}.")
                return

            # Check if room already exists at these coordinates
            existing_room = coord_map.get_room_at_coords(*new_coords)
            if existing_room:
                caller.msg(f"There is already a room ({existing_room.key}) at those coordinates!")
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
            room = create_object(roomtype, key="placeholder")  # Temporary key
            room.key = f"Room{room.id}"  # Set final key using room's ID
            
            # Set room coordinates
            coord_map.set_room_coords(room, *new_coords)
            
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
            
            created_room = room  # Store reference for later move
            caller.msg(f"Created room {room.key} to the {full_direction}.")
        
        # Move caller to the new room at the end
        if created_room and created_room.pk:  # Verify room exists in database
            caller.move_to(created_room, quiet=True)
            caller.msg(f"You have been moved to {created_room.key}.")
        elif created_room:
            caller.msg("Warning: Could not move to new room - room creation may have failed.")

class CmdBuildGrid(ObjManipCommand):
    """
    Build a grid of rooms in given dimensions.

    Usage:
      buildgrid <direction> <number> <direction2> <number2> [connect]

    Creates a grid of rooms extending in two directions. If 'connect' is specified,
    automatically creates exits to any existing adjacent rooms outside the grid.

    Example:
      buildgrid west 4 north 3
      buildgrid south 2 east 5 connect
    """

    key = "buildgrid"
    locks = "cmd:perm(build) or perm(Builder)"
    help_category = "Building"

    def func(self):
        """Create the grid of rooms."""
        caller = self.caller
        if not self.args:
            caller.msg("Usage: buildgrid <direction> <number> <direction2> <number2> [connect]")
            return

        args = self.args.split()
        if len(args) < 4:
            caller.msg("Usage: buildgrid <direction> <number> <direction2> <number2> [connect]")
            return

        dir1, num1, dir2, num2 = args[:4]
        force_connections = "connect" in args[4:] if len(args) > 4 else False

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

        # Get coordinate manager
        coord_map = get_coord_map()

        # Convert directions and get block number
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
        
        # Calculate base coordinates for grid
        base_coords = coord_map.get_room_coords(caller.location) or (0, 0, 0)
        
        # Create first row
        start_room = caller.location
        prev_room = start_room
        first_row = [start_room]
        current_coords = list(base_coords)  # Convert to list for easy modification
        
        # Set coordinates for starting room if not already set
        if not coord_map.get_room_coords(start_room):
            coord_map.set_room_coords(start_room, *current_coords)

        def connect_to_adjacent(room, new_coords):
            """Helper to connect room to any adjacent existing rooms"""
            # Get all rooms from coord_map
            for room_id, coords in coord_map.db.rooms.items():
                if coords == new_coords or room_id == room.id:
                    continue
                    
                # Check if this room is adjacent
                if are_coords_adjacent(new_coords, coords):
                    existing_room = coord_map.get_room_at_coords(*coords)
                    if not existing_room or existing_room.id == room.id:
                        continue
                        
                    # Find the direction that connects these rooms
                    for direction, opposite in opposites.items():
                        test_coords = coord_map.calculate_next_coords(existing_room, direction)
                        if test_coords == new_coords:
                            # Found the correct direction
                            dir_aliases = []
                            dir_short = alias_map.get(direction)
                            if dir_short:
                                dir_aliases.append(dir_short)
                                
                            if create_exit_if_none(direction, dir_aliases, existing_room, room):
                                # Create return exit
                                back_aliases = []
                                back_short = alias_map.get(opposite)
                                if back_short:
                                    back_aliases.append(back_short)
                                    
                                create_exit_if_none(opposite, back_aliases, room, existing_room)

        for i in range(num1):
            # Calculate next coordinates in first direction
            next_coords = list(coord_map.calculate_next_coords(prev_room, dir1))
            
            # Check if room exists at these coordinates
            existing_room = coord_map.get_room_at_coords(*next_coords)
            if existing_room:
                caller.msg(f"Cannot build grid - room {existing_room.key} already exists at coordinates ({next_coords[0]}, {next_coords[1]}, {next_coords[2]})")
                return

            new_room = create_object(settings.BASE_ROOM_TYPECLASS, 
                                   key="placeholder")
            new_room.key = f"Block {block_num} Room{new_room.id}"
            set_room_block(new_room, block_num)  # Use tag instead of attribute
            
            # Set coordinates
            coord_map.set_room_coords(new_room, *next_coords)
            
            if force_connections:
                connect_to_adjacent(new_room, next_coords)
            
            # Create exits with appropriate aliases
            dir1_aliases = []
            if dir1 != dir1_full:  # if we used short form, add long form
                dir1_aliases.append(dir1_full)
            elif dir1 in alias_map:  # if we used long form, add short form
                dir1_aliases.append(alias_map[dir1])
                
            if create_exit_if_none(dir1, dir1_aliases, prev_room, new_room):
                # Only create return exit if forward exit was created
                back_dir = opposites[dir1_full]
                back_aliases = []
                back_short = alias_map.get(back_dir)
                if back_short:
                    back_aliases.append(back_short)
                    
                create_exit_if_none(back_dir, back_aliases, new_room, prev_room)

            first_row.append(new_room)
            prev_room = new_room
            current_coords = next_coords

        # Create additional rows
        for j in range(num2):
            prev_row = first_row
            new_row = []
            
            for i, base_room in enumerate(prev_row):
                # Calculate next coordinates in second direction
                next_coords = list(coord_map.calculate_next_coords(base_room, dir2))
                
                # Check if room exists at these coordinates
                existing_room = coord_map.get_room_at_coords(*next_coords)
                if existing_room:
                    caller.msg(f"Cannot complete grid - room {existing_room.key} already exists at coordinates ({next_coords[0]}, {next_coords[1]}, {next_coords[2]})")
                    return

                new_room = create_object(settings.BASE_ROOM_TYPECLASS,
                                       key="placeholder")
                new_room.key = f"Block {block_num} Room{new_room.id}"
                set_room_block(new_room, block_num)  # Use tag instead of attribute
                
                # Set coordinates
                coord_map.set_room_coords(new_room, *next_coords)
                
                if force_connections:
                    connect_to_adjacent(new_room, next_coords)
                
                # Link to room above/below with both forms as aliases
                dir2_aliases = []
                if dir2 != dir2_full:  # if we used short form, add long form
                    dir2_aliases.append(dir2_full)
                elif dir2 in alias_map:  # if we used long form, add short form
                    dir2_aliases.append(alias_map[dir2])
                    
                if create_exit_if_none(dir2, dir2_aliases, base_room, new_room):
                    # Only create return exit if forward exit was created
                    back_dir = opposites[dir2_full]
                    back_aliases = []
                    back_short = alias_map.get(back_dir)
                    if back_short:
                        back_aliases.append(back_short)
                        
                    create_exit_if_none(back_dir, back_aliases, new_room, base_room)
                
                # Link to previous room in row if it exists
                if new_row:
                    # Create forward exit with aliases
                    dir1_aliases = []
                    if dir1 != dir1_full:  # if we used short form, add long form
                        dir1_aliases.append(dir1_full)
                    elif dir1 in alias_map:  # if we used long form, add short form
                        dir1_aliases.append(alias_map[dir1])
                    
                    if create_exit_if_none(dir1, dir1_aliases, new_row[-1], new_room):
                        # Only create return exit if forward exit was created
                        back_dir = opposites[dir1_full]
                        back_aliases = []
                        back_short = alias_map.get(back_dir)
                        if back_short:
                            back_aliases.append(back_short)
                        
                        create_exit_if_none(back_dir, back_aliases, new_room, new_row[-1])
                
                new_row.append(new_room)
            
            first_row = new_row

        caller.msg(f"Created a grid {num1}x{num2} rooms extending {dir1} and {dir2} (block #{block_num}).")

class CmdBuildMaze(ObjManipCommand):
    """
    Build a randomly connected maze of rooms.

    Usage:
      buildmaze <direction> <number> [connect]

    Creates a collection of randomly connected rooms. If 'connect' is specified,
    automatically creates exits to any existing adjacent rooms outside the maze.

    Example:
      buildmaze north 10
      buildmaze west 5 connect
    """

    key = "buildmaze"
    locks = "cmd:perm(build) or perm(Builder)"
    help_category = "Building"

    # Direction mappings as class attributes
    dir_map = {
        "n": "north", "ne": "northeast", "e": "east", "se": "southeast",
        "s": "south", "sw": "southwest", "w": "west", "nw": "northwest"
    }
    opposites = {
        "north": "south", "northeast": "southwest",
        "east": "west", "southeast": "northwest",
        "south": "north", "southwest": "northeast",
        "west": "east", "northwest": "southeast"
    }

    def get_valid_direction(self, source_room, existing_rooms):
        """
        Find a valid direction that doesn't collide with existing rooms.
        
        Args:
            source_room (Object): Room to branch from
            existing_rooms (list): List of already created rooms
            
        Returns:
            tuple: (direction, coordinates) or (None, None) if no valid direction found
        """
        coord_map = get_coord_map()
        source_coords = coord_map.get_room_coords(source_room)
        if not source_coords:
            return None, None
            
        directions = list(self.opposites.keys())
        random.shuffle(directions)
        
        for direction in directions:
            new_coords = coord_map.calculate_next_coords(source_room, direction)
            # Check if space is free and coords are adjacent
            if not coord_map.get_room_at_coords(*new_coords) and \
               are_coords_adjacent(source_coords, new_coords):
                return direction, new_coords
        return None, None

    def connect_to_adjacent_rooms(self, room, exclude_rooms=None):
        """
        Connect a room to all adjacent existing rooms.
        
        Args:
            room (Object): Room to connect from
            exclude_rooms (list): Rooms to exclude from connections
        """
        coord_map = get_coord_map()
        room_coords = coord_map.get_room_coords(room)
        if not room_coords:
            return
            
        exclude_rooms = exclude_rooms or []
        
        # Get all rooms from coord_map
        for room_id, coords in coord_map.db.rooms.items():
            if room_id == room.id or room_id in [r.id for r in exclude_rooms]:
                continue
                
            # Check if this room is adjacent
            if are_coords_adjacent(room_coords, coords):
                existing_room = coord_map.get_room_at_coords(*coords)
                if not existing_room or existing_room.id == room.id:
                    continue
                    
                # Find the direction that connects these rooms
                for direction, opposite in self.opposites.items():
                    test_coords = coord_map.calculate_next_coords(existing_room, direction)
                    if test_coords == room_coords:
                        # Found the correct direction
                        dir_aliases = []
                        dir_short = self.dir_map.get(direction)
                        if dir_short:
                            dir_aliases.append(dir_short)
                            
                        if create_exit_if_none(direction, dir_aliases, existing_room, room):
                            # Create return exit
                            back_aliases = []
                            back_short = self.dir_map.get(opposite)
                            if back_short:
                                back_aliases.append(back_short)
                                
                            create_exit_if_none(opposite, back_aliases, room, existing_room)
                        break

    def func(self):
        """Create the maze of rooms."""
        import random
        
        caller = self.caller
        if not self.args:
            caller.msg("Usage: buildmaze <direction> <number> [connect]")
            return

        args = self.args.split()
        if len(args) < 2:
            caller.msg("Usage: buildmaze <direction> <number> [connect]")
            return

        direction, number = args[:2]
        force_connections = "connect" in args[2:] if len(args) > 2 else False
        
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

        # Get coordinate manager
        coord_map = get_coord_map()

        # Get full direction name for messages
        full_direction = self.dir_map.get(direction, direction)
        
        # Calculate coordinates for first room
        first_coords = coord_map.calculate_next_coords(caller.location, direction)
        
        # Check if room already exists at first position
        if coord_map.get_room_at_coords(*first_coords):
            caller.msg(f"Cannot start maze - a room already exists in that direction!")
            return

        # Direction mappings setup
        alias_map = {v: k for k, v in self.dir_map.items()}  # reverse mapping

        # Get block number for this maze
        block_num = get_next_block_number()

        # Create rooms
        rooms = [caller.location]
        created_rooms = []  # Track rooms we create (not including start room)

        # Create and place first room
        new_room = create_object(settings.BASE_ROOM_TYPECLASS,
                               key="placeholder")
        new_room.key = f"Block {block_num} Room{new_room.id}"
        set_room_block(new_room, block_num)  # Tag handles block number
        
        # Set coordinates for first room
        coord_map.set_room_coords(new_room, *first_coords)
        
        # Create initial connection with specified direction
        aliases = []
        if direction != full_direction:  # if we used short form, add long form
            aliases.append(full_direction)
        elif direction in alias_map:  # if we used long form, add short form
            aliases.append(alias_map[direction])
            
        if create_exit_if_none(direction, aliases, caller.location, new_room):
            # Only create return exit if forward exit was created
            back_dir = self.opposites[full_direction]
            back_aliases = []
            back_short = alias_map.get(back_dir)
            if back_short:
                back_aliases.append(back_short)
                
            create_exit_if_none(back_dir, back_aliases, new_room, caller.location)
        
        if force_connections:
            self.connect_to_adjacent_rooms(new_room, exclude_rooms=[caller.location])
        
        rooms.append(new_room)
        created_rooms.append(new_room)

        # Create remaining rooms
        for i in range(number - 1):
            # Create the room first
            new_room = create_object(settings.BASE_ROOM_TYPECLASS,
                                   key="placeholder")
            new_room.key = f"Block {block_num} Room{new_room.id}"
            set_room_block(new_room, block_num)  # Tag handles block number
            
            # Try to find a valid position for this room
            placed = False
            for attempt in range(10):  # Try up to 10 different source rooms
                source = random.choice(created_rooms)
                rand_dir, new_coords = self.get_valid_direction(source, created_rooms)
                
                if rand_dir:
                    # Found a valid position
                    coord_map.set_room_coords(new_room, *new_coords)
                    
                    if force_connections:
                        self.connect_to_adjacent_rooms(new_room, exclude_rooms=created_rooms + [caller.location])
                    
                    # Create exits between rooms
                    rand_aliases = []
                    rand_short = alias_map.get(rand_dir)
                    if rand_short:
                        rand_aliases.append(rand_short)
                        
                    if create_exit_if_none(rand_dir, rand_aliases, source, new_room):
                        # Only create return exit if forward exit was created
                        back_dir = self.opposites[rand_dir]
                        back_aliases = []
                        back_short = alias_map.get(back_dir)
                        if back_short:
                            back_aliases.append(back_short)
                            
                        create_exit_if_none(back_dir, back_aliases, new_room, source)
                    
                    placed = True
                    break
            
            if not placed:
                caller.msg("Could not find a valid position for more rooms. Maze generation stopped.")
                break
            
            created_rooms.append(new_room)
            rooms.append(new_room)

            # 30% chance for additional connection, but only if we can find a valid direction
            if i > 0 and random.random() < 0.3:
                # Try to connect to nearby rooms
                for other_room in random.sample(created_rooms[:-1], min(3, len(created_rooms[:-1]))):
                    if other_room != source:
                        # Check if rooms are adjacent before attempting connection
                        other_coords = coord_map.get_room_coords(other_room)
                        new_coords = coord_map.get_room_coords(new_room)
                        
                        if are_coords_adjacent(other_coords, new_coords):
                            # Find the direction that connects these rooms
                            for direction, opposite in self.opposites.items():
                                test_coords = coord_map.calculate_next_coords(other_room, direction)
                                if test_coords == new_coords:
                                    # Found the correct direction
                                    rand_aliases = []
                                    rand_short = alias_map.get(direction)
                                    if rand_short:
                                        rand_aliases.append(rand_short)
                                        
                                    if create_exit_if_none(direction, rand_aliases, other_room, new_room):
                                        # Create return exit
                                        back_aliases = []
                                        back_short = alias_map.get(opposite)
                                        if back_short:
                                            back_aliases.append(back_short)
                                            
                                        create_exit_if_none(opposite, back_aliases, new_room, other_room)
                                    break
                            break

        caller.msg(f"Created a maze of {len(created_rooms)} rooms starting {full_direction} (block #{block_num}).")

class CmdInitCoords(ObjManipCommand):
    """
    Initialize the coordinate system by setting the current room as the origin point.

    Usage:
      initcoords

    Sets the current room's coordinates to (1000,1000,1000), establishing it as
    a central point from which all other room coordinates will be calculated.
    This should typically only be run once, on the first room of your game.
    """

    key = "initcoords"
    locks = "cmd:perm(build) or perm(Builder)"
    help_category = "Building"

    def func(self):
        """Set up the coordinate origin point."""
        caller = self.caller
        
        if not caller.location:
            caller.msg("You must be in a room to initialize coordinates!")
            return

        # Get coordinate manager
        coord_map = get_coord_map()
        
        # Check if this room already has coordinates
        current_coords = coord_map.get_room_coords(caller.location)
        if current_coords:
            caller.msg(f"This room already has coordinates: ({current_coords[0]}, {current_coords[1]}, {current_coords[2]})")
            return
            
        # Set the origin point
        coord_map.set_room_coords(caller.location, 1000, 1000, 1000)
        caller.msg("Room coordinates initialized to (1000, 1000, 1000)")

class CmdCheckCoords(ObjManipCommand):
    """
    Check coordinates of current room and validity of its exits.

    Usage:
      checkcoords

    Shows the current room's coordinates and verifies that all exits
    connect to rooms that are exactly one coordinate step away.
    """

    key = "checkcoords"
    locks = "cmd:perm(build) or perm(Builder)"
    help_category = "Building"

    def func(self):
        """Check the room's coordinates and exits."""
        caller = self.caller
        room = caller.location
        
        if not room:
            caller.msg("You must be in a room to check coordinates!")
            return

        coord_map = get_coord_map()
        coords = coord_map.get_room_coords(room)
        
        if not coords:
            caller.msg("This room has no coordinates set.")
            return
            
        x, y, z = coords
        caller.msg(f"Room: {room.key}")
        caller.msg(f"Coordinates: ({x}, {y}, {z})")
        
        # Check each exit
        for exit in room.exits:
            if not exit.destination:
                caller.msg(f"Exit '{exit.key}' has no destination!")
                continue
                
            dest_coords = coord_map.get_room_coords(exit.destination)
            if not dest_coords:
                caller.msg(f"Exit '{exit.key}' leads to room with no coordinates.")
                continue
                
            dx, dy, dz = dest_coords
            if are_coords_adjacent(coords, dest_coords):
                caller.msg(f"Exit '{exit.key}' -> ({dx}, {dy}, {dz}) [Valid]")
            else:
                caller.msg(f"Exit '{exit.key}' -> ({dx}, {dy}, {dz}) [INVALID: non-adjacent]")

class CmdDeleteBlock(ObjManipCommand):
    """
    Delete all rooms in a specified block.

    Usage:
      deleteblock <block number> [/force]

    Deletes all rooms assigned to the specified block number.
    Also cleans up any exits leading to the deleted rooms.
    Use this command with caution as it cannot be undone.

    Switches:
      /force - Skip confirmation for large block deletions

    Example:
      deleteblock 5
      deleteblock 12/force
    """

    key = "deleteblock"
    locks = "cmd:perm(build) or perm(Builder)"
    help_category = "Building"
    switch_options = ("force",)

    def func(self):
        """Delete all rooms in the block."""
        caller = self.caller
        
        if not self.args:
            caller.msg("Usage: deleteblock <block number>")
            return
            
        try:
            block_num = int(self.args.strip())
        except ValueError:
            caller.msg("Block number must be an integer.")
            return
            
        # Find all rooms with this block number using evennia's search_tag
        from evennia import search_tag
        from evennia.objects.models import ObjectDB
        tag_key = f"room_block_{block_num}"
        rooms = search_tag(tag_key, category="room_block")
        
        if not rooms:
            caller.msg(f"No rooms found in block {block_num}.")
            return
            
        room_count = len(rooms)
        
        # Check if player is in one of the rooms to be deleted
        if caller.location and any(room.id == caller.location.id for room in rooms):
            caller.msg("You cannot delete the block you are currently in!")
            return
            
        # Ask for confirmation if deleting more than 10 rooms and /force not used
        if room_count > 10 and "force" not in self.switches:
            caller.msg(f"Warning: This will delete {room_count} rooms and all their exits.")
            caller.msg("Use 'deleteblock <number>/force' to skip this warning.")
            return
            
        coord_map = get_coord_map()
        room_ids = set(room.id for room in rooms)
        
        # First pass - collect all exits and validate rooms still exist
        valid_rooms = []
        exits_to_delete = set()
        
        # Find all exits connected to any of these rooms
        exits = ObjectDB.objects.filter(db_typeclass_path__contains="exits.Exit").exclude(db_destination__isnull=True)
        
        for room in rooms:
            try:
                # Check if room still exists
                if not room.pk:
                    continue
                valid_rooms.append(room)
                
                # Get exits in this room leading anywhere
                exits_to_delete.update(exit for exit in room.exits if exit.pk)
                
                # Find exits from any room that lead to this room
                exits_to_delete.update(
                    exit for exit in exits 
                    if exit.pk and exit.destination 
                    and exit.destination.id == room.id
                )
                
            except ObjectDoesNotExist:
                continue
        
        # Delete exits first
        exit_count = 0
        for exit in exits_to_delete:
            try:
                if exit.pk and exit.id:  # Double check exit still exists
                    exit.delete()
                    exit_count += 1
            except (ObjectDoesNotExist, AttributeError):
                continue
            
        # Then delete rooms and clean up coordinate tracking
        rooms_deleted = 0
        for room in valid_rooms:
            try:
                if room.pk and room.id:  # Double check room still exists
                    # Remove from coordinate tracking
                    if room.id in coord_map.db.rooms:
                        del coord_map.db.rooms[room.id]
                    # Delete the room
                    room.delete()
                    rooms_deleted += 1
            except (ObjectDoesNotExist, AttributeError):
                continue
            
        caller.msg(f"Deleted block {block_num}: {rooms_deleted} rooms and {exit_count} exits removed.")

class CmdAddRegion(ObjManipCommand):
    """
    Add a region to a room or block of rooms.

    Usage:
      addregion <type> [#|region_id] [block #]
      addregion/list <type>
      addregion/remove <type> [region_id]

    Arguments:
        type - Type of region (descriptive, spawning, resource)
        #|region_id - Region number from list or ID (e.g. "1" or "dark_forest")
        block # - Optional block number to apply region to all rooms in that block
        region_id - ID of specific region to remove (if omitting, removes all of type)

    Switches:
        list - Show available regions of the specified type
        remove - Remove region(s) instead of adding
        force - Skip confirmation for large block operations

    Examples:
        addregion/list descriptive     - List all available descriptive regions
        addregion descriptive 1        - Add first listed descriptive region
        addregion descriptive dark_forest  - Add specific region by ID
        addregion spawning 2 5         - Add second spawning region to block 5
        addregion/remove resource      - Remove all resource regions from current room
    """

    key = "addregion"
    locks = "cmd:perm(build) or perm(Builder)"
    help_category = "Building"
    
    def func(self):
        """Implement the command"""
        caller = self.caller
        region_types = ["descriptive", "spawning", "resource"]

        if not self.args:
            caller.msg("Usage: addregion <type> [#|region_id] [block #]")
            caller.msg(f"Valid types: {', '.join(region_types)}")
            return

        args = self.args.strip().split()
        if not args:
            return

        region_type = args[0].lower()
        if region_type not in region_types:
            caller.msg(f"Invalid region type. Must be one of: {', '.join(region_types)}")
            return

        # Get region manager script
        region_manager = GLOBAL_SCRIPTS.region_manager
        if not region_manager:
            caller.msg("Error: Region manager not found!")
            return

        # Get correct region handler based on type
        region_handler = getattr(region_manager.ndb, region_type, None)
        if not region_handler:
            caller.msg(f"Error: No handler found for {region_type} regions!")
            return

        # Handle list switch
        if "list" in self.switches:
            regions = region_handler.list_regions()
            if not regions:
                caller.msg(f"No {region_type} regions defined.")
                return

            # Get details for each region with numbered index
            table = self.styled_table("#", "ID", "Name", "Description")
            for i, region_id in enumerate(regions, 1):
                region_data = region_handler.get_region(region_id)
                if region_data:
                    name = region_data.get('name', region_id)
                    desc = region_data.get('description', '').split('\n')[0][:40]  # First line, truncated
                    table.add_row(str(i), region_id, name, desc)
            
            caller.msg(f"\n{region_type.title()} Regions:")
            caller.msg(table)
            caller.msg("\nUse region number or ID when adding a region.")
            return

        # Handle remove switch
        if "remove" in self.switches:
            # Get specific region ID if provided
            region_id = args[1] if len(args) > 1 else None
            
            # Determine target rooms
            if len(args) > 1 and args[1].isdigit():  # If block number provided
                block_num = int(args[1])
                from evennia import search_tag
                rooms = search_tag(f"room_block_{block_num}", category="room_block")
                if not rooms:
                    caller.msg(f"No rooms found in block {block_num}.")
                    return
                target_rooms = rooms
            else:  # Current room only
                if not caller.location:
                    caller.msg("You must be in a room!")
                    return
                target_rooms = [caller.location]

            # Remove region(s)
            for room in target_rooms:
                result = region_manager.remove_region_from_room(room, region_type, region_id)
                if result and len(target_rooms) == 1:
                    msg = f"Removed {region_type} region"
                    msg += f" '{region_id}'" if region_id else "s"
                    msg += f" from {room.get_display_name(caller)}"
                    caller.msg(msg)

            if len(target_rooms) > 1:
                caller.msg(f"Removed {region_type} region(s) from {len(target_rooms)} rooms in block {block_num}.")
            return

        # Normal add region mode
        if len(args) < 2:  # Need to show available regions and prompt for choice
            regions = region_handler.list_regions()
            if not regions:
                caller.msg(f"No {region_type} regions defined.")
                return

            # Show available regions and prompt with numbers
            table = self.styled_table("#", "ID", "Name", "Description")
            for i, region_id in enumerate(regions, 1):
                region_data = region_handler.get_region(region_id)
                if region_data:
                    name = region_data.get('name', region_id)
                    desc = region_data.get('description', '').split('\n')[0][:40]
                    table.add_row(str(i), region_id, name, desc)
            
            caller.msg(f"\nAvailable {region_type.title()} Regions:")
            caller.msg(table)
            caller.msg("\nUsage: addregion <type> <#|region_id> [block #]")
            return

        # Process region addition
        region_id = args[1]
        regions = region_handler.list_regions()
        
        # Handle numeric selection
        if region_id.isdigit():
            try:
                index = int(region_id) - 1
                if 0 <= index < len(regions):
                    region_id = regions[index]
                else:
                    caller.msg(f"Invalid region number. Choose 1-{len(regions)}.")
                    return
            except (ValueError, IndexError):
                caller.msg(f"Invalid region number. Choose 1-{len(regions)}.")
                return
        
        # Check if region exists
        if not region_handler.get_region(region_id):
            caller.msg(f"Region '{region_id}' not found!")
            return

        # Handle block specification
        if len(args) > 2 and args[2].isdigit():
            block_num = int(args[2])
            from evennia import search_tag
            rooms = search_tag(f"room_block_{block_num}", category="room_block")
            if not rooms:
                caller.msg(f"No rooms found in block {block_num}.")
                return
            
            # Verify action for multiple rooms
            if len(rooms) > 10 and "force" not in self.switches:
                caller.msg(f"This will add the {region_type} region '{region_id}' to {len(rooms)} rooms.")
                caller.msg("Use /force switch to skip this warning.")
                return
                
            success_count = 0
            for room in rooms:
                try:
                    if region_manager.add_region_to_room(room, region_type, region_id):
                        success_count += 1
                except Exception as e:
                    caller.msg(f"Error adding region to {room.get_display_name(caller)}: {str(e)}")
            
            caller.msg(f"Added {region_type} region '{region_id}' to {success_count} rooms in block {block_num}.")
            
        else:  # Single room mode
            if not caller.location:
                caller.msg("You must be in a room!")
                return
                
            try:
                if region_manager.add_region_to_room(caller.location, region_type, region_id):
                    caller.msg(f"Added {region_type} region '{region_id}' to {caller.location.get_display_name(caller)}.")
                else:
                    caller.msg("Failed to add region.")
            except Exception as e:
                caller.msg(f"Error: {str(e)}")