$( document). ready( function(){
    function Editor(input, preview) {
        this .update = function () {
            preview.innerHTML = markdown.toHTML(input.value);
            $('code').each (function (i, e) {hljs.highlightBlock(e)});
            //$('code').addClass('mycode');
            $('input[name=content]').attr('value',$('#preview').html());
        };
        input.editor = this ;
        this .update ();
    }
    var getEle = function (id) { return document .getElementById (id); };
    new Editor(getEle ("text-input" ), getEle( "preview"));
});