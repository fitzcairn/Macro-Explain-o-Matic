// Javascript code for automatic tooltips from Fitzcairn's Macro
// Explain-o-matic.  Requires util.js, win_lib.js and http_lib.js to
// be loaded.  Credit for ideas for library organization as well as
// using a request queue to help with response caching goes to
// mmochampion.com.

// Tooltip library
var mett_lib = {

    // Constructor, with style sheet.
    init: function(css) {
        // Prevent loading more than once.
        if (mett_lib.loaded) return;

        // Tooltip id, class, and style.
        var id         = "mett";
		var class_name = "mett-hover";
        var css        = "http://static.macroexplain.com/tooltip.css";

        // Get a hover handling library with reposition
        // on mousemove.
        mett_lib.hover = win_lib.get_hover_lib(id, class_name, css, true);

        // Currently active tooltip
        mett_lib.active_tooltip = null;

        // Go through the document and assign a handler to each
        // link with the appropiate class.  Root element is document.
        mett_lib.register_links(document);

        // Create the cache to prevent repeated calls and the
        // request queue.
        mett_lib.req_cache   = Object();
        mett_lib.req_queue   = Array();
        mett_lib.curr_req    = null;

        // Set up a callback to listen if this page has any elements
        // added to it.  If so, they need to be parsed for tooltips as
        // well.  Does not work in IE<=6--upgrade to a real browser
        // already!!
		if (typeof(document.addEventListener) == "function") {
            document.addEventListener('DOMNodeInserted',
                                      mett_lib.add_new_dom_node_tt,
                                      true);
        }
        
        // Load complete.
        mett_lib.loaded = true;
	},


    // Whether or not this is a link we want to create 
    // a tooltip for.  Returns the macro id.
	extract_tooltip_link: function(anchor) {
        var macro_id = "";

        // Two ways a link is valid as a tooltip.
        // First: href="[www.]?macroexplain.com/<id>"
		var url      = anchor.getAttribute("href") || "#";
		if (url.match(/^(http:\/\/)?(?:www\.)?macroexplain\.com\/m\S+$/)) {
            macro_id = url.split('/').pop();
        }
        
        // Second: rel="<id>"
        var rel      = anchor.getAttribute("rel") || "";
        if (rel.match(/^m\S+$/)) {
            macro_id = rel;
        }    
        return macro_id;
	},


    // Find tooltip links, and register handlers on them to show/move/hide
    // the tooltip.
	register_links: function(element) {
		if (typeof(element.getElementsByTagName) == "undefined") return false;

        // Iterate over all links under this element and process
        // those that require tooltips.
		var links = element.getElementsByTagName("a");
		for(var i = 0; i < links.length; i++) {
			if(mett_lib.extract_tooltip_link(links[i])) {
                // Register tooltip callbacks on link.  On link
                // mousover, make a http request for hover data and
                // show a hover.
				links[i].onmouseover = function(evt) { mett_lib.create_tooltip(this); }

                // On mouseout, simply hide hover.
				links[i].onmouseout  = function(evt) { mett_lib.hover.hide();         }
			}
		}
	},


    // Create a tooltip for this link
	create_tooltip: function(anchor) {
        // Register this tooltip as the active one
		mett_lib.active_tooltip    = anchor;

        // Prep the hover div.
        mett_lib.hover.anchor_hover();

        // Get the macro to fetch the interpretation for
        var macro_id = mett_lib.extract_tooltip_link(anchor);

        // Check cache.  On hit, render from cache.
        if (mett_lib.req_cache[macro_id]) {
            mett_lib.hover.render_hover(mett_lib.req_cache[macro_id]);
        }
        // Miss.  Issue request.
        else {
            // Problem: what if someone hovers over lots of links in
            // succession?  This means we need to queue up requests along
            // with their anchors for caching.
            req       = Object();
            req['id'] = macro_id;
            req['a']  = anchor;
            mett_lib.req_queue.push(req);
            mett_lib.process_requests();
        }
	},

    
    // Process a request from the queue.
    process_requests: function() {
		if (mett_lib.req_queue.length > 0 && !mett_lib.curr_req) {
			mett_lib.curr_req = mett_lib.req_queue.pop()
            // Dispatch the call.
            http_lib.get_request("/_tt?m=" + mett_lib.curr_req['id'],
                                 mett_lib.update_tooltip,
                                 mett_lib.update_tooltip_error);
		}        
    },

    
    // Update the current active tooltip with returned data,
    // and save the response in the cache.
    update_tooltip: function(tt_html) {
        // Cache results
        mett_lib.req_cache[mett_lib.curr_req['id']] = tt_html;
        
        // If this is still the active tt and we got something,
        // render.
        if (mett_lib.curr_req['a'] == mett_lib.active_tooltip) {
            // Render the tt
            mett_lib.hover.render_hover(tt_html);
        }
        
        // Done with the current request.
        mett_lib.curr_req = null;

        // Continue to process requests.
        mett_lib.process_requests();
    },


    // Handle error.
    update_tooltip_error: function() {
        // Continue to process requests.
        mett_lib.process_requests();
    },


    // Here to handle elements that are inserted into the page.
    // They will need toottips added to their links as well.
	add_new_dom_node_tt: function(event) {
        if (typeof(event.target) == "object")
            mett_lib.register_links(event.target);
	}
};

// Queue the init for this library to the document onload event.
add_onload_event(mett_lib.init);
