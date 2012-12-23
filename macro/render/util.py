'''
Utilities used in front-end rendering
'''
import os
import urllib
import time
import logging
from operator                         import itemgetter
from google.appengine.api             import memcache
from google.appengine.ext.webapp      import template

# My modules
from macro.render.defs                import *
from macro.exceptions                 import NoInputError
from macro.data.appengine.defs        import MEMCACHED_VIEWS, MACRO_PROC_KEY, MACRO_VIEW_KEY, MEMCACHED_THROTTLE_SECONDS,MEMCACHED_MACRO_PROC
from macro.render.interpretation      import TOKEN_CS_ON, TOKEN_CS_OFF
from macro.data.appengine.savedmacro  import SavedMacroOps
from macro.render.interpretation      import generate_cmd_html, generate_interpret_html


html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)

def unescape(s):
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    # this has to be last:
    s = s.replace("&amp;", "&")
    return s


# Generate form error text
def get_form_error(field):
    return FORM_SAVE_REQ_ERROR[field]


# Internal helper function translating field maps into template arrays.
# The parameter is the set of previously selected classes.
def translate_classmap(sel=[],in_list=CLASS_LIST):
    '''
    Helper to translate classes into a map for a template.
    '''
    return [{'i': n.replace(" ", "_"), 'v': '1', 'src': '_checked'} \
                                                        if n in sel \
            else {'i': n.replace(" ", "_"), 'v': '0', 'src': ''}    \
            for n in in_list]


# Use memcached to throttle actions.  Check to see if this user has
# done the requested action recently.  If we get no IP, then they
# get tossed in the same bucket as everyone else with no IP.
def throttle_action(action, ip, limit=MEMCACHED_THROTTLE_SECONDS):
    ''' Throttles specified action.  Returns time left till
    user can do that action, 0 = its ok.  Uses IP as id.'''

    key = "%s%s" % (action, str(ip))
    curr_secs = int(time.time())
    user_secs = memcache.get(key)
    if user_secs is not None:
        return (MEMCACHED_THROTTLE_SECONDS - (curr_secs - user_secs))
    else:
      memcache.add(key, int(time.time()), MEMCACHED_THROTTLE_SECONDS)  
    return 0


# Helper function to simplify template rendering.
def render_template(template_obj, template_vars={}, path=''):
    '''
    Helper function to render a template in the template directory
    with its variable substitutions.  Returns template HTML.
    '''
    # Populate the search variables in the base templace
    template_vars['q_in']           = GET_SEARCH_QUERY
    template_vars['s_in']           = GET_SEARCH_SORT
    template_vars['search']         = URL_SEARCH
    template_vars['max_tag_length'] = SINGLE_TAG_MAX_LENGTH
    template_vars['search_text']    = FORM_SEARCH_INPUT_HELP

    # Populate the token highlighting CSS classes, needed in most pages.
    template_vars['tok_on']         = TOKEN_CS_ON
    template_vars['tok_off']        = TOKEN_CS_OFF    

    # Static resources
    template_vars['static']         = STATIC_URL
    
    # Fetch the template path the first time this is called.
    if type(template_obj) is str and path:
        return template.render(os.path.join(path,
                                            template_obj),
                               template_vars)
    # Pre-loaded template
    return template_obj.render(template_vars)


# Get a processed macro from the macro id.
def get_macro_obj_from_id(macro_id, macro=None):
    '''Get a processed macro from the macro id.  Raises an exception
    on error.  Assumes valid input.  Incrments the view counter
    for this macro.'''

    # First check memcache for a processed macro object:
    macro_obj = memcache.get(MACRO_PROC_KEY % macro_id)
    if not macro_obj:
        # Nothing from memcache, load from data store.
        if not macro:
            saved_macro_entity = SavedMacroOps.get_macro_entity(macro_id)
            # If saved_macro_entity is still none, we failed
            # in the datastore.
            if saved_macro_entity is None:
                raise NoInputError("Macro id '%s' not found." % macro_id)
            macro = saved_macro_entity.macro

        # Process the macro, lazily importing.
        from macro.interpret.interpreter import MacroInterpreter
        macro_obj = MacroInterpreter().interpret_macro(macro)

        # Save macro in memcached.
        memcache.add(MACRO_PROC_KEY % macro_id,
                     macro_obj,
                     MEMCACHED_MACRO_PROC)
    return macro_obj


# Render a processed macro's interpretation into a template.
def render_macro(macro_obj, path, errors=True, tt=False, template='processed_macro.template'):
    ''' Helper to render macro interpretation into a template. '''
    macro_output_list = []

    # Render the macro lines
    for cmd in macro_obj:
        macro_output_list.append({'line':      generate_cmd_html(cmd.cmd_list, tt=tt, show_err=errors),
                                  'interpret': generate_interpret_html(cmd.interpret, tt=tt, show_err=errors, cmd_error=cmd.error)})
        
    # Return rendered output
    return render_template(template,
                           {'macro'    : macro_output_list},
                           path)
         

# Fetch a saved macro's populated view template hash
def get_view_dict_from_macro_id(macro_id, saved_macro=None):
    # View pages are extremely heavy, and the majority of their
    # data doesn't change.  First attempt to get the static data
    # from memcached.
    key = MACRO_VIEW_KEY % macro_id
    macro_form_template_values = memcache.get(key)

    # If we missed in memcached, load from the data store.
    if not macro_form_template_values:
        # Ensure we have a saved macro.  Will throw
        # exception on fail.
        if not saved_macro:
            saved_macro = SavedMacroOps(macro_id)

        # Start populating template.
        macro_form_template_values = {
            'macro_input'     : saved_macro.entity.macro,
            'title'           : saved_macro.entity.title,
            'author_name'     : saved_macro.entity.name,
            'author_server'   : saved_macro.entity.server,
            'notes'           : saved_macro.entity.notes,
            'version'         : saved_macro.entity.version,
            'curr_version'    : "%s.%s.%s" % (MAJOR_VERSION,
                                              MINOR_VERSION,
                                              PATCH_VERSION),
            'class_list'      : translate_classmap(in_list=saved_macro.entity.classes),
            'classes'         : ", ".join(saved_macro.entity.classes),
            'tags'            : ", ".join(saved_macro.entity.tags),
            'macro_id'        : macro_id,
            }

        # Save in memcached
        memcache.add(key, macro_form_template_values, MEMCACHED_VIEWS)
    return macro_form_template_values


