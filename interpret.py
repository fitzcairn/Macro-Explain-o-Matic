'''
Main GAE script for Fitzcairns Macro Interpreter.
'''

import re
import os
import cgi
import urllib
import logging
from google.appengine.ext             import webapp
from google.appengine.ext.webapp      import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api             import mail

# Get some Django tools
from django.core.validators           import email_re

# Get macro appengine components
from macro.render.defs                import *
from macro.render.encoding            import unescape
from macro.render.util                import get_form_error,translate_classmap,throttle_action
from macro.exceptions                 import NoInputError,OtherError
from macro.util                       import valid
from macro.data.appengine.savedmacro  import SavedMacroOps, encode_text, decode_text
from macro.render.page.interpret      import generate_view_page,generate_edit_page
from macro.render.page.error          import generate_error_page


# Save the template path from this CGI
_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__),
                             'templates')

class MacroView(webapp.RequestHandler):
    '''
    Handles view of already saved macro.
    '''

    # Helper to get the macro id.
    def get_macro_id(self):
        return str(self.request.path[1:]);

    # Helper to render a view page.
    def __render_view_page(self, output={}):
        # Get the macro page, catching exceptions
        try:
            page = generate_view_page(_TEMPLATE_PATH,
                                      self.get_macro_id(),
                                      self.request.host_url,
                                      output)
        except NoInputError, inst:
            page = generate_error_page(_TEMPLATE_PATH, error=inst)
        except Exception, inst:
            logging.error(inst)
            page = generate_error_page(_TEMPLATE_PATH, error="Your macro was not found.  Please double check the URL.")
        self.response.out.write(page)


    # Decode incoming links.
    def get(self):
        '''
        Handle encoded links.
        '''
        # Make sure the request is encoded.
        self.request.encoding = "UTF-8"

        # Get the macro page, catching exceptions
        self.__render_view_page()
        

    # Send this macro via email.
    def post(self):
        '''
        Handle encoded links.
        '''
        # Make sure the request is encoded.
        self.request.encoding = "UTF-8"

        # Create a link to this macro.
        macro_link = '%s/%s' % (self.request.host_url,
                                self.get_macro_id())
                
        # Get user input.
        field_vals = {}
        field_vals['msg'] = None
        
        # Are we sending an email?
        if self.request.get(FORM_MACRO_EMAIL, default_value=None):
            # To is required -- TODO: VALIDATE EMAIL!
            field_vals['to_addr'] = self.request.get(FORM_EMAIL_TO, default_value="")
            if not field_vals['to_addr']:
                field_vals['msg'] = "Need an email address to send to."
                if not email_re.search(field_vals['to_addr']):
                    field_vals['msg'] = "The email address entered was invalid."

            # From is optional.
            field_vals['from_name'] = self.request.get(FORM_EMAIL_FROM,
                                                                                                 default_value="a fellow WoW player")

            # Use memcached to throttle people to sending one macro every 10
            # seconds--only check if there are no errors already
            if field_vals['msg'] is None:
                secs_left = throttle_action("email", self.request.remote_addr)
                if secs_left > 0:
                    field_vals['msg'] = "You must wait %s seconds before you may send this macro again." % (secs_left)

            # If there were no errors, send.
            if field_vals['msg'] is None:
                mail.send_mail(sender=MACRO_EMAIL_REPLY_ADDRESS,
                               to=field_vals['to_addr'],
                               subject=MACRO_EMAIL_SUBJECT,
                               body=MACRO_EMAIL_BODY % \
                               ({'from': field_vals['from_name'],
                                 'link': macro_link}),
                               )
                # Clear input for next send, and tell user success.
                field_vals = {}
                field_vals['msg'] = "Macro sent successfully!"                

        # Get the macro page, catching exceptions
        self.__render_view_page(field_vals)


class MacroProcess(webapp.RequestHandler):
    '''
    Handles web UI for macro interpretation.
    '''

    # Just display normal UI, unless a macro id is passed.
    def get(self):
        '''
        Display interpret page.  If a macro id is passed, will load
        macro for editing.
        '''
        # Make sure the request is encoded.
        self.request.encoding = "UTF-8"

        # Was there a macro?
        macro = self.request.get(GET_MACRO_EXPLAIN)
        if macro:
            # Return rendered page.
            return self.__render_edit_page(m=macro)

        # Get the macro id, if there is one, and write out the page.
        return self.__render_edit_page(m_id=self.request.get(GET_MACRO_LINK))
    

    # Macro interpret requests.
    def post(self):
        '''
        Form input from the macro interpreter.
        '''
        # Make sure the request is decoded correctly.
        self.request.encoding = "UTF-8"

        # Get the macro, decode into unicode
        macro = self.request.get(FORM_MACRO_INPUT)
        return self.__render_edit_page(m=macro)


    # Render a macro for remote interpreters
    def __render_remote_interp_page(self, macro, response='xml'):
        self.response.out.write(generate_remote_interpretation(_TEMPLATE_PATH, macro, response))


    # Helper to simplify generating an edit page.
    def __render_edit_page(self, m=None, m_id=None):
        # Generate the page and write it out.
        try:
            self.response.out.write(generate_edit_page(_TEMPLATE_PATH, macro=m, macro_id=m_id))
        except OtherError, inst:
            logging.error("Macro: %s\nError: %s" % (m, inst))
            self.response.out.write(generate_error_page(_TEMPLATE_PATH, m, str(inst)))
        except Exception, inst:
            logging.error("Macro: %s\nError: %s" % (m, inst))
            self.response.out.write(generate_error_page(_TEMPLATE_PATH, m))


            
# Seperate handler for link generation.
class MacroSave(webapp.RequestHandler):
    '''
    Handles saving a macro
    '''
    def get(self):
        # Redirect to the intepreter.
        return self.redirect("/")
    

    def post(self):
        '''
        Form input from the macro save.
        '''
        page = None
        
        # Make sure the request is encoded correctly.
        self.request.encoding = "UTF-8"
        enc_macro = self.request.get(FORM_MACRO_INPUT)

        # Did we get an html-encoded macro--i.e. from a save error?
        if self.request.get(FORM_MACRO_ESC):  
            # Yes, unescape it.
            enc_macro = unescape(enc_macro)

        # Call to a helper to simplify exception handling.
        try:
            # If we did not get a valid macro, then this page has issues.
            macro     = decode_text(enc_macro)

            if not valid(macro):
                raise NoInputError("Attempt to save an empty macro.")
            else:
                page = self.__render_form_page(macro)
        except OtherError, inst:
            logging.error("Macro: %s\nError: %s" % (macro, inst))
            page = generate_error_page(_TEMPLATE_PATH, macro, str(inst))
        except Exception, inst:
            logging.error("Macro: %s\nError: %s" % (macro, inst))
            page = generate_error_page(_TEMPLATE_PATH, macro)            

        # Write out response
        if page:
            self.response.out.write(page)


    # Helper function to simplify exception handling.
    def __render_form_page(self, macro):
        # Validate form errors and save
        form_errors = {}
        opt_fields    = {
            'title_show': 'none',
            'title_hide': 'block',
            'notes_show': 'none',
            'notes_hide': 'block',
            }
            
        # Title is optional.
        title  = self.request.get(FORM_SAVE_TITLE, default_value="")[0:TITLE_MAX_LENGTH]

        # Author is optional.
        name   = self.request.get(FORM_SAVE_NAME, default_value="")[0:NAME_MAX_LENGTH]
        
        # Server is optional.
        server = self.request.get(FORM_SAVE_SERVER, default_value="")[0:SERVER_MAX_LENGTH]

        # Notes are optional
        notes  = self.request.get(FORM_SAVE_NOTES, default_value="")[0:NOTES_TEXT_LENGTH]

        # Update optional field status
        if valid(title) or valid(name) or valid(server):
            opt_fields['title_show'] = "block"
            opt_fields['title_hide'] = "none"
        if valid(notes):
            opt_fields['notes_show'] = "block"
            opt_fields['notes_hide'] = "none"        

        # Version defaults to current version.
        version = "%s.%s.%s" % (MAJOR_VERSION,
                                MINOR_VERSION,
                                PATCH_VERSION)
        
        # Must have at least one class, and all must be recognized.
        classes = []
        for c in CLASS_LIST:
            if self.request.get(c.replace(" ", "_")) == '1': classes.append(c)
        if len(classes) == 0:
            form_errors['class_error'] = get_form_error(FORM_SAVE_CLASSES)

        # Must have at least one tag, and all must be recognized.
        # De-dup tags via a set.
        tags = list(set([t for t in re.split("\s*,\s*",
                                             self.request.get(FORM_SAVE_TAGS)) if t]))
        if len(tags) == 0:
            form_errors['tag_error'] = get_form_error(FORM_SAVE_TAGS)
        else:
            if len(self.request.get(FORM_SAVE_TAGS)) > ALL_TAGS_MAX_LENGTH:
                form_errors['tag_error'] = "Too many tags!"
            else:
                longest_tag = max(tags, key=len)
                if len(longest_tag) > SINGLE_TAG_MAX_LENGTH:
                    form_errors['tag_error'] = "Tag %s exceeds the max tag length of %s chars!" % (longest_tag, SINGLE_TAG_MAX_LENGTH)

        # Use memcached to throttle people to saving one macro every 10
        # seconds.    Only do this AFTER the user has fixed errors.
        if len(form_errors) == 0:
            secs_left = throttle_action("save", self.request.remote_addr)
            if secs_left > 0:
                form_errors['spam'] = "You must wait %s seconds before you may save another macro." % (secs_left)

        # Were there any errors?    If success, save and redirect
        if len(form_errors) == 0:
            # Return an error page if something really wrong happens.
            link = None
            link = SavedMacroOps.save_macro(macro, cgi.escape(notes), title, name, classes, tags, version, server)
            # Redirect to the intepreter with the link.
            self.redirect("/%s" % link)

        # Error in validation--display.
        else:
            # Create template data based on input.
            input_vals = {
                'title_data'      : title,
                'name_data'       : name,
                'macro_notes'     : notes,
                'curr_version'    : version,
                'note_limit'      : NOTES_TEXT_LENGTH,
                'note_ch_left'    : NOTES_TEXT_LENGTH - len(notes),
                'class_list'      : translate_classmap(sel=set(classes)),
                # Server list lives in a template.
                'server_list'     : template.render(os.path.join(_TEMPLATE_PATH,
                                                                 'servers.template'),
                                                    {}),
                'tag_def_list'    : TAG_LIST,
                'selected_server' : server,
                'tag_list'        : ",".join(tags),
                }
            # Add in errors.
            input_vals.update(form_errors)

            # Add in optional field status.
            input_vals.update(opt_fields)
            
            # Write out the page
            return generate_edit_page(_TEMPLATE_PATH,
                                      macro,
                                      save_values=input_vals)
          

''' Register handlers for WSCGI. '''
application = webapp.WSGIApplication(
    [(URL_MACRO_PROCESS, MacroProcess),
     (URL_MACRO_VIEW,    MacroView),
     (URL_SAVE_PROCESS,  MacroSave),
     ],
    debug=True)


def real_main():
    run_wsgi_app(application)

def profile_main():
    # This is the main function for profiling 
    # We've renamed our original main() above to real_main()
    import cProfile, pstats
    prof = cProfile.Profile()
    prof = prof.runctx("real_main()", globals(), locals())
    print "<pre style='color: GRAY;'>"
    stats = pstats.Stats(prof)
    stats.sort_stats("time")    # Or cumulative
    stats.print_stats(80)    # 80 = how many to print
    # The rest is optional.
    # stats.print_callees()
    # stats.print_callers()
    print "</pre>"

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    if DO_PROFILE: profile_main()
    else: real_main()

