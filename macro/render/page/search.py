'''
Collection of shared tools for appengine page rendering.
'''

# My modules
from macro.render.defs                import *
from macro.render.util                import render_template
from macro.data.appengine.savedmacro  import SavedMacroOps

# Generate a search results page.
def generate_search_page(path, terms, page, sort, page_size=DEF_SEARCH_RESULTS):
    '''
    Generate a search results page.
    '''
    error = None

    # Make sure page is a number, failing on bad input
    prev_page = None
    if not page:
        page = 1
    else:
        page = int(page)
        prev_page = page - 1
        
    # Do the search
    # TODO: Add column sort
    results = []
    is_next_page = False
    if (len(terms) < SINGLE_TAG_MAX_LENGTH):
        (results, is_next_page) = SavedMacroOps.search(terms, page=page, num=page_size, sort=sort)
    else:
        error = "Query term too long."
        terms = terms[:SINGLE_TAG_MAX_LENGTH] + "..."

    # If the number of results is less than that of page_size,
    # then there is no next page.
    next_page = None
    if is_next_page: next_page = page + 1

    # If there are no results, add an error.
    if not error and len(results) == 0:
        error = "No results found."

    # TODO: Hook up template controls to sort results.
    # TODO: Hook up template controls to page forward/back.
    
    # Return generated search page.
    return render_template('base.template',
                            {'query'  : terms,
                             'content': render_template('search.template',
                                                        {'search_error'    : error,
                                                         'curr_version'    : "%s.%s.%s" % (MAJOR_VERSION,
                                                                                           MINOR_VERSION,
                                                                                           PATCH_VERSION),
                                                         
                                                         'query'      : terms,
                                                         'q_esc'      : FORM_QUERY_ESC,
                                                         'results'    : results,
                                                         'sort'       : sort,
                                                          'page_var'   : FORM_SEARCH_PAGE,
                                                         
                                                         # Only give a prev page if we're over page 1.
                                                         'prev_page'  : prev_page,
                                                         'page'       : page,
                                                         'next_page'  : next_page,
                                                         },
                                                        path)},
                           path)


