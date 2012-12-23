'''
HTML Encoding and assorted tools
'''

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

# Length limit on tokens before we need to insert a break in a word.
TT_TOKEN_LIMIT          = 32
TOKEN_LIMIT             = 60
ERROR_TOKEN_LIMIT       = 25

# Helper to split a token
def split_token(s, p, j):
    return j.join([ s[i:i+p] for i in range(0,len(s),p) ])

# Helper to insert breaks into long words in a string
def insert_breaks(s, lim, b="<br>"):
    return ' '.join(map(lambda w: split_token(w, lim, b), s.split()))
