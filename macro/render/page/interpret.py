'''
Rendering for view and interpret pages.
'''

import urllib
from google.appengine.api import memcache

# My modules
from macro.render.defs                import *
from macro.render.util                import escape, translate_classmap, render_template, get_macro_obj_from_id, render_macro, get_view_dict_from_macro_id
from macro.util                       import valid, NULL_POSITION
from macro.exceptions                 import NoInputError
from macro.data.appengine.savedmacro  import SavedMacroOps

# Generate a macro view page.
def generate_view_page(path, macro_id, host_url, save_values={}):
    '''
    Generate a macro view page. Returns None on error.
    Propogates exceptions up.
    '''
    ret_page = None

    # Make sure we got valid input.
    if not macro_id: raise NoInputError("You entered an invalid macro ID.  Try again?")

    # Ensure we have a saved macro.  Will throw exception on fail.
    saved_macro = SavedMacroOps(macro_id)

    # View pages are extremely heavy, and the majority of their
    # data doesn't change.  Use helper to handle this.
    macro_form_template_values = get_view_dict_from_macro_id(macro_id, saved_macro)

    # Add in edit and view links.
    # Add in the author link.
    # Add in the form ids.
    page_values = {'macro_link'      : '%s/%s'    % (host_url,
                                                    macro_id),
                   'macro_edit'      : '%s?%s=%s' % (host_url,
                                                     GET_MACRO_LINK,
                                                     macro_id),
                   'author'          : _format_author(saved_macro.entity.name,
                                                      saved_macro.entity.server),
                   'send_email'      : FORM_MACRO_EMAIL,
                   'send_input_form' : FORM_EMAIL_INPUT,
                   'to'              : FORM_EMAIL_TO,
                   'from'            : FORM_EMAIL_FROM,
                   }
    macro_form_template_values.update(page_values)
    
    # Generate the dynamic parts of the page:
    #   1. Increment the view counter on this macro.
    #   2. Get the rating in terms of stars for this macro.
    dynamic_page_vals = {
        'stars'           : [i + 1 for i in range(MAX_RATING)],
        'num_rates'       : saved_macro.entity.num_rates,
        'views'           : saved_macro.add_to_view_count(),
        'rating'          : saved_macro.get_rating_dict(saved_macro.get_rating()),
        }
    macro_form_template_values.update(dynamic_page_vals)
    
    # Is this another save attempt after errors?  If so, update
    # with errors and previous values.
    macro_form_template_values.update(save_values)

    # Call helper to interpret the macro behind the id.
    macro_obj = get_macro_obj_from_id(macro_id, saved_macro.entity.macro)

    # Populate the templace with the processed macro.
    macro_form_template_values['processed_macro_html'] = \
         render_macro(macro_obj, path)

    # Get the copy and paste form of the macro
    macro_form_template_values['copy_paste'] = \
        _render_copy_cmd(macro_obj)

    # Render the macro view template html.
    ret_page  = render_template('view.template',
                                macro_form_template_values,
                                path)
    return render_template('base.template',
                           {'content':  ret_page},
                           path)


# Genereate the edit macro page.
def generate_edit_page(path, macro=None, save_values={}, macro_id=None):
    '''
    Generate edit page via template.  Exceptions propogated upwards.
    Propogates exceptions up.
    '''
    # Two parts to this page: macro form and link form.
    macro_form_html       = ''
    macro_link_html       = ''

    # Start filling in the macro form template
    macro_form_template_values = {
        'intro_text'      : FORM_MACRO_INPUT_HELP,
        'macro_process':    URL_MACRO_PROCESS,
        'macro_input_form': FORM_MACRO_INPUT,}
    
    # If we got a macro_id, attempt to get the macro from it.
    macro_obj = None
    if valid(macro_id):
        macro_obj = get_macro_obj_from_id(macro_id)
        macro     = macro_obj.macro
    elif valid(macro):
        # Import big modules locally to avoid unneccesary work.
        from macro.interpret.interpreter import MacroInterpreter
        macro_obj = MacroInterpreter().interpret_macro(macro)

     # If we got a good macro, display its interpretation
    if valid(macro):
        # Add the macro to the form.
        if macro_obj.macro_changed:
            macro_form_template_values['macro'] = _render_clean_cmd(macro_obj)
            macro_form_template_values['changed'] = MACRO_CHANGED
        else:
            macro_form_template_values['macro'] = macro

        # Grab the templates for both the interpretation and the
        # processed macro, and populate them.
        macro_form_template_values['processed_macro_html'] = \
           render_macro(macro_obj, path)
        
        # If we have a valid macro that we could try saving,
        # generate form.  Also, only do this if we didn't come
        # directly from a view--no need to re-save a macro.
        if macro_obj.macro_good and not macro_id:
            macro_unesc = _render_clean_cmd(macro_obj)
            macro_esc   = escape(macro_unesc)
            macro_link_template_values = {
                'title_show'      : "none",
                'title_hide'      : "block",
                'notes_show'      : "none",
                'notes_hide'      : "block",
                'link_process'    : URL_SAVE_PROCESS,
                'macro_input_form': FORM_MACRO_INPUT,
                'macro'           : macro_unesc,
                'macro_esc'       : macro_esc,
                'macro_is_esc '   : FORM_MACRO_ESC,
                'title'           : FORM_SAVE_TITLE,
                'name'            : FORM_SAVE_NAME,
                'notes'           : FORM_SAVE_NOTES,
                'server'          : FORM_SAVE_SERVER,
                'classes'         : FORM_SAVE_CLASSES,
                'tags'            : FORM_SAVE_TAGS,
                'note_limit'      : NOTES_TEXT_LENGTH,
                'note_ch_left'    : NOTES_TEXT_LENGTH,
                'class_list'      : translate_classmap(),
                'tag_def_list'    : TAG_LIST,
                'tag_list'        : '',
                'server_list'     : render_template('servers.template', path=path),
                'selected_server' : '',
                'curr_version'    : "%s.%s.%s" % (MAJOR_VERSION,
                                                  MINOR_VERSION,
                                                  PATCH_VERSION),
                }
            
            # Is this another save attempt after errors?  If so, update
            # with errors and previous values.
            macro_link_template_values.update(save_values)

            # Render the template.
            macro_link_html = render_template('save_form.template',
                                              macro_link_template_values,
                                              path)
    
    # Add in the link html.
    macro_form_template_values['macro_link_html'] = \
           macro_link_html

    # Render the macro form template html.
    ret_page  = render_template('macro_form.template',
                                macro_form_template_values,
                                path)

    return render_template('base.template',
                           {'content': ret_page },
                           path)


#
# Internal Functions
#

# Format the author name for display
def _format_author(name, server):
    '''Create an armory-linked author name.'''
    # If there is no server, just return name.
    if server == "": return name
    locale,server_name = server.split("-")
    locale      = locale.lower()
    server_name = server_name.replace(" ", "-").lower()
    return ARMORY_LINK % (locale, server_name, urllib.quote(name.encode("utf-8")), escape(name))


# Render a copy/paste version of the macro.
def _render_copy_cmd(macro_obj):
    # Render the macro lines
    return '<br>'.join([c.cmd_str for c in macro_obj])


# Render the cleaned command string.
def _render_clean_cmd(macro_obj):
    # Render the macro lines
    return '\r\n'.join([c.cmd_str for c in macro_obj])

    
