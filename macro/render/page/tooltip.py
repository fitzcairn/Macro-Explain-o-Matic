'''
Rendering for tooltips
'''

import urllib
from google.appengine.api             import memcache

from macro.render.util                import get_macro_obj_from_id, render_macro
from macro.data.appengine.defs        import MEMCACHED_TT
from macro.exceptions                 import NoInputError


# Generate a macro tooltip.
def generate_tooltip(path, macro_id):
    '''
    Generate a macro view page. Returns None on error.
    Propogates exceptions up.
    '''
    rendered_tt = None

    # Make sure we got valid input.
    if not macro_id: raise NoInputError("You entered an invalid macro ID.  Try again?")

    # Check to see if we can fetch the already-rendered tooltip
    # from memcached, since it is static data.
    key = "tt_%s" % macro_id
    rendered_tt = memcache.get(key)
    if not rendered_tt:
        # Create the rendered tooltip and save in memcached
        rendered_tt = render_macro(get_macro_obj_from_id(macro_id),
                                   path,
                                   errors=False,
                                   tt=True,
                                   template='tooltip.template')
        memcache.add(key, rendered_tt, MEMCACHED_TT)

    return rendered_tt
