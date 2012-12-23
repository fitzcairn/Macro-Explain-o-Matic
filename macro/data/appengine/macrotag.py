'''
An inverted tag -> macroid index.

We shard the entries for each tag to reduce locking issues.
'''

import logging
import urllib
import random
from google.appengine.api               import memcache
from google.appengine.ext               import db


# How many prefixes to fetch at one go.
_NUM_PREFIX_TO_FETCH = 10

# Delimiter to pack lists for memcached
_DELIM = ","

# The saved macro information from the database.  Fairly light, but
# traffic will be high, so only keep for 1 minute.
_MEMCACHED_TAG = 60

# Datastore class for the tag
class MacroTag(db.Model):
    ''' Entity class storing tags for Macros.  '''
    # The tag broken down into prefixes for typeahead.
    prefix_list = db.ListProperty(str)


def save_macro_tags(tags):
    ''' Create tag entities for each tag in the list,
    storing the macro_id as part of the key. '''

    def txn(tag, prefix_list):
        # Create the tag only if it doesn't exist already.
        saved_tag = MacroTag.get_by_key_name(tag)
        if not saved_tag:
            saved_tag = MacroTag(key_name = tag, prefix_list = prefix_list)
            saved_tag.put()
        return saved_tag
    
    # Create and save
    # NOTE: there is no shared locking across tags, so
    # we could get race conditions where two tags of the same
    # name are saved at once.  In this case, need to ignore 
    # failures -- add blanked try/catch and pass on exceptions
    for t in tags:
        prefix_list = [t[0:i] for i in xrange(1, len(t))] + [t]
        try:
            db.run_in_transaction(txn, t, prefix_list)
        except:
            pass

def get_macro_tags_for(tag_prefix):
    ''' Given a prefix to search for, return the list of
    tags starting with this prefix. '''

    if tag_prefix:
        tag_prefix = tag_prefix.lower()

    # Check memcached first.
    ret_list = memcache.get(tag_prefix)
    if not ret_list:
        # Fetch and save in memcached
        q = MacroTag.all(keys_only=True).filter("prefix_list =", tag_prefix)
        ret_list = [r.name() for r in q.fetch(_NUM_PREFIX_TO_FETCH)]
        ret_list.sort()
        memcache.add(tag_prefix, ret_list,
                     _MEMCACHED_TAG)
    return ret_list


