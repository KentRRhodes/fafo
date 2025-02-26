"""
Scripts

Scripts are powerful jacks-of-all-trades. They have no in-game
existence and can be used to represent persistent game systems in some
circumstances. Scripts can also have a time component that allows them
to "fire" regularly or a limited number of times.

There is generally no "tree" of Scripts inheriting from each other.
Rather, each script tends to inherit from the base Script class and
just overloads its hooks to have it perform its function.

"""

from evennia.scripts.scripts import DefaultScript


class Script(DefaultScript):
    """
    This is the base TypeClass for all Scripts. Scripts describe
    all entities/systems without a physical existence in the game world
    that require database storage (like an economic system or
    combat tracker). They
    can also have a timer/ticker component.

    A script type is customized by redefining some or all of its hook
    methods and variables.

    * available properties (check docs for full listing, this could be
      outdated).

     key (string) - name of object
     name (string)- same as key
     aliases (list of strings) - aliases to the object. Will be saved
              to database as AliasDB entries but returned as strings.
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
     date_created (string) - time stamp of object creation
     permissions (list of strings) - list of permission strings

     desc (string)      - optional description of script, shown in listings
     obj (Object)       - optional object that this script is connected to
                          and acts on (set automatically by obj.scripts.add())
     interval (int)     - how often script should run, in seconds. <0 turns
                          off ticker
     start_delay (bool) - if the script should start repeating right away or
                          wait self.interval seconds
     repeats (int)      - how many times the script should repeat before
                          stopping. 0 means infinite repeats
     persistent (bool)  - if script should survive a server shutdown or not
     is_active (bool)   - if script is currently running

    * Handlers

     locks - lock-handler: use locks.add() to add new lock strings
     db - attribute-handler: store/retrieve database attributes on this
                        self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not
                        create a database entry when storing data

    * Helper methods

     create(key, **kwargs)
     start() - start script (this usually happens automatically at creation
               and obj.script.add() etc)
     stop()  - stop script, and delete it
     pause() - put the script on hold, until unpause() is called. If script
               is persistent, the pause state will survive a shutdown.
     unpause() - restart a previously paused script. The script will continue
                 from the paused timer (but at_start() will be called).
     time_until_next_repeat() - if a timed script (interval>0), returns time
                 until next tick

    * Hook methods (should also include self as the first argument):

     at_script_creation() - called only once, when an object of this
                            class is first created.
     is_valid() - is called to check if the script is valid to be running
                  at the current time. If is_valid() returns False, the running
                  script is stopped and removed from the game. You can use this
                  to check state changes (i.e. an script tracking some combat
                  stats at regular intervals is only valid to run while there is
                  actual combat going on).
      at_start() - Called every time the script is started, which for persistent
                  scripts is at least once every server start. Note that this is
                  unaffected by self.delay_start, which only delays the first
                  call to at_repeat().
      at_repeat() - Called every self.interval seconds. It will be called
                  immediately upon launch unless self.delay_start is True, which
                  will delay the first call of this method by self.interval
                  seconds. If self.interval==0, this method will never
                  be called.
      at_pause()
      at_stop() - Called as the script object is stopped and is about to be
                  removed from the game, e.g. because is_valid() returned False.
      at_script_delete()
      at_server_reload() - Called when server reloads. Can be used to
                  save temporary variables you want should survive a reload.
      at_server_shutdown() - called at a full server shutdown.
      at_server_start()

    """

    pass


"""
Scripts for fafo.
"""

from evennia import DefaultScript

class RoomBlockScript(DefaultScript):
    """
    Script for managing room block numbers.
    This ensures block numbers persist across server reloads/restarts.
    """
    
    def at_script_creation(self):
        """Set up initial script attributes."""
        self.key = "room_block_manager"
        self.persistent = True  # Make sure it survives server reloads
        # Initialize the next block number if not already set
        self.db.next_block = self.db.next_block if self.db.next_block is not None else 1
    
    def get_next_block(self):
        """Get and increment the next available block number."""
        current = self.db.next_block
        self.db.next_block = current + 1
        return current


class CoordMapScript(DefaultScript):
    """
    Script for managing room coordinates and providing mapping functionality.
    """
    
    def at_script_creation(self):
        """Set up initial script attributes."""
        self.key = "coord_map_manager"
        self.persistent = True
        # Initialize coordinate tracking
        self.db.rooms = {}  # Format: {room.id: (x, y, z)}
        # Track the bounds of the map
        self.db.bounds = {
            'min_x': 0, 'max_x': 0,
            'min_y': 0, 'max_y': 0,
            'min_z': 0, 'max_z': 0
        }
    
    def set_room_coords(self, room, x, y, z=0):
        """
        Set coordinates for a room and update map bounds.
        
        Args:
            room (Object): The room to set coordinates for
            x (int): X coordinate
            y (int): Y coordinate
            z (int): Z coordinate (default: 0)
        """
        # Store coordinates both in script and on room
        self.db.rooms[room.id] = (x, y, z)
        room.db.coordinates = {'x': x, 'y': y, 'z': z}
        
        # Update bounds
        self.db.bounds['min_x'] = min(self.db.bounds['min_x'], x)
        self.db.bounds['max_x'] = max(self.db.bounds['max_x'], x)
        self.db.bounds['min_y'] = min(self.db.bounds['min_y'], y)
        self.db.bounds['max_y'] = max(self.db.bounds['max_y'], y)
        self.db.bounds['min_z'] = min(self.db.bounds['min_z'], z)
        self.db.bounds['max_z'] = max(self.db.bounds['max_z'], z)
    
    def get_room_coords(self, room):
        """
        Get coordinates for a room.
        
        Args:
            room (Object): The room to get coordinates for
            
        Returns:
            tuple: (x, y, z) coordinates or None if not set
        """
        if not room or not room.id:
            return None
            
        return self.db.rooms.get(room.id)
    
    def get_room_at_coords(self, x, y, z=0):
        """
        Find a room at specific coordinates.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            z (int): Z coordinate (default: 0)
            
        Returns:
            Object or None: Room at coordinates if found
        """
        from evennia import ObjectDB
        
        for room_id, coords in self.db.rooms.items():
            if coords == (x, y, z):
                try:
                    return ObjectDB.objects.get(id=room_id)
                except ObjectDB.DoesNotExist:
                    # Room no longer exists, clean up our tracking
                    del self.db.rooms[room_id]
        return None
    
    def calculate_next_coords(self, base_room, direction):
        """
        Calculate the next coordinates in a given direction.
        
        Args:
            base_room (Object): The starting room
            direction (str): Direction to move
            
        Returns:
            tuple: (x, y, z) for new coordinates
        """
        current_coords = self.get_room_coords(base_room) or (0, 0, 0)
        x, y, z = current_coords
        
        # Direction mapping
        direction = direction.lower()
        if direction in ['north', 'n']:
            y += 1
        elif direction in ['south', 's']:
            y -= 1
        elif direction in ['east', 'e']:
            x += 1
        elif direction in ['west', 'w']:
            x -= 1
        elif direction in ['northeast', 'ne']:
            x += 1
            y += 1
        elif direction in ['northwest', 'nw']:
            x -= 1
            y += 1
        elif direction in ['southeast', 'se']:
            x += 1
            y -= 1
        elif direction in ['southwest', 'sw']:
            x -= 1
            y -= 1
        elif direction == 'up':
            z += 1
        elif direction == 'down':
            z -= 1
            
        return (x, y, z)


class RegionManagerScript(DefaultScript):
    """
    Script for managing region assignments and data.
    """
    
    def at_script_creation(self):
        """Set up initial script attributes."""
        self.key = "region_manager"
        self.persistent = True
        self.desc = "Manages region assignments and data"
        
        from world.regions.manager import RegionManager
        from world.regions import DESCRIPTIVE_PATH, SPAWNING_PATH, RESOURCE_PATH
        
        # Initialize region managers
        self.ndb.descriptive = RegionManager("descriptive", DESCRIPTIVE_PATH)
        self.ndb.spawning = RegionManager("spawning", SPAWNING_PATH)
        self.ndb.resource = RegionManager("resource", RESOURCE_PATH)
    
    def at_server_reload(self):
        """Refresh region data on server reload."""
        from world.regions.manager import RegionManager
        from world.regions import DESCRIPTIVE_PATH, SPAWNING_PATH, RESOURCE_PATH
        
        # Reinitialize region managers
        self.ndb.descriptive = RegionManager("descriptive", DESCRIPTIVE_PATH)
        self.ndb.spawning = RegionManager("spawning", SPAWNING_PATH) 
        self.ndb.resource = RegionManager("resource", RESOURCE_PATH)
    
    def at_server_start(self):
        """Initialize on server start."""
        self.at_server_reload()
    
    def add_region_to_room(self, room, region_type, region_id):
        """
        Add a region to a room.
        
        Args:
            room (Object): Room to add region to
            region_type (str): Type of region ("descriptive", "spawning", "resource")
            region_id (str): ID of region to add
        """
        manager = getattr(self.ndb, region_type, None)
        if not manager:
            raise ValueError(f"Invalid region type: {region_type}")
            
        return manager.apply_to_room(room, region_id)
    
    def remove_region_from_room(self, room, region_type, region_id=None):
        """
        Remove a region (or all regions of a type) from a room.
        
        Args:
            room (Object): Room to remove region from
            region_type (str): Type of region ("descriptive", "spawning", "resource")
            region_id (str, optional): Specific region ID to remove, or None for all of type
        """
        manager = getattr(self.ndb, region_type, None)
        if not manager:
            raise ValueError(f"Invalid region type: {region_type}")
            
        if region_id:
            # Remove specific region
            return manager.remove_from_room(room, region_id)
        else:
            # For descriptive regions, remove the single region if it exists
            if region_type == "descriptive":
                current_region = getattr(room.db, manager._get_descriptor_name(), None)
                if current_region:
                    return manager.remove_from_room(room, current_region)
            # For spawning/resource regions, remove all regions of that type
            else:
                attr_name = manager._get_descriptor_name()
                regions = getattr(room.db, attr_name, set()).copy()
                success = False
                for rid in regions:
                    if manager.remove_from_room(room, rid):
                        success = True
                return success
            return False
