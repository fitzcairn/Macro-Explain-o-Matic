'''
Simple scan of web apis for item/spell data.

Outputs CSV files for postprocessing
'''

import re
import sys
import time
import logging

# Get the APIs
from scan_external.webapi.wowhead     import WowheadRequest
from scan_external.webapi.wowdb       import WowdbRequest
from scan_external.webapi.mmochampion import MmoChampionRequest


# Set up the logger
logging.basicConfig(level=logging.DEBUG,
                    format='%(message)s')
logger = logging.getLogger()

# Scan
def scan_and_output(req_objs, csv_objs, todo="items", start=0, end=70000):
    scan_items = (todo == "items")
    # Iterate through the items.  Seems to be about 50000 of them.
    for i in range(end)[start:]:
        if (i % 10 == 0): logging.info("   -> now at %s" % i)

        # For each site, grab
        for src,req in req_objs.items():
            #logging.info("  Querying %s for id %s..." % (src, i))
            try:
                if scan_items: data = req.get_item(i)
                else:          data = req.get_spell(i)
            except Exception, inst:
                #logging.info(" %s couldn't find id %s.  Msg: %s" %\
                #             (src, i, str(inst)))
                continue

            # Write out to this source's csv file.
            # Escape any commas in the name.
            if scan_items:
                line = ",".join(['"%s"' % str(data["name"]).replace('"', '""'),
                                 str(data["slot"]),
                                 str(data["gcd"]),
                                 str(data["item_id"])])
            else:
                line = ",".join(['"%s"' % str(data["name"]).replace('"', '""'),
                                 str(data["self"]),
                                 str(data["gcd"]),
                                 str(data["spell_id"]),
                                 str(data["rank"])])
            csv_objs[src].write(line + "\n")
            csv_objs[src].flush()
            logging.info(line)


if __name__ == "__main__":
    # Decide if we're scanning items or spells.
    todo = "items"
    start = 0
    end   = 70000
    try:
        if sys.argv[1].lower()[0] == 's':
            todo = "spells"
    except:
        pass
    try:
        start = int(sys.argv[2])
        end   = int(sys.argv[3])
    except:
        pass
    logging.info("About to scan all %s, starting at %s and ending at %s" % (todo, start, end))

    # Init the in-memory structure.
    name_to_data = {}

    # Create the request objects
    req_obj = {}
    req_obj['wowhead']     = WowheadRequest("EN")
    req_obj['wowdb']       = WowdbRequest("EN")
    req_obj['mmochampion'] = MmoChampionRequest("EN")
    
    # Create a series of open csv files
    csv_obj = {}
    csv_obj['wowhead']     = open("%s%s" % ("data/new/wowhead_%s.csv." % todo, time.time()), 'w')
    csv_obj['wowdb']       = open("%s%s" % ("data/new/wowdb_%s.csv." % todo, time.time()), 'w')
    csv_obj['mmochampion'] = open("%s%s" % ("data/new/mmochampion_%s.csv." % todo, time.time()), 'w')
    
    # Scan and ouput
    logging.info("All files open, starting scan...")
    scan_and_output(req_obj, csv_obj, todo, start, end)
    logging.info("Scan complete!")

    # Close up csvs.
    for n,csv in csv_obj.items():
        csv.close()

