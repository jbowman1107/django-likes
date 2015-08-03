if (typeof $ != 'undefined') {

    $(document).ready(function(){

        $(document).on('click', 'a.liker', function(event){
            event.preventDefault();
            var el = $(this);
            var replace_selector = el.attr('replace_selector');

            var replace_target = replace_selector
                ? $(replace_selector)
                : el.parents('.likes:first');

            $.get(el.attr('href'), {}, function(data){
                replace_target.html(data);
            });

        });
    })
}