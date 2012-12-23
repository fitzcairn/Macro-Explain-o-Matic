'''
Error messages, removed out to one file for ease of editing.
'''


# Max length for macros.
MAX_LEN_ALLOWED = 1024

# Error for macro too long.
MACRO_LEN_ERROR = """You are attempting to interpret a macro with %s characters. The macro interpreter currently only supports macros up to %s characters in length."""

# Errors reported on exception
LEXER_ERROR = """There were errors in this macro command that make it invalid."""
PARSER_ERROR = """The interpreter did not understand this macro command."""

# Warning for spaces in the command.
WARN_REMOVED_SPACES = """Found and removed %s unneeded characters."""

# If this object is always true, warn that all other command objs are
# a waste of space and return.  If there were params in the next
# object, they will ignored.
WARN_UNUSED_TOKENS = """Previous macro conditions are always true, so this part of your command will never be executed.  Removed <i>%s</i> to save characters."""

# Repeated option args--useless tokens
WARN_UNUSED_REPEATED_ARGS = """This argument is repeated in the same condition.  Removed <i>%s</i> to save characters."""

# Repeated phrase
WARN_REPEATED_PHRASE = """This entire phrase is repeated within the same condition. Removed to save characters."""

# Repeated condition
WARN_REPEATED_CONDITION = """This entire condition is repeated within the same macro command object. Removed to save characters."""

# Repeated option word
WARN_REPEATED_OPTION_WORD = """This option word is used multiple times in the same condition.  Consider either eliminating one use or combining arguments to save characters."""

# Warn that this target is only valid in certain situations.
WARN_TARGET_PARTY_OR_SELF = """Be aware that this macro will only correctly target %s if %s is either your name or the name of someone in your group."""

# Using action-oriented option words in meta commands
WARN_ACTION_OPTION_IN_META = """The '%s' option is only checked when the macro is triggered. It is not very useful with commands like %s."""

# If this is the last object and the previous object also
# evaluated to true, then this is just a waste of a character.
WARN_UNUSED_EXTRA_ELSE = """The trailing %s token may cause unintended bugs with your command.  Check the interpretation of this macro to be sure it is doing what you intended."""

# If this is the last object and the previous object did NOT
# automatically evaluate to true, then this command may have
# unintended effects.  Warn if there are no parameters!
WARN_UNINTENDED_ELSE = """Be careful--this macro could contain a subtle bug!  The empty conditions after the %s token automatically evaluate to true. The conditions prior to the %s token are not always true.  This means that if the conditions fail, %s will still execute with NO parameters.  Is this what you intend?"""

# If we hit an empty condition and there are still more conditions to
# process, we're done--the other conditions will never be executed.
WARN_UNUSED_CONDITIONS = """Empty conditions--conditions with no option tests--are automatically True, causing %s to run on the default target.  No condition after this one will ever be evaluated.  Did you mean to put the empty condition after other conditions?"""

# Check if a target was set in the conditional that is the key unit
# for this command.  If so the parameters are used as the target.
# Otherwise, the unit in the parameters is ignored.
WARN_NOT_KEY_UNIT = """The target parameter %s is ignored in this macro.  This is because the target in the conditional is not the command's key unit, which is '%s'.  To have '%s' used as the target, use '%s' as the conditional target."""

# If the entire condition refers only to the player, the user
# specified a target in this condition, and the verb does not accept
# external targets, then the target is either ignored (if not
# 'player') or superflous.
WARN_CONDITIONS_PLAYER = """Every condition in this set refers only to yourself, and the %s command does not take external targets.  There is no need to specify your target in this macro."""

# Verb doesn't take external targets.
WARN_TARGET_IGNORED = """The target in this condition is completely ignored.  The %s command does not accept external targets."""

# Specifying target=self and then phrases that only check self anyways
# with a verb that only casts self.
WARN_TARGET_USELESS_SELF = """All conditions in this phrase only evaluate against yourself,' and the %s command does not take external targets.  Your target will be completely ignored in this macro. and can be removed."""

# Specifying target=self and then any other phrases in a condition is
# kind of a waste of time.
WARN_TARGET_SELF = """If you specify yourself as the target, all other conditions will be checked against yourself.  Is that your intent?"""

# Did we recognize this spell?
WARN_UNKNOWN_SPELL = """Did not recognize this a spell.  Check spelling and caps?"""

# Does this verb itself trip the GCD?
WARN_VERB_GCD = """The %s command almost always trips a global cooldown cycle which will prevent will prevent later actions in this macro from executing."""

# Does this spell trip the GCD?
WARN_SPELL_GCD = """Casting %s trips a global cooldown cycle for all spells, which will prevent will prevent later spells in this macro from being cast."""

# Did we recognize this item?
WARN_UNKNOWN_ITEM = """Did not recognize this item.  Check spelling and caps?"""

# Using the item trip the GCD?
WARN_ITEM_GCD = """%s %s while in combat could trigger a global cooldown cycle for all spells and items, preventing further actions in your macro."""
    
# Item when we expected a spell (and vice versa)
WARN_ITEM_INSTEAD_OF_SPELL = """The %s command takes spells.  %s was recognized as an item. Did you mean to use a command like /use?"""
WARN_SPELL_INSTEAD_OF_ITEM = """The %s command takes items.  %s was recognized as an spell. Did you mean to use a command like /cast?"""


''' Interpretation Errors. '''

# Correcting a number >1 for cycle commands
WARN_NUMBER_LT_1 = """Using 0 as a parameter for this targeting command is the same as not having a parameter at all.  Remove this if you need to save a character."""
WARN_NUMBER_GT_1 = """This targeting command only requires a '1' to reverse the targeting order. Changing your parameter from '%s' to 1 for clarity."""

# Warn for wrong targeting command command.
WARN_USE_TARGET_INSTEAD_OF_EXACT = """This targeting command is used for targeting exact unit names. While your macro functions correctly, consider using /tar instead to save character space."""

# Warn when equipping something for the wrong slot.
WARN_WRONG_SLOT = """%s is not equippable in slot %s %s."""#  It should instead be equipped in slot %s as your %s."""

# Warn when the slot is invalid
WARN_INVALID_SLOT = """Equipment slot %s is most likely invalid.  Please double check this value."""

# Warn when we have repeated related commands.
WARN_RELATED_COMMAND = """Command %s will be ignored, since %s was already used in this macro."""
