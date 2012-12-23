'''
Test objects for wow.
'''

from macro.data.wow_obj_base    import WowObject
from macro.interpret.slots      import DATA_TO_GAME_SLOTS

def get_test_object(obj, is_item=False):
    if is_item: return TestItem(obj)
    return TestSpell(obj)


# For offline testing purposes
class TestItem(WowObject):
    def __init__(self, item=''):
        self.name = item
        self.slot = 23
        self.id   = 6292
    def found(self):
        return True
    def get_id(self):
        return self.id
    def get_name(self):
        return self.name
    def get_slot(self):
        return self.slot
    def test_item_slotid(self, slot_id=0):
        if self.slot in DATA_TO_GAME_SLOTS:
            return (slot_id in DATA_TO_GAME_SLOTS[self.slot])
        return False
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
        return self.name
    def trips_gcd(self):
        return self.gcd
    def is_spell(self):
        return True
