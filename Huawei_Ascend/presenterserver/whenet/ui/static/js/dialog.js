var dialog = (function Dialog() {
    var $mask = $("<div id='dlg-mask'></div>");

    //title--
    //content--object{type[1 for input, 0 for text], text[display in content]}
    //btnFlag--1 for OK+Cancel, 0 for OK
    function initHtml(title, content, btnFlag, ok, cancel) {
        var div = "";
        div += "<div id='dlg-box' class='dot'>";
        div += "<h1 class='dot' style=\"margin-bottom:5px\">" + title + "</h1>"
        div += "<div style=\"width:100%;height:1px;background-color:#ccc;\"></div>";
        if (content.type == 0) {
            div += "<p>" + content.text + "</p>"
        } else if (content.type == 1) {
            div += "<input type='text' value='" + content.text + "' placeholder='" + content.placeholder + "' autocomplete='off'/>";
        }
        if (btnFlag == 0) {
            div += "<div><span class='ok'>OK</span></div>";
        } else if (btnFlag == 1) {
            div += "<div><span class='ok'>OK</span><span class='cancel'>Cancel</span></div>";
        }
        div += "</div>";
        $mask.html(div);
        $mask.find("input").val($mask.find("input").val());
        if (content.type == 1) {
            $mask.find(".ok").on("click", function() {
                var retText = $mask.find("input").val();
                hide();
                if (ok) {
                    ok(retText);
                }
            });
            $mask.find(".cancel").on("click", function() {
                var retText = $mask.find("input").val();
                hide();
                if (cancel) {
                    cancel(retText);
                }
            });
        } else {
            $mask.find(".ok").on("click", function() {
                hide();
                if (ok) {
                    ok();
                }
            });
            $mask.find(".cancel").on("click", function() {
                hide();
                if (cancel) {
                    cancel();
                }
            });
        }
    }

    function calcBoxPos() {
        var $box = $mask.find("#dlg-box");
        var mask_w = $mask.outerWidth();
        var mask_h = $mask.outerHeight();
        var box_w = $box.outerWidth();
        var box_h = $box.outerHeight();
        var pos_left = (mask_w - box_w) / 2 + "px";
        var pos_top = (mask_h - box_h) / 2 + "px";
        $box.css("left", pos_left).css("top", pos_top);
    }

    function show() {
        $("body").prepend($mask);
        $mask.css("display", "block");
        if ($mask.find("input") && $mask.find("input")[0]) {
            $mask.find("input")[0].focus();
        }
        calcBoxPos();
        $(window).resize(calcBoxPos);
    }

    function hide() {
        $mask.css("display", "none");
        $mask.remove();
    }

    return {
        hide: hide,
        tip: function(title, text, ok) {
            initHtml(title, { type: 0, text: text }, 0, ok, null);
            show();
        },
        input: function(title, text, placeholder, ok, cancel) {
            initHtml(title, { type: 1, text: text, placeholder: placeholder }, 1, ok, cancel);
            show();
        },
        confirm: function(title, text, ok, cancel) {
            initHtml(title, { type: 0, text: text }, 1, ok, cancel);
            show();
        }
    }
})();