// Form library handline field-specific actions.
// Requires prior inclusion of util.js.

// Library to handle the main interpretation input form
var in_lib = {

    // Constructor
    init: function(form_id, field_id, msg_span_id, count_span_id) {
        // Can't update counts without util.js
        if (!self.update_count) return true;

        // Set library variables
        in_lib.field         = document.getElementById(field_id);
        in_lib.form          = document.getElementById(form_id);
        in_lib.msg_span      = document.getElementById(msg_span_id);
        in_lib.count_span    = document.getElementById(count_span_id);

        // Set handlers for input field
        in_lib.field.onfocus = in_lib.on_focus;
        in_lib.field.onblur  = in_lib.on_blur;
        in_lib.field.onkeyup = in_lib.on_keyup;

        // Set handlers for form
        in_lib.form.onsubmit = in_lib.on_submit;

        // Intro message
        in_lib.intro_text    = "Type or paste your World of Warcraft macro here.";
        in_lib.intro_shown   = false;

        // Warning limit for chars
        in_lib.warn_limit    = 255;
        in_lib.warn_msg      = "Warning: macro length exceeds default UI limit.  This macro will require an add-on to execute.";
        in_lib.msg_span.innerHTML = '';

        // Count message
        in_lib.count_start   = "You have ";
        in_lib.count_end     = " characters remaining out of the macro limit of " + in_lib.warn_limit;

        // Set up intro and warning text
        in_lib.on_blur();
        in_lib.on_keyup();
    },
    

    // On focus, clear intro text
    on_focus: function() {
        var field = in_lib.field;
        // If the field contains the intro text, clear it and change
        // the field style.
        if (field.value == in_lib.intro_text) {
            field.style.color="#2d3234";
            field.value="";
            in_lib.intro_shown = false;
        }
    },


    // On blur, add intro text
    on_blur: function() {
        var field = in_lib.field;
        // If the field is empty, add the intro text back in and change
        // the field style.
        if (field.value == "") {
            field.style.color="#4c5355";
            field.value = in_lib.intro_text;
            in_lib.intro_shown = true;
        }
    },


    // Make sure there is something in a field before allowing submit.
    on_submit: function() {
        var field = in_lib.field;
        if (field.value == '' || field.value == in_lib.intro_text) {
            return false;
        }
        return true;
    },


    // Handle character limits for the input form.
    on_keyup: function() {
        // Only do count if the contents aren't the intro txt.
        if (in_lib.intro_shown) {
            in_lib.count_span.innerHTML = in_lib.count_start +
                                          in_lib.warn_limit  +
                                          in_lib.count_end;
        }
        // Update count field.
        else {
            update_count(in_lib.field, in_lib.warn_limit, 
                         in_lib.count_span, in_lib.count_start,
                         in_lib.count_end);
        }

        // Set warnings.
        if (in_lib.field.value.length > in_lib.warn_limit) {
            in_lib.msg_span.innerHTML = in_lib.warn_msg;
        }
        else {
            in_lib.msg_span.innerHTML = '';
        }
    }
};



// Library for the save form.
var save_lib = {

    // Constructor
    init: function(form_id, class_img_class, field_id, count_span_id, char_limit) {
        // Can't update counts without util.js
        if (!self.update_count) return true;

        // Set library variables
        save_lib.field         = document.getElementById(field_id);
        save_lib.form          = document.getElementById(form_id); 
        save_lib.count_span    = document.getElementById(count_span_id);

        // Set handlers for notes field
        save_lib.field.onfocus = save_lib.on_focus;
        save_lib.field.onblur  = save_lib.on_blur;
        save_lib.field.onkeyup = save_lib.on_keyup;

        // Set handlers for form
        save_lib.form.onsubmit = save_lib.on_submit;

        // Intro message for notes
        save_lib.intro_text    = "Type or paste a short macro description here.";
        save_lib.intro_shown   = false;

        // Count message
        save_lib.limit         = char_limit;
        save_lib.count_start   = "You have ";
        save_lib.count_end     = " characters remaining out of " + save_lib.limit + ".";

        // Set up intro and warning text
        save_lib.on_blur();
        save_lib.on_keyup();

        // Where the images live.
        // For now, this is local, but soon will be moved
        // to an image server.
        save_lib.img_url = "http://static.macroexplain.com/";

        // Current class list
        save_lib.class_list= ['Death_Knight',
                              'Druid',
                              'Hunter',
                              'Mage',
                              'Paladin',
                              'Priest',
                              'Rogue',
                              'Shaman',
                              'Warlock',
                              'Warrior'];
        
        // sel:  Checked images end in "_checked.png" 
        // over: Mouseover images end in "_over.png"
        // reg:  Regular images end in ".png"z
        save_lib.img_types = {sel:  "_checked.png",
                              over: "_over.png",
                              reg:  ".png"}

        // Image ids end in a postfix
        save_lib.id_pf = "_i";

        // Preload images.
        var types = [save_lib.img_types.sel, save_lib.img_types.over, save_lib.img_types.reg];
		for(var i = 0; i < save_lib.class_list.length; i++) {
            for(var j = 0; j < types.length; j++) {
                var img = new Image(28,28);
                img.src = save_lib.img_url + save_lib.class_list[i] + types[j];
                var test = img.src;
            }
        }

        // Set up handlers for image swapping for the class selection
        // images.
        save_lib.imgs = new Array();
		var imgs = save_lib.form.getElementsByTagName("img");
		for(var i = 0; i < imgs.length; i++) {
            if (imgs[i].className == class_img_class) {
                save_lib.imgs.push(imgs[i]);

                // Register callbacks on img.
				imgs[i].onmouseover = function(evt) { save_lib.swap_img(this);     }
				imgs[i].onmouseout  = function(evt) { save_lib.swap_img(this);     }
				imgs[i].onclick     = function(evt) { save_lib.swap_and_set(this); }
			}
		}        
    },


    // Class Selector --->
    // Select all the classes in the save form.
    select_all_img: function() {
        // Go through all the classes and mark each as
        // selected (if not already).
        for (i = 0; i < save_lib.class_list.length; i++) {
            field = document.getElementById(save_lib.class_list[i]);
            if (field.value == 0) {
                var img = document.getElementById(save_lib.class_list[i] + 
                                                  save_lib.id_pf);
                save_lib.swap_and_set(img);
            }
        }
    },
    

    // Clear all classes selected
    clear_all_img: function () {
        // If there's something in the field already, append.
        for (i = 0; i < save_lib.imgs.length; i++) {
            var c_n     = save_lib.imgs[i].alt;
            var field   = document.getElementById(c_n);

            // Set img to regular, and clear field.
            save_lib.imgs[i].src = save_lib.img_url + c_n + save_lib.img_types.reg;
            field.value = 0;
        }
    },


    // Mousclick handler.
    // Swap class images and set the corresponding form value.
    swap_and_set: function(img) {
        var c_n   = img.alt;
        var field = document.getElementById(c_n);
        
        // Swap field value, which is either 0/1, and image to on/off
        if (field.value == 0) {
            field.value = 1;
            img.src = save_lib.img_url + c_n + save_lib.img_types.sel;
        }
        else {
            field.value = 0;
            img.src = save_lib.img_url + c_n + save_lib.img_types.over;
        }
    },
    

    // Mouseover handler: class image swap.
    swap_img: function(img) {
        var c_n   = img.alt;

        // If this image is selected already, do nothing.
        // Otherwise, do mouseover image swapping.
        if (img.src.search(save_lib.img_types.sel) < 0) {  
            // If the mousover image is on, swap back to normal.
            // Else, swap to mouseover
            if (img.src.search(save_lib.img_types.over) > 0) {
                img.src = save_lib.img_url + c_n + save_lib.img_types.reg;
            }
            else {
                img.src = save_lib.img_url + c_n + save_lib.img_types.over;
            }
        }
    },

 
    // Show the optional fields
    show_opt: function(field_show, field_hide) {
        document.getElementById(field_show).style.display = "block";
        document.getElementById(field_hide).style.display = "none";
    },


    // Hide optional fields
    hide_opt: function(field_show, field_hide) {
        document.getElementById(field_show).style.display = "none";
        document.getElementById(field_hide).style.display = "block";
    },


    // Clear field
    clear_field: function(field_name) {
        var field = document.getElementById(field_name);
        field.value = "";
    },

    
    // Insert a tag into a field
    add_tag: function(field_name, input) {
        var field = document.getElementById(field_name);
        
        // If there's something in the field already, append.
        if (field.value.match(/\S/)) {
            field.value += "," + input;
        }
        else {
            field.value = input;
        }
    },


    // Handlers for the notes field -->
    // On focus, clear intro text
    on_focus: function() {
        var field = save_lib.field;
        // If the field contains the intro text, clear it and change
        // the field style.
        if (field.value == save_lib.intro_text) {
            field.style.color="#2d3234";
            field.value="";
            save_lib.intro_shown = false;
        }
    },


    // On blur, add intro text
    on_blur: function() {
        var field = save_lib.field;
        // If the field is empty, add the intro text back in and change
        // the field style.
        if (field.value == "") {
            field.style.color="#4c5355";
            field.value = save_lib.intro_text;
            save_lib.intro_shown = true;
        }
    },


    // Handle character limits for the input form.
    on_keyup: function() {
        // Only do count if the contents aren't the intro txt.
        if (save_lib.intro_shown) {
            save_lib.count_span.innerHTML = save_lib.count_start +
                                            save_lib.limit  +
                                            save_lib.count_end;
        } 
        // Update count field.
        else {
            update_count(save_lib.field, save_lib.limit, 
                         save_lib.count_span, save_lib.count_start,
                         save_lib.count_end);
        }
    },


    // Don't allow the notes field toh have the intro text.
    on_submit: function() {
        if (save_lib.field.value == save_lib.intro_text) {
            save_lib.field.value = '';
        }
        return true;
    }
};

