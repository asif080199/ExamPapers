/* AJAX comments posting */
/* By Frankie - no change */
(function( $ ){
$.fn.bindPostCommentHandler = function() {
    // We get passed a list of forms; iterate and get a unique id for each
    // attach a submit trigger to handle saving and returning
    this.each(function() {
        //$(this).find('input.submit-preview').remove();
        $(this).submit(function() {
            commentform = this;
            commentwrap = $(this).parent();
            $.ajax({
                type: "POST",
                data: $(commentform).serialize(),
                url: $(commentform).attr('action'),
                cache: false,
                dataType: "html",
                success: function(html, textStatus) {
                    $(commentform).replaceWith(html);
                    $(commentwrap).hide();
                    $(commentwrap).slideDown(600);
                    $(commentwrap).find('form').bindPostCommentHandler();
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    $(commentform).replaceWith('Your comment was unable to be posted at this time.  We apologise for the inconvenience.');
                }
            });
            return false;
        });
    }); //each
};
})( jQuery );

(function( $ ){
$.fn.bindReplyButtonHandler = function() {
    // We get passed a list of buttons; iterate and set each to show the form (which was hidden)
    this.each(function() {
        $(this).click(function() {
            /* Show the form! */
            replybutton = this;
            replyform = "#" + $(replybutton).val();
            $(replyform).show();

            return false;
        });
    }); //each
};
})( jQuery );

$(function() {
    $('.comment-form form').bindPostCommentHandler();
    $('.comment-reply-btn').bindReplyButtonHandler();
});
