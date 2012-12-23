// Shared library functions for 
// Fitzcairn's Macro Explain-o-matic.


// A great function to get CSS properties set in external style
// sheets.  Credit:
// http://robertnyman.com/2006/04/24/get-the-rendered-style-of-an-element/
function get_rendered_style(elm, css_rule_str){
	var str_val = "";
	if(document.defaultView && document.defaultView.getComputedStyle){
		str_val = document.defaultView.getComputedStyle(elm, "").getPropertyValue(css_rule_str);
	}
	else if(elm.currentStyle){
        // Catch errors for unsupported browsers (IE <= 5.0)
        try {
            css_rule_str = css_rule_str.replace(/\-(\w)/g,
                                                function (strMatch, p1) {
                                                    return p1.toUpperCase();
                                                });
            str_val = elm.currentStyle[css_rule_str];
        }
        catch(e) { /* In this case, return "" */ }
	}
	return str_val;
}


// A nice multi-onload handler solution for window onload events.
// Uses nested functions to stack onload handlers.  Credit:
// http://www.webreference.com/programming/javascript/onloads/
function add_onload_event (func) { 
    var oldonload = window.onload; 
    if (typeof window.onload != 'function') { 
	    window.onload = func; 
    } else { 
	    window.onload = function() { 
            if (oldonload) { 
                oldonload(); 
            } 
            func(); 
	    } 
    } 
} 


// Similar function for having muliple handlers registered
// for mouse moving events.
function add_mousemove_handler (func) {
    var old_handler  = document.onmousemove;
    if (typeof old_handler != 'function') { 
	    document.onmousemove = func; 
    } else { 
	    document.onmousemove = function(e) { 
            if (old_handler) { 
                old_handler(e); 
            } 
            func(e); 
	    } 
    } 
}


// Helper function to get the current XY scrolling offset.
function get_scroll_xy() {
    var scroll_offset = {x:0, y:0};
    var body = document.body;
    var root = document.documentElement;
    if(typeof(window.pageYOffset) == 'number') {
        // Netscape compliant
        scroll_offset.y = window.pageYOffset;
        scroll_offset.x = window.pageXOffset;
    }
    else if(body && (body.scrollLeft || body.scrollTop)) {
        // DOM compliant
        scroll_offset.y = body.scrollTop;
        scroll_offset.x = body.scrollLeft;
    }
    else if(root && (root.scrollLeft || root.scrollTop)) {
        // IE6 standards compliant mode
        scroll_offset.y = root.scrollTop;
        scroll_offset.x = root.scrollLeft;
    }
    return scroll_offset;
}

// Helper function to get the current size of the browser window.
function get_win_xy() {
    var dim = {x: 0, y: 0};
    var body = document.body;
    var root = document.documentElement;
    if( typeof( window.innerWidth ) == 'number' ) {
        // Non-IE
        dim.x = window.innerWidth;
        dim.y = window.innerHeight;
    } else if( root && ( root.clientWidth || root.clientHeight ) ) {
        // IE 6+ in 'standards compliant mode'
        dim.x = root.clientWidth;
        dim.y = root.clientHeight;
    } else if( body && ( body.clientWidth || body.clientHeight ) ) {
        // IE 4 compatible
        dim.x = body.clientWidth;
        dim.y = body.clientHeight;
    }
    return dim;
}


// Get mouse position in IE and Firefox
// Returns a variable with x and y properties
function get_mouse_pos(e) {
  var cursor = {x: 0, y: 0};
  if (!e) e = window.event;
  if (e.pageX || e.pageY){
    cursor.x = e.pageX;
    cursor.y = e.pageY;
  }
  else if (e.clientX || e.clientY){
      cursor.x = e.clientX + document.body.scrollLeft +
                 document.documentElement.scrollLeft;
      cursor.y = e.clientY + document.body.scrollTop +
                 document.documentElement.scrollTop;
  }
  return cursor;
}


// Get the position of an element.
function get_el_pos(obj) {
    var pos = {x: 0, y: 0};
    if (obj.offsetParent) {
        pos.x = obj.offsetLeft
            pos.y = obj.offsetTop
            while (obj = obj.offsetParent) {
                pos.x += obj.offsetLeft
                pos.y += obj.offsetTop
            }
    }
    return pos;
}


// Update a message span with the count of chars in a input field.
function update_count(field, char_limit, msg_span, msg_start, msg_end) {
    var rem   = char_limit - field.value.length;
    if (rem < 0) rem = 0;
    msg_span.innerHTML = msg_start + rem + msg_end;
}


// Simple function to select text in a div
function select_text(div_id) {
  var text = document.getElementById(div_id);

  // Non-IE
  if (window.getSelection) {
    var selection = window.getSelection();

    // Safari
    if (selection.setBaseAndExtent) {
      selection.setBaseAndExtent(text, 0, text, text.innerHTML.length-1);
    }
    // Firefox, Opera
    else {
      var range = document.createRange();
      range.selectNodeContents(text);
      selection.removeAllRanges();
      selection.addRange(range);
    }
  }
  // IE
  else {
    var range = document.body.createTextRange();
    range.moveToElementText(text);
    range.select();
  }
}


// Define trim for all strings
String.prototype.trim = function () {
    return this.replace(/^\s*/, "").replace(/\s*$/, "");
}

