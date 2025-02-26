# Room Building and Navigation Commands Documentation

## Overview
This document describes two main command systems:
1. Room building commands for world creation
2. Navigation commands for moving between rooms

## Command Sets

### BuilderCmdSet
Builder-only commands for world creation, requiring the "build" or "Builder" permission:
- `initcoords` - Sets up coordinate system by initializing current room at (1000,1000,1000)
- `checkcoords` - Displays current room coordinates and validates exit connections
- `deleteblock` - Deletes all rooms and exits in a specified block number
- `buildroom` - Creates a single room with connecting exits
- `buildgrid` - Creates a structured grid of connected rooms
- `buildmaze` - Creates a randomly connected maze of rooms

### CompassCmdSet
Navigation commands available to all players for moving between rooms:
- `north` (`n`) - Move through any north exit
- `south` (`s`) - Move through any south exit
- `east` (`e`) - Move through any east exit
- `west` (`w`) - Move through any west exit
- `northeast` (`ne`) - Move through any northeast exit
- `northwest` (`nw`) - Move through any northwest exit
- `southeast` (`se`) - Move through any southeast exit
- `southwest` (`sw`) - Move through any southwest exit

## Coordinate System Setup

### Initial Setup
Before creating rooms with coordinates, you must initialize the coordinate system:

1. Go to your starting room (usually #2)
2. Run the `initcoords` command
3. This sets the room as (1000,1000,1000), giving plenty of space in all directions
4. All other rooms will be positioned relative to this origin point

### Coordinate Validation
Use the `checkcoords` command to:
- View current room's coordinates
- Verify all exits connect to adjacent rooms
- Check for invalid exit connections
- Debug coordinate-based navigation issues

### Valid Coordinate Relationships
- Cardinal moves (N,S,E,W): One coordinate differs by 1, other stays same
- Diagonal moves (NE,NW,SE,SW): Both coordinates differ by 1
- Z-coordinate changes not currently supported
- No direct movement between non-adjacent coordinates

## Room Block Management

### RoomBlockScript
Persistent script that maintains room block numbering across server restarts.

**Class Location:** `typeclasses/scripts.py`

**Attributes:**
- `next_block`: Database attribute storing the next available block number

**Methods:**
- `at_script_creation()`: Sets up initial script configuration and block counter
- `get_next_block()`: Returns current block number and increments counter

## Building Commands

### CmdInitCoords
Initialize the coordinate system by setting the current room as the origin point.

**Usage:**
```
initcoords
```

**Features:**
- Sets current room coordinates to (1000,1000,1000)
- Creates a central origin point for the coordinate system
- Should be run once at game setup
- Prevents multiple initializations of the same room
- Must be run before using coordinate-based building commands

### CmdBuildRoom
Creates a single room using either direction-based or coordinate-based placement.

**Usage:**
```
buildroom <direction>       # Direction-based placement
buildroom <x> <y> [z]      # Coordinate-based placement
```

**Direction Mode:**
- Creates room one step away in specified direction
- Automatically creates bidirectional exits
- Uses current room's coordinates as reference
- Verifies space is available before creation
- Both long ("north") and short ("n") forms supported

**Coordinate Mode:**
- Places room at exact coordinates
- Optional z coordinate (uses current room's z if omitted)
- Creates exits if new room is adjacent to current room
- Prevents creation at occupied coordinates
- Supports negative coordinates

**Exit Features:**
- Creates bidirectional exits when appropriate
- Supports both full names and abbreviations
- Prevents duplicate exit creation
- Validates coordinate adjacency
- Automatic alias management for both directions

**Movement:**
- Builder automatically moved to new room after creation
- Success: "You have been moved to Room{id}"
- Failure warning if movement unsuccessful
- Prevents creation without valid coordinates

**Safety Checks:**
- Requires builder permissions
- Validates current location exists
- Checks coordinate system initialization
- Prevents room overlap
- Verifies exit creation success

**Example Usage:**
```
buildroom n          # Create room north and move there
buildroom southeast  # Create room southeast and move there
buildroom 997 1000   # Create at coordinates and move there
buildroom 997 1000 901  # Create at exact xyz and move there
```

### CmdBuildGrid
Creates a rectangular grid of interconnected rooms.

**Usage:**
```
buildgrid <direction1> <number1> <direction2> <number2> [connect]
```

**Options:**
- connect: Creates exits to any valid adjacent rooms outside the grid

**Room Naming:**
- Each room is named "Block {block} Room{id}"
  - {block} is the unique block number assigned to this grid
  - {id} is the room's unique database ID

**Valid Directions:**
- Cardinal directions only: north/n, south/s, east/e, west/w
- Each direction accepts both full name and abbreviation

**Room Naming:**
- Rooms named using coordinate system: "Grid Room (x,y)"
- x coordinate increases in first direction
- y coordinate increases in second direction

**Exit System:**
- All exits work with both full names and abbreviations
- Each room connects to neighbors in both directions, unless an exit already exists
- Duplicate exits are prevented:
  - Checks both exit keys and aliases before creation
  - If an exit already exists in a direction, no new exit is created
  - Return exits only created if forward exit was successfully created
- All exits support both full names and abbreviations

**Grid Features:**
- Coordinates used to ensure proper room spacing
- Each room placed at calculated grid position
- Internal coordinate tracking prevents overlaps
- Grid integrity maintained through coordinate system

**Connection Features:**
- By default, only creates connections within the grid
- With 'connect' option:
  - Checks for adjacent existing rooms outside the grid
  - Creates exits to all valid adjacent rooms
  - Both forward and return exits are created
  - Maintains coordinate adjacency rules
  - Prevents duplicate exits

**Coordinate Rules:**
- All rooms placed at calculated grid positions
- Coordinates increment by 1 in each direction
- Prevents creation if any coordinate position is occupied
- All exits must connect adjacent coordinates
- Optional connections to external rooms follow same rules

### CmdBuildMaze
Creates a collection of randomly connected rooms.

**Usage:**
```
buildmaze <direction> <number> [connect]
```

**Options:**
- connect: Creates exits to any valid adjacent rooms outside the maze

**Room Naming:**
- Each room is named "Block {block} Room{id}"
  - {block} is the unique block number assigned to this maze
  - {id} is the room's unique database ID

**Valid Directions:**
- All compass directions supported
- Both full names and abbreviations accepted

**Room and Exit Features:**
- Rooms named using block and database ID format
- First room connects to starting point in specified direction
- Each subsequent room connects to at least one previous room
- Random direction selection for connections after first room
- Duplicate exits are prevented:
  - Checks for existing exits before creating new ones
  - For random connections, tries up to 3 different directions
  - If no valid exit direction found, skips that connection
- Each successful forward exit creates corresponding return exit
- All exits support both full names and abbreviations
- 30% chance for additional random connections between rooms
  - Additional connections also check for existing exits
  - Will attempt multiple random directions if first choice has existing exit

**Maze Features:**
- Random connections based on available coordinates
- Room placement validated against coordinate system
- No room overlap due to coordinate checking
- Complex mazes with guaranteed valid paths
- Exits only connect rooms that are exactly one step apart:
  - Cardinal directions: one coordinate differs by 1, other by 0
  - Diagonal directions: both coordinates differ by 1
  - Vertical connections not allowed (z coordinate must match)
  - Cannot create exits between non-adjacent rooms
- Additional random connections follow same adjacency rules
- Coordinate system ensures realistic room connections

**Connection Features:**
- Standard mode only connects rooms within the maze
- With 'connect' option:
  - Each new room checks for adjacent existing rooms
  - Creates exits to all valid adjacent rooms
  - Both forward and return exits are created
  - Maintains coordinate adjacency rules
  - Prevents duplicate exits
  - Excludes connections to rooms within the same maze

**Room Placement Rules:**
- First room placed at calculated coordinates from start point
- Subsequent rooms only placed at valid adjacent coordinates
- Up to 10 attempts to find valid position for each room
- Generation stops if no valid positions found
- Random connections only between adjacent coordinates

**Exit Creation Rules:**
- All exits must connect adjacent coordinates
- Validates coordinate adjacency before creating exits
- Prevents duplicate exit creation
- Supports both full names and abbreviations
- Optional connections to external rooms follow same rules

### CmdDeleteBlock
Delete all rooms and their connected exits in a specified block.

**Usage:**
```
deleteblock <block number> [/force]
```

**Safety Features:**
- Cannot delete block containing your current location
- Confirmation prompt for deleting more than 10 rooms
- Use /force switch to skip confirmation
- Handles already deleted exits gracefully
- Validates room existence before deletion
- Cleans up orphaned exits and coordinates

**Features:**
- Deletes all rooms in the specified block number
- Removes all exits connected to deleted rooms
- Updates coordinate tracking system
- Reports number of rooms and exits removed
- Requires builder permissions
- Cannot be undone - use with caution

**Example:**
```
deleteblock 5      # Deletes block #5 (with confirmation if >10 rooms)
deleteblock 7/force  # Delete block 7 without confirmation
```

### CmdAddRegion
Add a region to a room or block of rooms.

**Usage:**
```
addregion <type> [#|region_id] [block #]
addregion/list <type>
addregion/remove <type> [region_id]
```

**Arguments:**
- type - Type of region (descriptive, spawning, resource)
- #|region_id - Region number from list or ID (e.g. "1" or "dark_forest")
- block # - Optional block number to apply region to all rooms in that block
- region_id - ID of specific region to remove (if omitting, removes all of type)

**Switches:**
- /list - Show available regions of the specified type
- /remove - Remove region(s) instead of adding
- /force - Skip confirmation for large block operations

**Example Usage:**
```
addregion/list descriptive     # List numbered descriptive regions
addregion descriptive 1        # Add first listed descriptive region
addregion descriptive dark_forest  # Add specific region by ID
addregion spawning 2 5        # Add second spawning region to block 5
addregion/remove resource     # Remove all resource regions from current room
```

**List Format:**
The /list switch now displays regions in a numbered table:
```
# | ID           | Name         | Description
--+-------------+-------------+------------
1 | dark_forest | Dark Forest | Ancient trees loom overhead...
2 | desert_waste| Desert      | An endless expanse of sand...
```

Numbers can be used instead of IDs for easier region selection.

## Navigation System

### CompassCommand
Base class for all movement commands.

**Class Location:** `commands/compass.py`

**Methods:**
- `move_character(direction)`: Core movement logic
  - Checks if character has a current location
  - Searches for matching exit by name (case-insensitive)
  - Moves character through exit if found
  - Provides appropriate feedback messages

### Navigation Commands
All navigation commands extend CompassCommand and follow the pattern:
```python
CmdNorth(CompassCommand):      # Matches both 'north' and 'n'
CmdSouth(CompassCommand):      # Matches both 'south' and 's'
CmdEast(CompassCommand):       # Matches both 'east' and 'e'
CmdWest(CompassCommand):       # Matches both 'west' and 'w'
CmdNortheast(CompassCommand):  # Matches both 'northeast' and 'ne'
CmdNorthwest(CompassCommand):  # Matches both 'northwest' and 'nw'
CmdSoutheast(CompassCommand):  # Matches both 'southeast' and 'se'
CmdSouthwest(CompassCommand):  # Matches both 'southwest' and 'sw'
```

**Command Features:**
- Available to all characters (no special permissions required)
- Case-insensitive matching of exit names
- Works with both full names and abbreviations
- Provides clear feedback on successful movement or failure

## Usage Examples

### Navigation
```
n           # Move through north exit (same as 'north')
southeast   # Move through southeast exit (same as 'se')
W           # Move through west exit (same as 'west', case-insensitive)
```

### Room Building
```
# Create single rooms
buildroom n     # Creates room to the north (same as 'buildroom north')
buildroom sw    # Creates room to the southwest (same as 'buildroom southwest')

# Create grids (cardinal directions only)
buildgrid w 4 n 3   # 4x3 grid extending west then north
buildgrid s 2 e 5   # 2x5 grid extending south then east

# Create mazes (any compass direction)
buildmaze n 10      # 10-room maze starting northward
buildmaze west 5    # 5-room maze starting westward
```

## Room Block System
The block system organizes rooms created by buildgrid and buildmaze into logical groups.

**Features:**
- Each grid/maze gets unique block number
- Block numbers persist across server restarts
- Block number stored using room tags (category: "room_block")
- Managed by RoomBlockScript global script
- Automatically increments for each new structure
- Can be deleted as a group using deleteblock command

**Uses:**
- Group identification
- Structure management
- Block deletion
- Area organization

**Technical Details:**
- Block numbers are sequential integers starting from 1
- Numbers never reused, even after server restart
- Global script ensures persistence
- Building commands automatically assign block numbers
- Only grid and maze commands use block numbers
- Individual rooms built with buildroom are not assigned block numbers
- Rooms are tagged with format "room_block_X" where X is the block number
- Block deletion removes both rooms and associated exits

## Coordinate System

**Implementation:**
- Coordinates stored as x,y,z values in room.db.coordinates
- Maintained by CoordMapScript for persistence
- Used for room placement validation
- Available for mapping and navigation features
- Not displayed in room descriptions

## Room Coordinate Management

**Coordinate Storage:**
- Each room stores x,y,z coordinates
- Coordinates managed by CoordMapScript
- Coordinates persist across server restarts
- Internal tracking prevents overlaps
- Coordinate bounds automatically tracked

**Exit Validation:**
- All exits checked for coordinate adjacency
- Invalid connections blocked for non-superusers
- Warning messages for invalid connections
- Supports cardinal and diagonal movement
- Z-axis movement not currently implemented

## Tag Management

### Room Block Tags
All rooms created by buildgrid and buildmaze are automatically tagged with their block number:
- Tag format: "room_block_X" (where X is the block number)
- Tag category: "room_block"
- Tags persist across server restarts
- Block numbers are never reused
- Individual rooms from buildroom are not assigned block tags

### Block Deletion Rules
- Only rooms with matching block tags are deleted
- All exits connected to deleted rooms are removed
- Both incoming and outgoing exits are cleaned up
- Coordinate records are removed from tracking system
- Cannot delete blocks containing your current location
- Requires confirmation for large block deletions
- Safety features prevent orphaned exits or records

### Tag Search Order
When deleting blocks, the system:
1. First identifies all rooms with matching block tag
2. Collects all exits (both directions) for those rooms
3. Validates room and exit existence before deletion
4. Removes coordinate tracking data
5. Deletes exits first, then rooms
6. Reports total counts of removed objects