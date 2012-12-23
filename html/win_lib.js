// Javascript code for hovers from Fitzcairn's Macro Explain-o-matic.
// Requires util.js to be loaded.


// Use a factory pattern to return a window object for each type of
// window required.
function win_lib() {
}

// Get a hovering library object.
// Library supports windows that can follow the cursor or
// are statically positioned.  If cursor movements are required,
// then the last argument must be 'true'.
win_lib.get_hover_lib = function(id, class_name, css_url, follow_mouse) {
    // Make sure we've loaded the libraries we need, or
    // otherwise we can't do anything.
    if (!self.add_mousemove_handler) return null;

    // Create the obj and style it if necessary
    var lib = new win_hover_lib(id, class_name);
    if (css_url) lib.set_default_style(css_url);
    
    // Start hovers hidden
    lib.hide();

    // If mouse repositioning (follow the mouse) is required,
    // register a mousemove callback.  Uses util.js.
    if (follow_mouse)
        //document.onmousemove = function(e) { lib.mouse_move(lib, e); };
        add_mousemove_handler(function(e) { lib.mouse_move(lib, e); });

    return lib;
};
    

// Mouseover windowing library constructor.
function win_hover_lib(id, class_name) {
    // Mouse positions
    this.x_pos = 0;
    this.y_pos = 0;

    // Create the hover div
    var js_box = document.createElement("div");
    js_box.id = id;
    js_box.className = class_name;
    document.getElementsByTagName("body")[0].appendChild(js_box);
    this.js_box = js_box;
}


// Load the hover stylesheet if we don't have one.
win_hover_lib.prototype.set_default_style = function(def_css_file) {
    var el = this.js_box;

    // Check for zIndex--need this defined by definition
    // if we're to "hover".
    z = get_rendered_style(el, "z-index");
    if (z != "auto" && z > 0) return;
    
    // Load the library hover stylesheet
    load_external_file(def_css_file, 'css');
};


// Event handler for mouse movements.  Saves the current mouse
// position, adjusts hovers.
win_hover_lib.prototype.mouse_move = function(scope_obj, event_obj) {
    var cursor = get_mouse_pos(event_obj);
    scope_obj.set_anchor_pos(cursor);
    if (scope_obj.js_box.style.visibility != "hidden") {
        scope_obj.position_hover();
    }
};


// Accessor to set mouse position.  Takes an object with .x/.y
// properties.
win_hover_lib.prototype.set_anchor_pos = function(pos) {
    this.y_pos = pos.y;
    this.x_pos = pos.x;
};


// Anchor hover, prep.
win_hover_lib.prototype.anchor_hover = function() {
    this.js_box.style.left = "0px";
    this.js_box.style.top  = "0px";
    this.js_box.innerHTML  = "Loading, please wait. . .";
};


// Render a hover
win_hover_lib.prototype.render_hover = function(html, offset) {
    // Render the tt if we have html
    if (html)
        this.js_box.innerHTML = html;
    
    // Position and show the hover
    this.position_hover(offset);
    this.show();
};


// Position the hover.  Disallow the hover to go off the edge of the
// browser window due to scrolling or other positioning.
// Uses functions defined in util.js
win_hover_lib.prototype.position_hover = function(offset) {
    var box           = this.js_box;
    var x             = this.x_pos;
    var y             = this.y_pos;
    var root          = document.documentElement;
    var body          = document.body;
    var scroll_offset = get_scroll_xy();
    var win_dim       = get_win_xy();
    
    // Box offset from mouse cursor--default is 20px
    if (isNaN(offset))
        offset        = 20;
 
    // Default position: above and to the right.
    var ax            = x + offset;
    var ay            = y - offset - box.offsetHeight;
    
    // Handle running into the top of the screen
    if (ay < scroll_offset.y) {
        swap_ay = y + offset;
        // Degenerate case: no room to display the box.
        if (win_dim.y < box.offsetHeight) {
            // No change to position, allow to float off screen.
        }
        // No room on bottom, but room between bottom and top.
        else if (swap_ay + box.offsetHeight > scroll_offset.y + win_dim.y) {
            ay = scroll_offset.y + win_dim.y - box.offsetHeight;
        }
        else {
            ay = swap_ay;
        }
    }
    // Handle running into the right of the screen
    if (ax + box.offsetWidth > scroll_offset.x + win_dim.x) {
        swap_ax = x - box.offsetWidth - offset;
        // Degenerate case: no room to display the box.
        if (win_dim.x < box.offsetWidth) {
            // No change to position, allow to float off screen.
        }
        // No room on left, but room between left and right
        else if (swap_ax < scroll_offset.x) {
            ax = scroll_offset.x;
        }
        else {
            ax = swap_ax;
        }
    }
    box.style.left = "" + (ax) + "px";
    box.style.top = "" + (ay) + "px";
};


// Show the hover.
win_hover_lib.prototype.show = function() {
    this.js_box.style.visibility = "visible";
};


// Hide the hover and de-register it.
win_hover_lib.prototype.hide = function() {
    this.js_box.style.visibility = "hidden"
};



