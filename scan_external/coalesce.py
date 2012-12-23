'''
Takes multiple spell or item csvs and
coalesces them into a single authoritative csv.
'''

import re
import sys
import csv
import time
import copy
import logging

# Get the APIs
from scan_external.webapi.wowhead     import WowheadRequest
from scan_external.webapi.wowdb       import WowdbRequest
from scan_external.webapi.mmochampion import MmoChampionRequest


# Name filter rules.
NAME_FILTER = [re.compile("TEST"),
               re.compile("QA"),
               re.compile("Debug"),
               re.compile("DEBUG"),
               re.compile("[\[\]]"),
               re.compile("\(Unused\)"),
               re.compile("Deprecated"),
               re.compile("DEPRECATED")]

# Rank/slot filter
RANK_SLOT_FILTER = re.compile("^\d+$")


# Read a CSV into memory, returning a map of id -> data
def parse(csv_file, items=True):
    ret_map = {}
    for row in csv.reader(open(csv_file)):
        if len(row[0]) > 0:
            fail = False
            # Filter on name.
            row[0] = row[0].strip()
            for name_filter in NAME_FILTER:
                if name_filter.search(row[0]):
                    logging.debug("Bad name for %s %s: %s" % \
                                  ("item" if items else "spell",
                                   row[3], row[0]))
                    fail = True
            if not fail and items:
                # Ensure rank contains a digit, else clear it.
                if row[1] == '' or not RANK_SLOT_FILTER.search(row[1]):
                    logging.debug("Bad slot for item %s: %s" % (row[3], row[1]))                
                    row[1] = '-1'
                ret_map[row[3]] = {"name":    row[0],
                                   "slot":    int(row[1]),
                                   "gcd":     row[2],
                                   "item_id": int(row[3])}
            elif not fail:
                # Ensure rank contains a digit, else clear it.
                if row[4] is not '' and not RANK_SLOT_FILTER.search(row[4]):
                    logging.debug("Bad spell rank for spell %s: %s" % (row[3], row[4]))
                else:
                    ret_map[row[3]] = {"name":     row[0],
                                       "self":     row[1],
                                       "gcd":      row[2],
                                       "spell_id": int(row[3]),
                                       "rank":     int(row[4])}
    return ret_map


# Helper to get most frequent item in a list, first on ties.
def _get_most_freq(items, handle_slot=False):
    max_c   = -1
    max_e   = -1 if handle_slot else None
    results = {}
    for item in items: 
        if item != '':
            results.setdefault(item, 0)
            results[item] += 1  
    for i,c in results.items():
        # If we're handling slots, prefer the minimum non-negative slot.
        if handle_slot and max_e < 0 and i > max_e:
            max_c = c
            max_e = i
        elif handle_slot and i > 0 and i < max_e:
            max_c = c
            max_e = i            
        # Otherwise, just take the most frequent
        elif c > max_c:
            max_c = c
            max_e = i
    return max_e


# Helper to aggregate different sources of data
def _aggregate(sources, fields):
    c = sources[0]

    # Add a count for number of disagreements for this item.
    c["_d"] = 0

    # Add a count for how many sources there were for this item.
    c["_n"] = len(sources)

    if len(sources) > 1:
        # Check field agreement
        for f in fields:
            f_set = [s[f] for s in sources]
            if not sum([f_set[0] == v for v in f_set]) == len(f_set):
                c["_d"] += 1
                # For GCD fields, if we have only two sources and they
                # don't agree, choose True.  GCD is most always false,
                # require high agreement to override this.
                if f is "gcd" and len(f_set) < 3:
                    c[f] = 'True'
                else:
                    c[f] = _get_most_freq(f_set, (f is "slot"))
                if f is not "slot": logging.debug("mismatch for entry %s field %s: %s -- chose [%s]" % (entity_id, f, f_set, c[f]))
    return c


# Selection functions--choose what data to keep.
def choose_item(entity_id, source_data, out_set):
    c = _aggregate(source_data, ["name", "slot", "gcd"])

    # Now that we have something for this itemid, see if the name is
    # already taken.
    if c["name"] in out_set:
        prev = out_set[c["name"]]

        # Prefer a) item with a slot.
        if c["slot"] > 0 and prev["slot"] < 0:
            out_set[c["name"]] = c
        # b) item with more sources
        elif c["_n"] > prev["_n"]:
            out_set[c["name"]] = c
        # c) item with less disagreements among sources
        elif c["_d"] < prev["_d"]:
            out_set[c["name"]] = c
        # d) item with larger itemid (crap heuristic)
        elif c["item_id"] > prev["item_id"]:
            out_set[c["name"]] = c
    else:
        out_set[c["name"]] = c


# Choose what spell to keep.
def choose_spell(entity_id, source_data, out_set):
    spell = _aggregate(source_data, ["name", "self", "rank", "gcd"])
    entities = [spell]

    # If this spell has a rank, also consider it for the
    # the ranked slot.
    if spell["rank"]:
        ranked_spell = copy.deepcopy(spell)
        ranked_spell["name"] = "%s(Rank %s)" % (spell["name"], spell["rank"])
        entities.append(ranked_spell)
        
    # Choose whether to keep the spell entites as authoritative.
    for c in entities:
        if c["name"] in out_set:
            prev = out_set[c["name"]]
            # a) prefer the spell that has a parsed rank.
            if c["rank"] and not prev["rank"]:
                out_set[c["name"]] = c
            # b) If this spell has a rank and the rank is greater
            # than the saved rank, keep it.
            elif c["rank"] and prev["rank"]:
                if c["rank"] > prev["rank"]:
                    out_set[c["name"]] = c
            # Prefer c) spell with more sources
            elif c["_n"] > prev["_n"]:
                out_set[c["name"]] = c
            # d) spell with less disagreements among sources
            elif c["_d"] < prev["_d"]:
                out_set[c["name"]] = c
        else:
            out_set[c["name"]] = c
    return


# Entry point for coalescing.
if __name__ == "__main__":
    # Set up the logger
    logging.basicConfig(level=logging.INFO,
                        format='%(message)s')

    # Decide if we're scanning items or spells.
    items = True
    try:
        if sys.argv[1].lower()[0] == 's':
            logging.info("About to coalesce SPELL data.")
            items = False
        else:
            logging.info("About to coalesce ITEM data.")
    except:
        logging.error("Require spell/items as input.")
        sys.exit(1)        

    # Get our input files
    try:
        in_files = sys.argv[2:]
        if not in_files: raise Exception()
    except:
        logging.error("Require at least one input file.")
        sys.exit(1)

    # Parse them.
    logging.info("...Parsing input data...")
    parsed_csv = {}
    keyset = set()
    for f in in_files:
        try:
            parsed = parse(f, items)
            if parsed:
                parsed_csv[f] = parsed
                logging.info("    Source %s has %s entries." % (f, len(parsed_csv[f].keys())))
                keyset = keyset | set(parsed_csv[f].keys())
        except Exception, inst:
            logging.error("Error parsing file " + str(f))
            raise

    # Now for each unique element in the set, make a decision which to
    # keep.
    logging.info("...Coalescing parsed input...")
    final_set = {}
    for entity_id in keyset:
        source_data = []
        for f in in_files:
            if entity_id in parsed_csv[f]:
                source_data.append(parsed_csv[f][entity_id])
        if items:
            choose_item(entity_id, source_data, final_set)
        else:
            choose_spell(entity_id, source_data, final_set)


    # Write out resulting csv file.
    logging.info("...Writing out final coalesced data...")
    out = open("%s%s" % ("coalesced_%s.csv." % ("item" if items else "spell"), time.time()), 'w')
    for data in final_set.values():
        if items:
            line = ",".join(['"%s"' % str(data["name"]).replace('"', '""'),
                             str(data["slot"]),
                             str(data["gcd"]),
                             str(data["item_id"])])
        else:
            if data['rank'] == '':
                data['rank'] = '1'
            line = ",".join(['"%s"' % str(data["name"]).replace('"', '""'),
                             str(data["self"]),
                             str(data["gcd"]),
                             str(data["spell_id"]),
                             str(data["rank"])])
        out.write(line + "\n")
        out.flush()
    out.close()
    logging.info("Done!")
