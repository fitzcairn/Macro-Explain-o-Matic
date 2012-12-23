'''
Warning/Error HTML
'''

from macro.render.encoding   import *

''' Error strings '''
DEF_ERROR        = """ Whoops! %s"""

TOKEN_ERROR_SPAN = """<a class='i_error' href='#' rel='%s' onclick='return false;'><sup class='error'>!</sup></a>"""
TOKEN_WARN_SPAN  = """<a class='i_warn' href='#' rel='%s' onclick='return false;'><sup class='warn'>?</sup></a>"""


def generate_init_error_html(error_list):
    if len(error_list) == 0: return ''
    return "<br>".join(error_list)


def generate_token_warning(token):
    return TOKEN_WARN_SPAN % (render_err_msg(token.warn))


def generate_token_error(token):
    return TOKEN_ERROR_SPAN % (render_err_msg(token.error))


# Helper function to render the msg.
def render_err_msg(msg_tuple):
    msg  = msg_tuple[0]
    if len(msg_tuple) > 1:
        toks = map(lambda e_list: \
                   ' '.join([escape(insert_breaks(t.get_error_desc(),
                                                  ERROR_TOKEN_LIMIT,
                                                  '-'))
                             for t in e_list]),
                   msg_tuple[1:])
        return msg % tuple(toks)
    else:
        msg = escape(msg)
    return msg
