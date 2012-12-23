// Javascript code for making AJAX calls to rate a macro,
// and then update the rating on the page.
// Requires http_lib, util to be loaded.


// Rating control library
var rate_lib = {
    // Constructor
    // The rater_obj is the div that selects rating,
    // while rating_obj is the div displays the rating.
    init: function(macro_id, rate_control_div, rate_control_id, rating_id) {
        // Can't save ratings without util/http_lib support.
        if (!self.http_lib || !self.get_el_pos) return true;

        rate_lib.rate_control_div     = document.getElementById(rate_control_div);
        rate_lib.timer                = null;
        rate_lib.rating               = 0; // Start with 0
        rate_lib.max_stars            = 5;
        rate_lib.rate_control_star_id = rate_control_id;
        rate_lib.rating_star_id       = rating_id;
        rate_lib.macro_id             = macro_id;

        // Preload on/off/voted/half images, in that order.
        rate_lib.images = new Array();
        rate_lib.images.push(new Image(12,12));
        rate_lib.images[0].src = "http://static.macroexplain.com/star_on.gif";
        rate_lib.images.push(new Image(12,12));
        rate_lib.images[1].src = "http://static.macroexplain.com/star_off.gif";
        rate_lib.images.push(new Image(12,12));
        rate_lib.images[2].src = "http://static.macroexplain.com/star_voted.gif";
        rate_lib.images.push(new Image(12,12));
        rate_lib.images[3].src = "http://static.macroexplain.com/star_half.gif";

        // Init the rate_control element.
        rate_lib.render_rate_control(rate_lib.rating);

        // Set a callback for mouseover--this is to light
        // up stars as we mouse over them, and stop as we
        // mouseout.
        rate_lib.rate_control_div.onmouseover = function (event_obj) {
            if (!event_obj) event_obj = window.event;
            rate_lib.handle_mouseover(event_obj);
        };
        rate_lib.rate_control_div.onmouseout = function (event_obj) {
            if (!event_obj) event_obj = window.event;
            rate_lib.handle_mouseout(event_obj);
        };

        // When the user clicks, determine the star we clicked on
        // and kick off the AJAX call.
        rate_lib.rate_control_div.onmouseup = function (event_obj) {
            if (!event_obj) event_obj = window.event;
            rate_lib.handle_mouseup(event_obj);
        };
    },


    // Helper Functions --->
    // Get the star mouse pointer is currently over.
    get_rating: function (event_obj) {
        // Determine element location at the time of the mousemove--
        // expensive, but something could have changed (font size, etc)
        // since the page was rendered, so we need to make sure we're
        // current. (NOTE: returns [x,y].)
        rate_control_pos = get_el_pos(rate_lib.rate_control_div);

        // Determine pointer location on the page.
        pointer = get_mouse_pos(event_obj);
    
        // Use above to figure out the number of stars we need to light
        // up, from 0-rate_lib.max_stars
        rel_pointer_x = pointer.x - rate_control_pos.x;
        num_stars = 0
        if (rel_pointer_x > 0) {
            num_stars = Math.ceil(rate_lib.max_stars * (rel_pointer_x / rate_lib.rate_control_div.offsetWidth))
        }
        return num_stars;
    },


    // Object Event Handlers --->
    // Mousemove
    handle_mousemove: function (event_obj) {
        // No rendering changes needed if we've rated already.
        if (rate_lib.rating > 0) { return; }

        // Render stars we're currently mousing over.
        rate_lib.render_rate_control(rate_lib.get_rating(event_obj));
    },


    // Mouseover
    handle_mouseover: function (event_obj) {
        // No rendering changes needed if we've rated already.
        if (rate_lib.rating > 0) { return; }

        // Register a mousemove handler for the duration of the time we're
        // over the control.  This will light up individual stars.
        rate_lib.rate_control_div.onmousemove = function (event_obj) {
            if (!event_obj) {
                event_obj = window.event;
            }
            rate_lib.handle_mousemove(event_obj);
        };
    },


    // Mouseout
    handle_mouseout: function (event_obj) {
        // No rendering changes needed if we've rated already.
        if (rate_lib.rating > 0) { return; }

        // De-register the mousemove handler.
        rate_lib.rate_control_div.onmousemove = null;

        // Clear all star render state.
        rate_lib.render_rate_control(0);
    },


    // Mouseup--kick off the asynch call.
    handle_mouseup: function (event_obj) {
        // No voting allowed if we've voted already
        if (rate_lib.rating > 0) { return; }

        // Figure out which star got clicked on.
        rate_lib.rating = rate_lib.get_rating(event_obj);

        // Freeze the rate_control widget.
        rate_lib.render_rate_control(rate_lib.rating);

        // Call into the saved rating provider with the display callback.
        // We do this by setting a function call in the future 300ms from
        // now.  This prevents rapid hits on our service for no
        // reason--i.e. doubleclicks.
        if (rate_lib.timer != null) {
            clearTimeout(rate_lib.timer);
        } 
        rate_lib.timer = setTimeout(rate_lib.timer_callback, 300);
    },


    // Rendering --->
    // Update the stars on the rate_control.
    render_rate_control: function (num_stars) {
        // If we've voted already, turn off widget.
        if (rate_lib.rating > 0) { num_stars = rate_lib.rating }

        // Render the user's selection in the rate_control div.
        for (var i=1; i <= rate_lib.max_stars; i++) {
            // Change source to reflect whether its on or off.
            star = document.getElementById(rate_lib.rate_control_star_id + i);
            if (i <= num_stars && i > 0) {
                if (rate_lib.rating > 0) {
                    star.src = rate_lib.images[2].src; // Voted
                }
                else {
                    star.src = rate_lib.images[0].src; // On
                }
            }
            else {
                star.src = rate_lib.images[1].src; // Off
            }
        }
    },


    // Update the rating on the page and the rating object.
    render_rating: function (new_rating) {
        // Render the user's selection in the rate_control div.
        for (var i=1; i <= rate_lib.max_stars; i++) {
            // Change source to reflect whether its on or off.
            star = document.getElementById(rate_lib.rating_star_id + i);
            if (i <= new_rating && i > 0) {
                star.src = rate_lib.images[0].src; // Full
            }
            else {
                // Is this a half star?
                if ((i - 0.5) == new_rating) {
                    star.src = rate_lib.images[3].src; // Half
                }
                else {
                    star.src = rate_lib.images[1].src; // Off
                }
            }
        }
    },


    // Callbacks --->
    // Timer callback to determine whether or not to do a rating.
    // Only do this if we have a rating to send.
    timer_callback: function () {
        // If we have a valid rating, call out to record it
        // via http_lib.
        if (rate_lib.rating > 0) {
            var url = "/_rate?m=" + escape(rate_lib.macro_id) + "&r=" + rate_lib.rating;
            http_lib.get_request(url,
                                 rate_lib.render_rating,
                                 null);
        }
    }

};

