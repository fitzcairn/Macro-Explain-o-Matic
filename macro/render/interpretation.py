'''
Render token HTML.
'''

from macro.render.errors    import generate_token_warning, generate_token_error
from macro.render.encoding  import *

# Static variable to turn off JS for automated tests
TOKEN_JAVASCRIPT_INACTIVE = False

''' HTML constants'''
CMD_HTML                = "<font class='cmd'>%s</font>"
TT_CMD_HTML             = "%s"
TT_INTREPRETED_HTML     = "%s"
TT_INTERPRETED_CMD_HTML = "%s<br>&nbsp;&nbsp;%s"
INTERPRETED_CMD_HTML    = "%s<br>&nbsp;&nbsp;%s"
INTERPRETATION_SEP      = "<br><br>"
INTERPRETED_BAD_HTML    = "<i>%s</i>"


''' Html constants '''
# The common name parts for token styles.
TOKEN_CS_ON             = "token_hl_on"
TOKEN_CS_OFF            = "token_hl_off"


# More efficient to encode these here than read them in from files.
TOKEN_BASE_STYLE        = """<style type='text/css'><!-- .""" + TOKEN_CS_OFF + """-%s-%s { }--></style>"""
TOKEN_JS_STYLE          = """<style type='text/css'><!-- .""" + TOKEN_CS_ON + """-%s-%s { color: #212527; background-color:#6e777a; } .""" + TOKEN_CS_OFF + """-%s-%s { } --></style>"""
TOKEN_WOWHEAD_SPELL     = """<a class="wowhead" href="http://www.wowhead.com/?spell=%s">%s</a>"""
TOKEN_WOWHEAD_ITEM      = """<a class="wowhead" href="http://www.wowhead.com/?item=%s">%s</a>"""
TOKEN_PARAM_TT          = """<font class='tt_p'>%s</font>"""
TOKEN_BASE_SPAN         = """<font class='""" + TOKEN_CS_OFF + """-%s-%s'>%s</font>"""
TOKEN_BASE_SPAN_STRIKE  = """<font class='""" + TOKEN_CS_OFF + """-%s-%s' style='text-decoration: line-through;'>%s</font>"""
TOKEN_JS_SPAN           = """<span class='""" + TOKEN_CS_OFF + """-%s-%s'>%s</span>"""
TOKEN_JS_SPAN_STRIKE    = """<span class='""" + TOKEN_CS_OFF + """-%s-%s' style='text-decoration: line-through;'>%s</span>"""
TOKEN_JS_SPAN_HIGHLIGHT = """<span class='""" + TOKEN_CS_OFF + """-%s-%s' style='background-color: #FFF000;'>%s</span>"""


# Generate cleaned txt command
def generate_cmd_txt(cmd_token_list):
    rendered_list = []
    for t in token_list:
        rendered_list.append(t.data)
        if (is_cmd and (t.space_after or t.add_space_after)) or \
               t.render_space_after:
            rendered_list.append(' ')
    return ''.join(rendered_list)


# Generate html from the actual command string.
def generate_cmd_html(cmd_token_list, show_err=True, tt=False):
    ''' Given list of cmd tokens, render and return html.'''
    if tt:
        return TT_CMD_HTML % render_token_list(cmd_token_list, is_cmd=True, show_err=show_err, tt=True)        
    return CMD_HTML % render_token_list(cmd_token_list, is_cmd=True, show_err=show_err)


# Generate html from an interpretation object
def generate_interpret_html(interp_tuple_list, show_err=True, cmd_error=False, tt=False):
    ''' Given a list of ([if token list], [then token list]) tuples,
    render and return html.'''
    ret = []
    for if_list,do_list in interp_tuple_list:
        if tt:
            if if_list:
                ret.append(TT_INTERPRETED_CMD_HTML % \
                           tuple([render_token_list(if_list, show_err=show_err, tt=tt),
                                  render_token_list(do_list, show_err=show_err, tt=tt)]))
            else:
                ret.append(TT_INTREPRETED_HTML % (render_token_list(do_list, show_err=show_err, tt=tt)))
        else:
            if if_list:
                ret.append(INTERPRETED_CMD_HTML % \
                           tuple([render_token_list(if_list, show_err=show_err, tt=tt),
                                 render_token_list(do_list, show_err=show_err, tt=tt)]))
            else:
                ret.append(render_token_list(do_list, show_err=show_err, tt=tt))
    html = INTERPRETATION_SEP.join(ret)
    if cmd_error:
        return INTERPRETED_BAD_HTML % INTERPRETATION_SEP.join(ret)
    return html


# Given a list of tokens, render them into HTML.
def render_token_list(token_list, is_cmd=False, show_err=True, tt=False):
    '''Given a list of tokens, render them into HTML.
    The is_raw_cmd parameter indicates whether the cmd or
    the interpretation is being rendered.'''
    rendered_list = []
    for t in token_list:
        rendered_list.append(render_token_html(t, is_cmd, show_err, tt))
        if (is_cmd and (t.space_after or t.add_space_after)) or \
               t.render_space_after:
            rendered_list.append(' ')
    return ''.join(rendered_list)


# Markup a token into HTML
def render_token_html(t, is_cmd=False, show_err=True, tt=False):
    '''
    Given a token, generate HTML output (including javascript)
    for insertion in place of the token.

    Args:
      t      - Token
      is_cmd - Whether or not to render as cmd or interpretation.
      tt     - Render as tt text with minimal markup

    Returns:
      String of token html.
    '''
    html = []
    tok_str = t.data
    if not is_cmd: tok_str = t.get_render_desc()
    tok_str = escape(tok_str)

    # If we are rendering in tt mode (for tooltips), return
    # tt rendered token marked up for tt styling.
    if tt:
        # Break words in tokens on the TT limit.
        tok_str = insert_breaks(tok_str, TT_TOKEN_LIMIT)
        if t.is_param(): tok_str = TOKEN_PARAM_TT % (tok_str)
        return tok_str
    else:
        # Break words in tokens on the non-TT limit.
        tok_str = insert_breaks(tok_str, TOKEN_LIMIT)

    # First markup the text with t.wowhead links if requested
    if t.wowhead and t.found():
        if t.attrs.param_data_obj.is_spell():
            tok_str = TOKEN_WOWHEAD_SPELL % (t.attrs.param_data_obj.get_id(),
                                             tok_str)
        else:
            tok_str = TOKEN_WOWHEAD_ITEM  % (t.attrs.param_data_obj.get_id(),
                                             tok_str)
    # Next add the style and span.
    if t.js:
        html.append(TOKEN_JS_STYLE % (t.index, t.token_id,
                                        t.index, t.token_id))
        if t.strike:
            html.append(TOKEN_JS_SPAN_STRIKE % (t.index, t.token_id,
                                                    tok_str))
        elif t.highlight:
            html.append(TOKEN_JS_SPAN_HIGHLIGHT % (t.index, t.token_id,
                                                       tok_str))
        elif t.error:
            html.append(TOKEN_JS_SPAN_HIGHLIGHT % (t.index, t.token_id,
                                                       tok_str))
        else:
            html.append(TOKEN_JS_SPAN % (t.index, t.token_id,
                                           tok_str))
    else:
        if t.strike:
            html.append(TOKEN_BASE_SPAN_STRIKE % (t.index, t.token_id,
                                                    tok_str))
        else:
            html.append(TOKEN_BASE_SPAN % (t.index, t.token_id,
                                           tok_str))
    # Add the error spans.
    if show_err:
        if t.error:  html.append(generate_token_error(t))
        elif t.warn: html.append(generate_token_warning(t))

    # Return completed token html.
    return ''.join(html)
