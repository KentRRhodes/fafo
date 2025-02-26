"""
Region manager for loading and managing region data.
"""
import os
import json
from evennia import logger

class RegionError(Exception):
    """Base exception for region-related errors"""
    pass

class RegionManager:
    """
    Manages loading and accessing region definitions.
    """
    def __init__(self, region_type, data_path):
        """
        Initialize region manager.
        
        Args:
            region_type (str): Type of region ("descriptive", "spawning", "resource")
            data_path (str): Path to region definition file
        """
        self.region_type = region_type
        self.data_path = data_path 
        self.regions = {}
        self._load_regions()
    
    def _load_regions(self):
        """Load all region definitions from JSON file"""
        filepath = f"{self.data_path}.json"
        if not os.path.exists(filepath):
            logger.log_err(f"Region data file not found: {filepath}")
            return
            
        try:
            with open(filepath, 'r') as f:
                self.regions = json.load(f)
        except Exception as e:
            logger.log_err(f"Error loading region file {filepath}: {e}")
    
    def get_region(self, region_id):
        """Get region data by ID"""
        return self.regions.get(region_id)
    
    def list_regions(self):
        """List all available regions"""
        return list(self.regions.keys())

    def _get_descriptor_name(self):
        """Get appropriate attribute name based on region type"""
        if self.region_type == "descriptive":
            return "descriptive_region"
        elif self.region_type == "spawning":
            return "spawning_regions"
        else:  # resource
            return "resource_regions"

    def apply_to_room(self, room, region_id):
        """
        Apply region to a room.
        
        Args:
            room (Object): Room to apply region to
            region_id (str): ID of region to apply
            
        Returns:
            bool: True if region was applied successfully
        """
        region_data = self.get_region(region_id)
        if not region_data:
            raise RegionError(f"Region '{region_id}' not found")
        
        attr_name = self._get_descriptor_name()
        
        # Handle descriptive regions (single region only)
        if self.region_type == "descriptive":
            # Remove any existing descriptive region first
            if hasattr(room.db, attr_name):
                self.remove_from_room(room, getattr(room.db, attr_name))
            
            # Set new descriptive region
            setattr(room.db, attr_name, region_id)
            # Update room name format
            room.name = f"[{region_data.get('name', region_id)}]{room.name}"
        
        # Handle spawning and resource regions (multiple allowed)
        else:
            # Initialize set if it doesn't exist
            if not hasattr(room.db, attr_name):
                setattr(room.db, attr_name, set())
            
            # Add new region to set
            getattr(room.db, attr_name).add(region_id)
        
        return True
    
    def remove_from_room(self, room, region_id):
        """
        Remove region from a room.
        
        Args:
            room (Object): Room to remove region from
            region_id (str): ID of region to remove
            
        Returns:
            bool: True if region was removed successfully
        """
        attr_name = self._get_descriptor_name()
        
        # Handle descriptive regions
        if self.region_type == "descriptive":
            if getattr(room.db, attr_name, None) == region_id:
                setattr(room.db, attr_name, None)
                # Reset room name
                if room.name.startswith('['):
                    room.name = room.name.split(']', 1)[1]
                return True
        
        # Handle spawning and resource regions
        else:
            region_set = getattr(room.db, attr_name, set())
            if region_id in region_set:
                region_set.discard(region_id)
                return True
        
        return False