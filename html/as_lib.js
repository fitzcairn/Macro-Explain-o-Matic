// Javascript code for auto-suggesting on a search box.
// Based on a tutorial by Nicholas C. Zakas, albiet
// modified heavily to generate suggestions via AJAX calls
// and a few other changes to avoid service DDOS.
// Requires util and http_lib to be loaded.


// Search autosuggest library
var as_lib = {

    // Init for this object.  Must be called from the page wanting
    // suggestions with the search box suggestions should be inserted
    // into as the arg.
    init: function (form_id, text_box_id) {
        // Can't offer suggestions without util/http_lib support.
        if (!self.http_lib || !self.get_el_pos) return true;

        as_lib.help      = "Search macros by tag";
        as_lib.form      = document.getElementById(form_id);
        as_lib.textbox   = document.getElementById(text_box_id);
        as_lib.layer     = null;
        as_lib.curr      = -1;
        as_lib.prefix    = "";
        as_lib.timer     = null;

        var control_obj  = as_lib;
    
        // Init with help message
        as_lib.setup_help();

        // Set a callback to catch keyup events on the textbox.
        as_lib.textbox.onkeyup = function (event_obj) {
            // Handle differences between browsers--IE stores the event as
            // a window event.
            if (!event_obj) {
                event_obj = window.event;
            }
            control_obj.handle_key_up(event_obj);
        };

        // Setup a callback to catch keydown events, for highlighting.
        as_lib.textbox.onkeydown = function (event_obj) {
            if (!event_obj) {
                event_obj = window.event;
            }
            control_obj.handle_key_down(event_obj);
        };

        // When we lose focus, hide the dropdown and restore the help 
        // text.
        as_lib.textbox.onblur = function () {
            control_obj.hide_dropdown();
            control_obj.setup_help();
        };

        // On focus, clear ONLY the help text
        as_lib.textbox.onfocus = function () {
            if (control_obj.textbox.value == control_obj.help) {
                control_obj.setup_input();
            }       
        };
        
        // On form submit, check the input.
        as_lib.form.onsubmit = as_lib.check_input;

        as_lib.create_dropdown();
    },


    // Check contents of control before running a search
    check_input: function () {
        if (as_lib.textbox.value.trim() != "" && 
            as_lib.textbox.value != as_lib.help) {
            return true;
        
        }
        return false;
    },


    // Object Event Handlers --->
    // Keyup
    handle_key_up: function (event_obj) {
        var control_obj = as_lib;
        var key_code    = event_obj.keyCode;
        var prefix      = as_lib.textbox.value

        // 32 is space, > 46 is non-alphanumberic, etc, 112-123 are
        // function keys.  Backspace is 8 and delete 46
        if (key_code < 8 || (key_code >= 9 && key_code < 32) || (key_code >= 33 && key_code < 46) || (key_code >= 112 && key_code <= 123)) {
            //ignore
        }
        else {
            // Something happened we care about, hide the dropdown
            // so we can regenerate it.
            as_lib.hide_dropdown();

            // If we have a value in the textbox. . .
            if (prefix.length > 0) {
                // Call into the saved suggestion provider with the the
                // display callback.  We do this by setting a function call in
                // the future 500ms from now.  This prevents rapid hits on
                // our service for no reason.
                if (as_lib.timer != null) {
                    clearTimeout(as_lib.timer);
                } 
                as_lib.timer = setTimeout(control_obj.timer_callback, 300);
            }
        }
    },


    // Keydown--modify which item is selected in the list.
    handle_key_down: function (event_obj) {
        // Only do this if we actually have a dropdown shown.
        if (as_lib.layer.style.visibility == "hidden") {
            return;
        }
        switch(event_obj.keyCode) {
            case 38: //up arrow
            as_lib.highlight_prev_suggestion();
            break;
            case 40: //down arrow
            as_lib.highlight_next_suggestion();
            break;
            case 13: //enter
            as_lib.hide_dropdown();
            break;
        }
    },


    // Positioning functions -->
    // Get the top/left of text box.
    // TODO: I think there are better ways to do this.
    get_pos: function (is_top) {
        var node = as_lib.textbox;
        var pos = 0;
        while(node.tagName != "BODY") {
            if (is_top) { pos += node.offsetTop; }
            else        { pos += node.offsetLeft; }
            node = node.offsetParent;
        }
        return pos;
    },
    get_left_pos: function () {
        return as_lib.get_pos(false);
    },
    get_top_pos: function () {
        return as_lib.get_pos(true);
    },


    // Rendering functions -->
    // Set text color/style in the textbox
    setup_input: function() {
        as_lib.textbox.style.color = "#2d3234";
        as_lib.textbox.value = "";
    },

    setup_help: function() {
        if (as_lib.textbox.value.trim() == "") {
            as_lib.textbox.style.color = "#4c5355";
            as_lib.textbox.value = as_lib.help;
        }
    },


    // Create the dropdown and add it to the page.
    create_dropdown: function () {
        as_lib.layer                  = document.createElement("div");
        as_lib.layer.className        = "suggestions";
        as_lib.layer.style.visibility = "hidden";
        document.body.appendChild(as_lib.layer);

        // Assign mouse event handlers to the new layer.
        var control_obj = as_lib;
        as_lib.layer.onmousedown = as_lib.layer.onmouseup =
        as_lib.layer.onmouseover = function (event_obj) {
            event_obj = event_obj || window.event;
            target_obj = event_obj.target || event_obj.srcElement;

            if (event_obj.type == "mousedown") {
                // Submit as_lib search
                control_obj.textbox.value = target_obj.firstChild.nodeValue;
                control_obj.hide_dropdown();
            }
            else if (event_obj.type == "mouseover") {
                control_obj.highlight_suggestion(target_obj);
            }
            else {
                control_obj.textbox.focus();
            }
        };

    },


    // Show the dropdown.
    show_dropdown: function (suggestion_list) {
        var div_obj = null;
        as_lib.layer.innerHTML = "";
        as_lib.curr = -1;

        // Construct the div from the suggestions
        for (var i=0; i < suggestion_list.length; i++) {
            div_obj = document.createElement("div");
            div_obj.appendChild(document.createTextNode(suggestion_list[i]));
            as_lib.layer.appendChild(div_obj);
        }

        // Position the div
        top_space = 1;
        pos = get_el_pos(as_lib.textbox);
        as_lib.layer.style.left = pos.x + "px";
        as_lib.layer.style.top  = pos.y + (as_lib.textbox.offsetHeight +
                                           top_space) + "px";
        as_lib.layer.style.visibility = "visible";
    },


    // Hide the dropdown
    hide_dropdown: function () {
        as_lib.layer.style.visibility = "hidden";
        as_lib.curr = -1;
    },


    // Highlight a suggestion inside of the dropdown.
    highlight_suggestion: function (node_obj) {
        // Clear all suggestions except the first one.
        for (var i=0; i < as_lib.layer.childNodes.length; i++) {
            var node = as_lib.layer.childNodes[i];
            if (node == node_obj) {
                node.className = "current";
            } else if (node.className == "current") {
                node.className = "";
            }
        }
    },


    // Handle keyboard highlighting.
    highlight_next_suggestion: function () {
        var node_list = as_lib.layer.childNodes;

        // Highlight the next suggestion, advancing the cur position.
        if (node_list.length > 0 && as_lib.curr < node_list.length-1) {
            var node = node_list[++as_lib.curr];
            as_lib.highlight_suggestion(node);
            as_lib.textbox.value = node.firstChild.nodeValue;
        }
    },
    highlight_prev_suggestion: function () {
        var node_list = as_lib.layer.childNodes;

        // Highlight the previous suggestion
        if (node_list.length > 0 && as_lib.curr > 0) {
            var node = node_list[--as_lib.curr];
            as_lib.highlight_suggestion(node);
            as_lib.textbox.value = node.firstChild.nodeValue;
        }
    },


    // Callbacks -->
    // Timer callback to determine whether or not to offer a suggestion.
    // Only do this if we have a new prefix and we don't have a prefix
    // highlighted.
    timer_callback: function () {
        var prefix   = as_lib.textbox.value
        // If we have a different (and valid) prefix, refresh the
        // suggestions via http_lib.
        if (prefix != as_lib.prefix && prefix.trim().length > 0 && as_lib.curr < 0) {
            as_lib.prefix = prefix.trim();
            var url = "/_ta?q=" + escape(as_lib.prefix);
            http_lib.get_request(url,
                                 as_lib.display_callback,
                                 null);
        }
    },


    // The autosuggest function, which selects which suggestion to display
    // from a list of suggestions
    display_callback: function (response) {
        var suggestion_list = new Array()
        if (response.length > 0) {
            suggestion_list = response.split(',');
        }
        if (suggestion_list.length > 0) {
            // Render the suggestions into a display
            as_lib.show_dropdown(suggestion_list);
        }
        else {
            as_lib.hide_dropdown();
        }
    }
};

