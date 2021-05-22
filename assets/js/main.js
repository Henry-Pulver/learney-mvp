import { initCy } from "./graph.js"
import { makeMouseoverTippy } from "./iconsAndButtons.js";
import { showIntroTippy, toggleIntro } from "./intro.js";

var toJson = function(obj){ return obj.json(); };
var toText = function(obj){ return obj.text(); };

var graphP = fetch('assets/positions_knowledge_graph.json').then(toJson);
var styleP = fetch('assets/knowledge_graph.cycss').then(toText);

document.getElementById("shiprightButton").addEventListener("mouseover", makeMouseoverTippy("#shiprightButton", "Want a new feature? Or bugfix? We want to hear about it - click here to suggest it!"));
document.getElementById("slackButton").addEventListener("mouseover", makeMouseoverTippy("#slackButton", "Want to give direct feedback? Is there content we've missed, or are the connections wrong? Join our Slack and tell us!"));
document.getElementById("feedbackButton").addEventListener("mouseover", makeMouseoverTippy("#feedbackButton", "Not a fan of Slack? Email us your feedback!"));

Promise.all([fetch('assets/introSlides.json').then(toJson)]).then(
    function (slides) {
        let introSlides = slides[0];
        showIntroTippy(introSlides);
        document.getElementById("introButton").onclick = toggleIntro(introSlides);
    }
);
Promise.all([styleP, graphP]).then(initCy);

// This function gets cookie with a given name
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

/*
The functions below will create a header with csrftoken
*/
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url === origin || url.slice(0, origin.length + 1) === origin + '/') ||
        (url === sr_origin || url.slice(0, sr_origin.length + 1) === sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});
