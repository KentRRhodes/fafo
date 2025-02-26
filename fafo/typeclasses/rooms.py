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
