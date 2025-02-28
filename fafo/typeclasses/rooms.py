"""
Room

Rooms are simple containers that has no location of their own.

"""
from evennia.objects.objects import DefaultRoom
from evennia import GLOBAL_SCRIPTS
from .objects import ObjectParent


class Room(ObjectParent, DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is true for any 'room' in general). They also use basetype_setup() 
    to add locks so they cannot be puppeted or picked up.
    """

    def at_object_creation(self):
        """
        Called when room is first created.
        """
        super().at_object_creation()
        
        # Initialize region attributes as empty
        self.db.regions = {
            'descriptive': None,
            'spawning': None, 
            'resource': None
        }
        
    def get_display_name(self, looker=None, **kwargs):
        """
        Displays the name of the object in a viewer-aware manner.
        
        Args:
            looker (Object, optional): The object looking at this one
            **kwargs: Arbitrary data for use in styling
            
        Returns:
            str: The display name of the room, including region name if set
        """
        base_name = super().get_display_name(looker, **kwargs)
        
        # Get descriptive region if set
        if hasattr(self, 'db') and self.db.regions and self.db.regions.get('descriptive'):
            region_id = self.db.regions['descriptive']
            # Get region data from region manager
            if hasattr(GLOBAL_SCRIPTS, 'region_manager'):
                region_handler = getattr(GLOBAL_SCRIPTS.region_manager.ndb, 'descriptive', None)
                if region_handler:
                    region_data = region_handler.get_region(region_id)
                    if region_data and 'name' in region_data:
                        return f"[{region_data['name']}]{base_name}"
        
        # If no region or error getting region data, return base name
        return base_name

    def return_appearance(self, looker, **kwargs):
        """
        This formats a description. It is the hook a 'look' command
        should call.
        Args:
            looker (Object): Object doing the looking.
            **kwargs: Arbitrary, optional arguments for users
                overriding the call (unused by default).
        """
        if not looker:
            return ""

        # get and identify all objects
        visible = (con for con in self.contents if con != looker and con.access(looker, "view"))
        exits, users, things, hostiles = [], [], [], []
        
        for con in visible:
            key = con.get_display_name(looker)
            if con.destination:
                exits.append(key)
            elif con.has_account:
                users.append(key)
            elif hasattr(con, 'is_alive'): # Check if it's a hostile
                hostiles.append(key)
            else:
                things.append(key)

        # get description, build string
        string = f"|c{self.get_display_name(looker)}|n\n"
        desc = self.db.desc
        
        if desc:
            string += f"{desc}"
            
        # Show hostiles (in yellow) and other objects first
        if hostiles or things:
            string += "\n|wYou see:|n"
            if hostiles:
                string += f" |y{', '.join(hostiles)}|n"
            if things:
                if hostiles:  # Add comma if we had hostiles
                    string += ","
                string += f" {', '.join(things)}"
            
        # Show exits all on one line
        if exits:
            string += f"\n|wObvious Exits:|n {', '.join(exits)}"
            
        # Show other players last
        if users:
            string += f"\n|wAlso here:|n {', '.join(users)}"

        return string
