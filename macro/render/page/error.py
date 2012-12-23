'''
Render an error page
'''
from macro.render.util                import render_template

# Generate an error page.
def generate_error_page(path, macro=None, error=None):
    '''
    Generate an error page.
    '''

    # Create the error string
    macro_str = ""
    error_str = ""
    if macro: macro_str = macro
    if error: error_str = error

    # Return generated error page.
    return render_template('base.template',
                            {'content': render_template('error.template',
                                                        {'input': macro_str,
                                                         'error': error_str},
                                                        path)},
                           path)



    
