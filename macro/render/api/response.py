'''
Create a response for a remote query from the addon interface.
'''

from google.appengine.api             import memcache
from django.utils                     import simplejson

from macro.render.util                import get_macro_obj_from_id, get_view_dict_from_macro_id, render_template
from macro.render.defs                import *
from macro.data.appengine.defs        import MEMCACHED_API 
from macro.render.errors              import render_err_msg
from macro.util                       import valid

# Genereate the edit macro page.
def generate_api_response(path, macro_id, r_type='xml'):
    '''
    Generate an XML/JSON interpretation of a macro.

    Handles exceptions, returning them as errors in the response.

    TO BE WRITTEN: API for response. Use template?
    '''

    # Can we hit memcached for this?
    key = "api_%s_%s" % (macro_id, r_type)
    response = memcache.get(key)
    if response: return response

    # Get parsed macro from id and begin response generation.
    response_dict = get_view_dict_from_macro_id(macro_id)
    
    # Call helper to interpret the macro behind the id.
    macro_obj = get_macro_obj_from_id(macro_id, response_dict['macro_input'])

    # Add macro, with or without errors.
    response_dict['interpret'] = _translate_parsed_macro(macro_obj),

    # Render to response type requested.
    if r_type == 'xml':
        response  = render_template('xml_response.template',
                                    response_dict,
                                    path)
    else: # json
        del response_dict['class_list']
        del response_dict['macro_input']
        response = simplejson.dumps(response_dict)
        
    # Add to memcached
    #memcache.add(key, response, MEMCACHED_API)  
    return response


# Internal method to translate an InterpretedMacro into a format for
# rendering into xml or JSON.
def _translate_parsed_macro(macro_obj):
    ''' Internal method to translate an InterpretedMacro into a format
    for rendering into xml or JSON.

    Returns a list of lists:

    macro         = [ [macro command]+ ]
    macro_command = [ [condition]?, [action] ]
    condition     = [ token+ ]
    action        = [ token+ ]
    token         = type, original, interpretaton, wowhead,
                    warnings, error

    '''

    URL_WOWHEAD_SPELL = """http://www.wowhead.com/?spell=%s"""
    URL_WOWHEAD_ITEM  = """http://www.wowhead.com/?item=%s"""
    ret    = []
    errors = []

    # Internal helper function to do utf8 compliance.
    def utf8(s):
        return s.encode('utf8')

    # Internal rendering function.
    # returns [[Type, Txt], Error]
    def render_tok(t):
        ''' Internal method to translate a Token into a format for
        rendering into xml or JSON.  Each token is represented as
        [type, original, interpretaton, wowhead, warnings, error].'''
        if not t: return []

        # Type
        tok = [t.get_token_type()]

        # Original token
        if not t.added:
            tok.append(t.data)
        else:
            tok.append('')

        # Interpretation
        tok.append(t.get_render_desc())

        # Wowhead
        if t.wowhead and t.found():
            if t.attrs.param_data_obj.is_spell():
                tok.append(URL_WOWHEAD_SPELL % (t.attrs.param_data_obj.get_id()))
            else:
                tok.append(URL_WOWHEAD_ITEM  % (t.attrs.param_data_obj.get_id()))
        else:
            tok.append('')

        # Warn/Error
        if t.warn:    tok.append(render_err_msg(t.warn))
        else:         tok.append('')
        if t.error:   tok.append(render_err_msg(t.error))
        else:         tok.append('')        

        # Encode and return
        #return map(utf8, tok)
        return tok

    def render_list(tok_list):
        if not tok_list: return []

        # Get the list of rendered tokens
        return map(render_tok, tok_list)
        
        
         
    # Iterate through the commands in the macro.
    for cmd in macro_obj:
        for if_do in cmd.interpret:
            ret.append(map(render_list, if_do))


    return ret


