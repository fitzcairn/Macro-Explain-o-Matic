#!/usr/bin/python
import getpass
import sys
import datetime
import logging
import time
import csv
import copy

#sys.path.append("C:\Program Files\Google\google_appengine")
#sys.path.append("C:\Program Files\Google\google_appengine\lib\yaml\lib")

from google.appengine.ext            import db
from macro.data.appengine.wow        import WOWSpell, WOWItem, get_item_key, get_spell_key
from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.ext            import db

# Backoff time on timeout, in seconds.
_BACKOFF = 3

# Number of retries allowed on failure
_MAX_RETRY = 3

# Simple auth function.
def auth_func():
    return raw_input('Username:'), getpass.getpass('Password:')


# Helper to output entities:
def str_entity(e, is_item=False):
    if is_item: return "name: [%s] slot: [%s] id: [%s]" % \
       (e.name, e.slot, e.id)
    return "name: [%s] buff: [%s] gcd: [%s] id: [%s] rank: [%s]" % \
           (e.name, e.buff, e.gcd, e.id, e.rank)


# Helper to minimize repeated code.  Gets a WOWspell/item
def get_datastore_obj(new, is_item=False):
    if is_item:
        return WOWItem(key_name=get_item_key(new['name']),
                       name=new['name'],
                       slot=new['slot'],
                       id=new['id'])      
    else:
        return WOWSpell(key_name=get_spell_key(new['name']),
                        name=new['name'],
                        buff=new['buff'],
                        gcd=new['gcd'],
                        rank=new['rank'],
                        id=new['id'])
      

# Helper to manage retries on urlib, etc exception
def do_w_retry(func, arg=None, num_retries=_MAX_RETRY):
    tries = 0
    while True:
        try:
            if arg: return func(arg)
            else:   return func()
        except Exception, inst:
            logger.info("FAIL: attempt %s of %s returned an error." % ((tries + 1), num_retries))
            logger.info("Got exception: %s" % inst)
            logger.info("Function: %s" % func)
            logger.info("Args: %s" % arg)
            logger.info("  Sleeping %s sec, then retrying..." % _BACKOFF)
            time.sleep(_BACKOFF)
            tries += 1
            if tries >= num_retries:
                logging.error("Dying with %s" % inst)
                raise
            pass    
    

# Take the contents of a parsed csv in dict form and insert into the DB.
def insert_from_csv(csv_map, is_item=False, batch=100):
    what = "item" if is_item else "spell"
    new_entities = []
    keys = csv_map.keys()
    keys.sort()
    for key in keys:
        new = csv_map[key]
        logger.info("  Adding %s with key: [%s]" % (what, key))
        new_entities.append(get_datastore_obj(new, is_item))

        # If we have a full bath to an insert.
        if len(new_entities) == batch:
            logger.info("Inserting batch of %s new %ss" % (len(new_entities), what))
            do_w_retry(db.put, new_entities)
            new_entities = []

    # If we have a last incomplete batch, send it.
    if len(new_entities) > 0:
        logger.info("Inserting batch of %s new %ss" % (len(new_entities), what))
        do_w_retry(db.put, new_entities)


# Taken from example online.
class Mapper(object):
    # Subclasses should replace this with a model class (eg,
    # model.Person).
    KIND = None

    # Subclasses can replace this with a list of (property, value)
    # tuples to filter by.
    FILTERS = []
    
    def map(self, entity):
        """Updates a single entity.
     
        Implementers should return a tuple containing two iterables
        (to_update, to_delete).
        """
        return ([], [])

    def get_query(self):
        """Returns a query over the specified kind, with any appropriate
        filters applied."""
        q = self.KIND.all()
        for prop, value in self.FILTERS:
            q.filter("%s =" % prop, value)
        q.order("__key__")
        return q

    def run(self, is_item, batch_size=100):
        """Executes the map procedure over all matching entities."""
        q = self.get_query()
        entities = do_w_retry(q.fetch, batch_size)
        count = 0
        while entities:
            to_put = []
            to_delete = []
            for entity in entities:
                map_updates, map_deletes = self.map(entity)
                if map_updates:
                    logger.info("    Replacing entity id: %s" % ','.join([str(e.id) for e in map_updates]))
                if map_deletes:
                    logger.info("    Removing entity: %s" % str_entity(entity, is_item))
                to_put.extend(map_updates)
                to_delete.extend(map_deletes)
            if to_delete:
                do_w_retry(db.delete, to_delete)
            if to_put:
                do_w_retry(db.put, to_put)
            q = do_w_retry(self.get_query)
            q.filter("__key__ >", entities[-1].key())
            entities = do_w_retry(q.fetch, batch_size)
            count += 1
            logger.info("Handled batch %s..." % count)


class WOWUpdater(Mapper):
    ''' Updater for WOW* appengine entities. '''
    def __init__(self, entity_map, is_item=False):
        self.is_item = is_item
        if is_item:
            self.KIND = WOWItem
        else:
            self.KIND = WOWSpell
        self.MAP = entity_map
          
    def map(self, entity):
        # Use the saved entity map to determine what to do with this
        # spell.
        #
        # If it is not in the map, delete.
        #
        # If it is present in the map and no fields are different,
        # then we do nothing.
        #
        # If it is in the map but has different data, we delete
        # the existing entity and upload a modified one.
        delete = []
        update = []

        # Get key for the entity
        if self.is_item:
            key = get_item_key(entity.name)
        else:
            key = get_spell_key(entity.name)          

        # Do we delete it?
        if key not in self.MAP:
            logger.info("  Adding key [%s] for deletion." % key)
            delete.append(entity)
        # No, do we need to update it?
        else:
            # Check fields, saving diff for report
            new = self.MAP[key]
            new_entity = None
            diff = []

            if self.is_item:
                if entity.id != new['id']:
                    diff.append([entity.id, new['id']])
                if entity.name != new['name']:
                    diff.append([entity.name, new['name']])
                if entity.slot != new['slot']:
                    diff.append([entity.slot, new['slot']])
            else:
                if entity.id != new['id']:
                    diff.append([entity.id, new['id']])
                if entity.name != new['name']:
                    diff.append([entity.name, new['name']])
                if entity.buff != new['buff']:
                    diff.append([entity.buff, new['buff']])
                if entity.gcd  != new['gcd']:
                    diff.append([entity.gcd, new['gcd']])        
                if entity.rank != new['rank']:
                    diff.append([entity.rank, new['rank']])        

            # If differences found, need to update this entity.
            if len(diff) > 0:
                logger.info("  Found difference for key [%s]: %s" % (key,
                                                                      ', '.join(map(lambda t: "%s -> %s" % (t[0], t[1]), diff))))
                new_entity = get_datastore_obj(new, is_item)
                update.append(new_entity)
                delete.append(entity)

            # Remove this entity once we've examined it so we
            # don't insert a dupe later.
            del self.MAP[key]
        return (update, delete)


def parse_csv(in_csv, is_item=False):
    entity_map = {}
    for entity in csv.reader(open(in_csv)):
        if is_item:
            # Map this into a hash and save.
            new = {'name': entity[0],
                   'slot': int(entity[1]),
                   'gcd':  True if entity[2] == 'True' else False,
                   'id':   int(entity[3])}
            # For items, save both item id and name as searchable
            # keys.
            entity_map[get_item_key(new['name'])] = copy.deepcopy(new)
            entity_map[get_item_key(new['id'])] = copy.deepcopy(new)
        else:
            # Map this into a hash and save.
            new = {'name': entity[0],
                   'buff': True if entity[1] == 'True' else False,
                   'gcd':  True if entity[2] == 'True' else False,
                   'id':   int(entity[3]),
                   'rank': int(entity[4]) if len(entity[4]) > 0 else 0}
            entity_map[get_spell_key(new['name'])] = copy.deepcopy(new)
    return entity_map
    

#### MAIN #####
if __name__ == "__main__":
    # Set up the logger
    logging.basicConfig(level=logging.INFO,
                        format='%(message)s')
    logger = logging.getLogger('upload')

    # Parse command-line options.
    if len(sys.argv) < 5:
        print "Usage: %s app_id [spell|item] csv host" % (sys.argv[0],)
        sys.exit(1)
    app_id    = sys.argv[1]
    is_item   = sys.argv[2].lower()[0] != 's'
    in_csv    = sys.argv[3]
    if len(sys.argv) > 4:
        host = sys.argv[4]
    else:
        host = '%s.appspot.com' % app_id

    # Add a handler to the logger to log to file.
    fh = logging.FileHandler("upload_of_%s.%s.txt" % \
                             ("items" if is_item else "spells", time.time()), mode='w')
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)

    # Report what we're doing.
    logger.info("About to update %s for app %s on host %s from file %s" %\
                 ("items" if is_item else "spells", app_id, host, csv))

    # Parse the csv file into a hash keyed on spell id.
    logger.info("...Parsing input csv file %s" % in_csv)
    entity_map = parse_csv(in_csv, is_item)

    # Use local dev server by passing in as parameter:  
    # servername='localhost:8080'  
    # Otherwise, remote_api assumes you are targeting APP_NAME.appspot.com  
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)

    # Update data.
    logger.info("Updating existing data...")
    WOWUpdater(entity_map, is_item).run(is_item)

    # Insert remaining new data.
    logger.info("Inserting remaining new data...")
    insert_from_csv(entity_map, is_item)
