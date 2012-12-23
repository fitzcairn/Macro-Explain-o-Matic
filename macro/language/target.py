''' Language specification for the WoW Macro language.

Targets.
'''
from macro.language.base import LanguagePart

# Class describing target units
class TargetUnit(LanguagePart):
    ''' Class describing target units for commands that accept units
    directly as their parameters.  In addition to fields in
    LanguagePart, the following describe a TargetUnit:

    needs_dash: (Optional)
    Whether or not this target requires a dash, which is the
    case of name targets within your party (or yourself).
    For example, <name>-target vs. pettarget
    Default True.

    follow: (Optional)
    Whether or not this is a valid follow-on target, i.e.
    pet and target in playerpettargettarget
    Default False.

    recognized:  (Optional)
    Whether or not this was a recongnized target unit.
    Default False.

    perc_target:  (Optional)
    Whether or not this target was a %t.
    Default False.

    req_num_arg:  (Optional)
    target requires an additional numerical argument.
    Default False.

    inc_the:  (Optional)
    Whether or not to prepend "the" to the description.
    Default False.

    use_are:  (Optional)
    Whether to use "is" (default) or "are" after a target for
    joins in conditionals, i.e. target IS in combat.
    Default False.

    use_ap_s:  (Optional)
    Whether to use \'s on target chains.
    Default True.

    use_your:  (Optional)
    Whether or not to use "your" in front of the target if the
    target is not part of a compound statement.  Ex: pet
    Default False.    
    '''
    attr_defaults = {
        'needs_dash'  : True,
        'follow'      : False,
        'recognized'  : False,
        'perc_target' : False,
        'req_num_arg' : False,
        'inc_the'     : False,
        'use_are'     : False,
        'use_your'    : False,
        'use_ap_s'    : True,
        }


''' Map of special target units. '''
TARGET_MAP = {
    'focus':        TargetUnit(needs_dash=False, recognized=True, desc="unit saved as your focus target", inc_the=True),
    'target':       TargetUnit(follow=True, needs_dash=False, recognized=True, desc="currently targeted unit", inc_the=True),
    'player':       TargetUnit(needs_dash=False, recognized=True, desc="you", inc_the=False, use_are=True, use_ap_s=False),
    #'playertarget': TargetUnit(needs_dash=False, recognized=True, desc="your currently targeted unit", inc_the=False),
    'mouseover':    TargetUnit(needs_dash=False, recognized=True, desc="unit your mouse is currently over", inc_the=True),
    'none':         TargetUnit(needs_dash=False, recognized=True, desc="no unit", inc_the=False),
    'party':        TargetUnit(needs_dash=False, recognized=True, desc="party member", req_num_arg=True, inc_the=False),
    'pet':          TargetUnit(follow=True, needs_dash=False, recognized=True, desc="pet", inc_the=False, use_your=True),
    'partypet':     TargetUnit(needs_dash=False, recognized=True, desc="pet of party member", req_num_arg=True, inc_the=True),
    'raid':         TargetUnit(needs_dash=False, recognized=True, desc="raid member", req_num_arg=True, inc_the=True),
    'raidpet':      TargetUnit(needs_dash=False, recognized=True, desc="pet of raid member", req_num_arg=True, inc_the=True),
    #'pettarget':    TargetUnit(needs_dash=False, recognized=True, desc="your pet's target", inc_the=False),
    'arena':        TargetUnit(needs_dash=False, recognized=True, desc="enemy Arena player", req_num_arg=True, inc_the=False),
    '%t':           TargetUnit(recognized=True, desc="(your currently targeted unit)", perc_target=True, inc_the=False),
    '%T':           TargetUnit(recognized=True, desc="(your currently targeted unit)", perc_target=True, inc_the=False),        
    }
