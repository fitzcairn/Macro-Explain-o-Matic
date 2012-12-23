// Javascript code for handling asyncronous http callbacks for 
// Fitzcairn's Macro Explain-o-matic.



// HTTP callback library
var http_lib = {

    // Constructor, creates XMLHttp request object.
    init: function () {
        http_lib.request_obj   = false;
        http_lib.callback_obj  = false;
        http_lib.request_obj   = false;
        try {
            http_lib.request_obj = new XMLHttpRequest();
        } catch (trymicrosoft) {
            try {
                http_lib.request_obj = new ActiveXObject("Msxml2.XMLHTTP");
            } catch (othermicrosoft) {
                try {
                    http_lib.request_obj = new ActiveXObject("Microsoft.XMLHTTP");
                } catch (failed) {
                    http_lib.request_obj = false;
                }
            }
        }
    },
    

    // Make a request via GET.
    //   url        -- Request url, including parameters
    //   cb_success -- Function to call back on success.
    //   cb_failure -- Function to call back on failure.
    get_request: function (url, cb_success, cb_failure) {
        // Only do this if we init'd ok.
        if (http_lib.request_obj) {
            http_lib.url        = url;
            http_lib.cb_success = cb_success;
            http_lib.cb_failure = cb_failure;
            http_lib._do_asynch_get();
        }
        else {
            try      { cb_failure(null); }
            catch(e) {}
        }
    },


    // Do a asynchronous call to the suggestion provider
    _do_asynch_get: function () {
        http_lib.request_obj.open("GET", http_lib.url, true);
        http_lib.request_obj.onreadystatechange = http_lib._process_update;
        http_lib.request_obj.send(null);
    },    


    // AJAX call returned; process information.
    _process_update: function () {
        // If successful, return results of call.
        if (http_lib.request_obj.readyState == 4 && http_lib.request_obj.status == 200) {
            if (!http_lib.cb_success) {
                // Not init'd correctly, ignore.
            }
            else {
                http_lib.cb_success(http_lib.request_obj.responseText);
            }
        }
        // Otherwise, return fail.
        else {
            try {
                if (http_lib.request_obj.status != 200)
                    http_lib.cb_failure(null);
            }
            catch(e) {}
        }
    }    
};

// Queue the init for this library to the document onload event.
add_onload_event(http_lib.init);

