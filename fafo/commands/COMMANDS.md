# Room Building and Navigation Commands Documentation

## Overview
This document describes two main command systems:
1. Room building commands for world creation
2. Navigation commands for moving between rooms

## Command Sets

### BuilderCmdSet
Builder-only commands for world creation, requiring the "build" or "Builder" permission:
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

### CmdBuildRoom
Creates a single room with connecting exits in a specified direction.

**Class Location:** `commands/builder.py`

**Usage:** 
```
buildroom <direction>
```

**Valid Directions:**
- Cardinal: north/n, south/s, east/e, west/w
- Intercardinal: northeast/ne, northwest/nw, southeast/se, southwest/sw

**Exit Creation:**
- Forward exit gets the input direction as its key
  - If short form used (e.g. 'n'), long form added as alias ('north')
  - If long form used (e.g. 'north'), short form added as alias ('n')
- Return exit gets opposite direction as key with corresponding alias
- All exits work with both full names and abbreviations

### CmdBuildGrid
Creates a rectangular grid of interconnected rooms.

**Usage:**
```
buildgrid <direction1> <number1> <direction2> <number2>
```

**Valid Directions:**
- Cardinal directions only: north/n, south/s, east/e, west/w
- Each direction accepts both full name and abbreviation

**Room Naming:**
- Rooms named using coordinate system: "Grid Room (x,y)"
- x coordinate increases in first direction
- y coordinate increases in second direction

**Exit System:**
- All exits work with both full names and abbreviations
- Each room connects to neighbors in both directions
- Return exits automatically created with appropriate aliases

### CmdBuildMaze
Creates a collection of randomly connected rooms.

**Usage:**
```
buildmaze <direction> <number>
```

**Valid Directions:**
- All compass directions supported
- Both full names and abbreviations accepted

**Room and Exit Features:**
- Rooms named sequentially: "Maze Room 1", "Maze Room 2", etc.
- First room connects to starting point in specified direction
- Each subsequent room connects to at least one previous room
- Random direction selection for connections after first room
- Each connection creates appropriate return exits
- All exits support both full names and abbreviations
- 30% chance for additional random connections between rooms

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
- Block number stored in room.db.room_block attribute
- Managed by RoomBlockScript global script
- Automatically increments for each new structure

**Uses:**
- Group identification
- Structure management
- Future block operations
- Area organization

**Technical Details:**
- Block numbers are sequential integers starting from 1
- Numbers never reused, even after server restart
- Global script ensures persistence
- Building commands automatically assign block numbers
- Only grid and maze commands use block numbers
- Individual rooms built with buildroom are not assigned block numbers