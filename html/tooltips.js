// Tooltip library for Fitzcairn's Macro Explain-o-matic.
// Written 5/2010 by Fitzcairn of Sisters of Elune US
// Feel free to copy, dissect, or otherwise reuse this code.


// A multi-onload handler solution for window onload events.  Uses
// nested functions to stack onload handlers.  From util.js, repeated
// here so IE/Chrome/Safari don't have to wait for util.js to load.
function add_onload_event (func) {
    //alert("loading: " + func);
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


// Load an external file via constructing a head link.  Some pretty
// terrible hacks here to get around the problem of knowing when an
// external javascript file is "done" loading.
function load_external_file(url, type, init_func){
    // JS
    if (type.toLowerCase() == "js") {
        var js = document.createElement('script');
        js.setAttribute("type","text/javascript");
        js.setAttribute("src", url);
        document.getElementsByTagName("head")[0].appendChild(js);
        if (init_func) {
            // for Safari/Chrome
            if (/WebKit/i.test(navigator.userAgent)) { // sniff
                js.onload = function () {
                    if (!js.onloadone) {
                        js.onloadone = true;
                        eval(init_func);
                    }
                }
            }
            else {
                // For IE--init library once loaded.
                js.onreadystatechange = function () {
                    if (js.readyState == 'complete' ||
                        js.readyState == 'loaded') {
                        if (!js.onloadone) {                    
                            js.onloadone = true;
                            eval(init_func);
                        }
                    }
                }
                // For Opera 9/Firefox
                if (document.addEventListener) {
                    if (!js.onloadone) {
                        try {
                            // Opera
                            document.addEventListener("DOMContentLoaded",
                                                      init_func,
                                                      false);
                        }
                        catch(e) {
                            // Firefox
                            js.onload = function () {
                                eval(init_func);
                            }
                        }
                        js.onloadone = true;
                    }
                }
            }
        }
    }
    // CSS
    else if (type.toLowerCase() == "css") {
        var css = document.createElement("link");
        css.setAttribute("rel", "stylesheet");
        css.setAttribute("type", "text/css");
        css.setAttribute("href", url);
        document.getElementsByTagName("head")[0].appendChild(css);
    }
}

// Static file url
var static_url = "http://static.macroexplain.com";

// Load tooltip css
load_external_file(static_url + "/tooltip.css", "css");
// Load util js library
load_external_file(static_url + "/util.js", "js");
// Load http js library
load_external_file(static_url + "/http_lib.js", "js", "http_lib.init()");
// Load windowing js library
load_external_file(static_url + "/win_lib.js", "js");
// Load tooltip js library
load_external_file(static_url + "/mett_lib.js", "js", "mett_lib.init()");



