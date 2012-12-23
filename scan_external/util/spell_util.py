'''
Specialized logic for wowhead spells.
Put into a module for easier testing.
'''

import re


# Decide whether or not to save this spell based on its attributes.
# Returns T/F
def keep_or_toss(new_data, old_data):
  # Is the incoming spell taught from a trainer?
  if "taught" in new_data:
    # Prefer spells with trainer records over those without.
    if "taught" not in old_data:
      return True
    
  # Spell either not taught by trainer, or both saved and incoming
  # records contain trainer information.
  # Does the incoming spell have a rank?
  if "rank" in new_data:
    # Prefer spells with rank info over those without--rank new_data is
    # a good indication of higher quality spell new_data.
    if "rank" not in old_data:
      return True
      
    # If there are ranks in both saved and new new_data, save the
    # highest ranked spell we've seen thus far.   
    if new_data["rank"] > old_data["rank"]:
      return True
      
  # If we're here, the only remaining decision criteria is spellid.
  # Save the spell with the highest spellid (TODO: improve this.)
  if new_data["spell_id"] > old_data["spell_id"]:
    return True

  return False

