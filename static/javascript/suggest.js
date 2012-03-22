getSuggestDiv = function() {
    return document.getElementById('search_suggest');
};
renderResult = function(resultXml) {
    return '<span onclick="suggestClick(' + resultXml.getAttribute('id') + ')">how ' + 
            resultXml.getAttribute('x_name') + ' affects ' + resultXml.getAttribute('y_name') +
            ' (' + resultXml.getAttribute('votes') + ')</span>';
};
updateSuggest = function(xmldata) {
    var suggDiv = getSuggestDiv();
    var dataElements = xmldata.getElementsByTagName('result')
    var html = '';
    for (var i = 0; i < dataElements.length; i++) {
        if (i != 0) html = html + '<br />';
        html = html + renderResult(dataElements[i]);
    }
    getSuggestDiv().innerHTML = html;
    displaySuggestions(true);
};
displaySuggestions = function(show) {
    var change = function() {
        getSuggestDiv().style['display'] = show ? 'block' : 'none';
    };
    if (show) {
        change();
    } else {
        window.setTimeout(change, 300);
    }
};
var nextId = 0;
var allowRequestsBackTo = 0;
var prevLength = 0;
suggest = function() {
    var searchBox = document.getElementById('search_bar');
    
    var thisRequest = ++nextId;
    var length = searchBox.value.length
    if (length < prevLength) {
        // On backspace, cancel all prev requests.
        allowRequestsBackTo = thisRequest;
    }
    prevLength = length;
    
    if (length == 0) {
        displaySuggestions(false);
    } else {
        dojo.xhrPost({
            url:        '/searchxml',
            postData:   'q='+searchBox.value,
            handleAs:   'xml',
            load:       function(xmldata) {
                            if (thisRequest >= allowRequestsBackTo) {
                                // Block all earlier requests.
                                allowRequestsBackTo = thisRequest;
                                updateSuggest(xmldata);
                            }
                        }
        });
    }
};
suggestClick = function(id) {
    document.location.href = '/view/' + id + '/';
};