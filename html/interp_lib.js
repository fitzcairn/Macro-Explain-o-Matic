// Javascript for the macro interpretation itself.
// Requires util.js, win_lib.js to be loaded


// Control over interpretation library.
// Uses hover library to power errors, etc.
var interp_lib = {
    // Constructor
    init: function(interp_el_id, token_on_class, token_off_class, help_id) {
        interp_lib.tok_on  = token_on_class;
        interp_lib.tok_off = token_off_class;

        // Go through the spans on the page, and add
        // mouseover/mouseout to all the tokens with the JS
        // highlighting styles.
        var element = document.getElementById(interp_el_id); 
        if (!element) return;
        var spans   = element.getElementsByTagName("span");
        if (spans) {
            for(var i = 0; i < spans.length; i++) {
                if (spans[i].className.indexOf(token_on_class)  == 0 || 
                    spans[i].className.indexOf(token_off_class) == 0) {
                    // Register callbacks on span.
                    spans[i].onmouseover = function(evt) { interp_lib.token_on(this);  }
                    spans[i].onmouseout  = function(evt) { interp_lib.token_off(this); }
                }
            }
        }

        // Create hover objects.
        interp_lib.hovers                = Object();
        interp_lib.hovers['error-hover'] = win_lib.get_hover_lib('error-hover',
                                                                 'error-hover');
        interp_lib.hovers['warn-hover']  = win_lib.get_hover_lib('warn-hover',
                                                                 'warn-hover');
        interp_lib.hovers['help-hover']  = win_lib.get_hover_lib('help-hover',
                                                                 'help-hover');

        // Hover state
        interp_lib.active_hover          = Object();

        // Get the help HTML.
        var help_text = document.getElementById(help_id).innerHTML;

        // Register hover links
        interp_lib.register_hovers(element, 'i_error', 'error-hover', false, 10);
        interp_lib.register_hovers(element, 'i_warn',  'warn-hover',  false, 10);
        interp_lib.register_hovers(element, 'i_help',  'help-hover',  false, 5, help_text);
    },

    
    // Remove/Add error <sup> tags.
    remove_error_tags: function(tag) {
        if (!tag) { tag = 'sup'; }
        var sups = document.getElementsByTagName(tag);
        for(var i=0; i < sups.length; i++) {
            sups[i].style.display = "none";
        }
        // Swap links, show "ON"
        document.getElementById('error_on').style.display = "none"; 
        document.getElementById('error_off').style.display = "inline"; 
    },
    add_error_tags: function(tag) {
        if (!tag) { tag = 'sup'; }
        var sups = document.getElementsByTagName('sup');
        for(var i=0; i < sups.length; i++) {
            sups[i].style.display = "";
        }
        // Swap links, show "OFF"
        document.getElementById('error_on').style.display = "inline"; 
        document.getElementById('error_off').style.display = "none"; 
    },


    // Register error/warning popups for an interpretation.
	register_hovers: function(element, h_class, id, onclick, distance, txt_override) {
		if (typeof(element.getElementsByTagName) == "undefined") return false;

        // Set state--no hovers on.
        interp_lib.active_hover[id] = null;

        // Iterate over all links under this element and process
        // those that require tooltips.
		var els = element.getElementsByTagName('a');
		for(var i = 0; i < els.length; i++) {
			if(els[i].className == h_class) {
                // Register tooltip callbacks on el.
                if (onclick) {
                    // Click on/off.
                    els[i].onclick     = function(evt) { interp_lib.click_hover(this, id, evt, txt_override); }
                }
                else {
                    els[i].onmouseover = function(evt) { interp_lib.show_hover(this, id, evt, distance, txt_override); }
                    // On mouseout, simply hide hover.
                    els[i].onmouseout  = function(evt) { interp_lib.hovers[id].hide();    }
                }
            }
		}
	},

    
    // Turn on/off
    click_hover: function(anchor, id, event_obj, txt_override) {
        // Hover already on--turn off.
        if (interp_lib.active_hover[id] == anchor) {
            interp_lib.hovers[id].hide();
            interp_lib.active_hover[id] = null;
        }
        else {
            interp_lib.active_hover[id] = anchor;
            interp_lib.show_hover(anchor, id, event_obj, txt_override);
        }
    },


    // Popup handlers for hovers.
    show_hover: function(anchor, id, event_obj, distance, txt_override) {
        // Get the mouse position and set it in the window object.
        pos = get_el_pos(anchor);
        interp_lib.hovers[id].set_anchor_pos(pos);

        // Get text to display, by default the anchor rel text.
        var txt = anchor.rel;
        if (txt_override) txt = txt_override;

        // Render, def 10 px offset
        interp_lib.hovers[id].render_hover(txt, distance);
    },


    // Mouse event handlers for cross-span highlighting.
    token_on: function(token) {
        interp_lib._change_tokens_style(token.className, interp_lib.tok_off, interp_lib.tok_on);
    },
    token_off: function(token) {
        // Get the id of the token we rolled off
        interp_lib._change_tokens_style(token.className, interp_lib.tok_on, interp_lib.tok_off);
    },


    // Internal helper: change token style to do highlighting.
    _change_tokens_style: function(token_id, from_style, to_style) {
        // Regexp replace the from_style in the token_id to the to_style.
        var old_token_id = token_id;
        var new_token_id = token_id.replace(from_style, to_style);
        
        // Iterate through the spans and highlight everything that
        // shares this it tuple.
        var token_list = document.getElementsByTagName('span');
        for(var i=0; i < token_list.length; i++) {
            if (token_list[i].className == old_token_id) {
                token_list[i].className =  new_token_id;
            }
        }
    }
};

