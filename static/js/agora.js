(function ($) {
    // Handle showing the login popup
    var handleLoginLink = function () {
        var loginLink = $('.login-link');

        if (loginLink.length) {
            loginLink.click(function () {
                $('#login-popup').show();

                return false;
            });

            $('#login-popup').click(function (event) {
                // Only catch events in the outer, overlay div
                if (event.target === this) {
                    $(this).hide();
                }
            });
        }
    };

    // jQuery plugin for selecting text
    $.fn.selectText = function () {
        var element = this[0];
        var range, selection;

        if (document.body.createTextRange) {
            range = document.body.createTextRange();
            range.moveToElementText(element);
            range.select();
        } else if (window.getSelection) {
            selection = window.getSelection();
            range = document.createRange();
            range.selectNodeContents(element);
            selection.removeAllRanges();
            selection.addRange(range);
        }
    };

    $.fn.ShowCommentForm = function(id){
            $(this).hide();
            $('#' + id).show();
        };

    $(document).ready(function () {
        handleLoginLink();

        // Add in the line numbers (no JS fallback unfortunately)
        if ($('.snippet').length) {
            var counter = 1;
            var lineNumbers = [];

            var lines = $('.code-lines').children();

            for (var i = 0, numLines = lines.length; i < numLines; i++) {
                var line = lines[i];
                // Set the top offset to be the same as that of the line
                var div = '<p style="top: ' + line.offsetTop + 'px">' +
                    '<a href="#l' + counter + '">' + counter + '</a></p>';
                counter++;
                lineNumbers.push(div);
            }

            $('.line-counters').append(lineNumbers.join(''));
        }

        // Highlight the code when the link is clicked
        $('.highlight-code-lines').click(function () {
            $('.code-lines').selectText();

            return false;
        });

        // Changing syntax highlighting colours
        var currentStyle = $('#change-highlighting').attr('data-default');
        $('#change-highlighting').change(function () {
            var newStyle = $(this).find(':selected').attr('data-name');

            $('.snippet').removeClass(currentStyle).addClass(newStyle);
            currentStyle = newStyle;
        });
    });
    $("input[name=Rate]").change(function()
    {
        $("#rate_form").submit();
    });
}
)(jQuery);