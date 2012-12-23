'''
Base class for backing types of wow objects.
'''



class WowObject():
    ''' Interface into the various backing stores for
    wow spell and item data.'''

    def found(self):
        return False

    # Must be implemented by data sources.
    def get_id(self):
        raise Exception

    def get_name(self):
        raise Exception
    
    def trips_gcd(self):
        return False

    # Only needs implementation by items.
    def test_item_slotid(self, slot_id=0):
        if not self.is_item(): return False
        raise Exception
    def get_slot(self):
        raise Exception

    # Only needs implementation by spells
    def self_only(self):
        return False
    
    # Only one of these need implementation
    def is_spell(self):
        return False
    def is_item(self):
        return False


# For offline testing purposes
class TestItem(WowObject):
    def __init__(self, item=''):
        self.name = '10 Pound Mud Snapper'
        self.slot = 23
        self.id   = 6292
    def found(self):
        return True
    def get_id(self):
        return self.id
    def get_name(self):
        return self.name
    def test_item_slotid(self, slot_id=0):
        return slot_id == self.slot
    def is_item(self):
        return True


class TestSpell(WowObject):
    def __init__(self, spell=''):
        self.name = spell
        self.buff = False
        self.gcd  = True
        self.id   = 1234
        self.rank = 1
    def found(self):
        return True
    def get_id(self):
        return self.id
    def get_name(self):
        raise self.name
    def trips_gcd(self):
        return self.gcd
    def is_spell(self):
        return True
