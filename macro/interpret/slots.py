''' Slot decoding. '''

from macro.interpret.errors    import WARN_INVALID_SLOT

# Check the slot token.
def check_slot_token(slot_tok):
    if not slot_tok: return
    try:
        if slot_tok.data_type is int and int(slot_tok.data) < MAX_SLOT_ID and int(slot_tok.data) >= MIN_SLOT_ID:
            return
    except:
        pass
    slot_tok.warn = (WARN_INVALID_SLOT,
                     [slot_tok])
    return
        
# Get the descrption back for a slot.
def decode_wow_slot(slot):
    k = str(slot)
    if k in SLOT_MAP:
        return SLOT_MAP[k]
    return None

def decode_data_slot(slot):
    k = str(slot)
    if k in DATA_SLOT_MAP:
        return DATA_SLOT_MAP[k]
    return None

def get_wow_slots_for_data(slotid):
    try:
        slot = int(slotid)
        slot_strs = [str(s) for s in DATA_TO_GAME_SLOTS[slot]]
        return " or ".join(slot_strs)
    except:
        pass
    return "(unrecognized slot)"


''' Maximum slot id. '''
MAX_SLOT_ID = 100
MIN_SLOT_ID = 0


''' Map of inventory slot ids in WoW to description.'''
SLOT_MAP = {
    '0': 'ammo', 
    '1': 'head armor',
    '2': 'neck',
    '3': 'shoulder armor', 
    '4': 'shirt',
    '5': 'chestpiece',
    '6': 'belt',
    '7': 'leg armor',
    '8': 'boots',
    '9': 'wrist armor', 
    '10': 'gloves', 
    '11': 'first ring', 
    '12': 'second ring',
    '13': 'first trinket', 
    '14': 'second trinket',
    '15': 'back',
    '16': 'main-hand weapon', 
    '17': 'off-hand weapon, two-hand weapon, or shield',
    '18': 'ranged weapon, libram, or relic',
    '19': 'tabard',
    '20': 'first bag (the rightmost one)',
    '21': 'second bag',
    '22': 'third bag',
    '23': 'fourth bag (the leftmost one)'
    }

''' Slot map for external sites, which are not the same as the WoW slots. '''
DATA_SLOT_MAP = {
    '0': 'ammo', 
    '1': 'head armor',
    '2': 'neck',
    '3': 'shoulder armor', 
    '4': 'shirt',
    '5': 'chestpiece',
    '6': 'belt',
    '7': 'leg armor',
    '8': 'boots',
    '9': 'wrist armor', 
    '10':'gloves', 
    '11':'finger',
    '12':'trinket',
    '13':'one-hand weapon',
    '14':'shield',
    '15':'ranged weapon',
    '16':'back',
    '17':'two-hand weapon',
    '18':'bag',
    '21':'main-hand weapon',
    '22':'off-hand weapon',
    '23':'item held in off-hand',
    '24':'projectile',
    '25':'thrown weapon',
    '26':'ranged weapon',
    '28':'relic or libram',
}


''' Decoder for game data slots for raw item data
from exernal sites '''
DATA_TO_GAME_SLOTS = {0: set([0]),
                      1: set([1]),
                      2: set([2]),
                      3: set([3]),
                      4: set([4]),
                      5: set([5]),
                      6: set([6]),
                      7: set([7]),
                      8: set([8]),
                      9: set([9]),
                      10: set([10]),
                      11: set([11, 12]),
                      12: set([13, 14]),
                      13: set([16, 17]),
                      14: set([17]),
                      15: set([18]),
                      16: set([15, 26]),
                      17: set([17]),
                      18: set([20, 21, 22, 23]),
                      19: set([19]),
                      21: set([16]),
                      22: set([17]),
                      23: set([17]),
                      24: set([0]),
                      25: set([18]),
                      28: set([18])}

