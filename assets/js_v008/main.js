import "./crsf.js"
import { initCy } from "./graph.js"
import { makeMouseoverTippy } from "./iconsAndButtons.js";
import { showIntroTippy, toggleIntro } from "./intro.js";
import { logPageView } from "./utils.js";

logPageView();

var toJson = function(obj){ return obj.json(); };
var toText = function(obj){ return obj.text(); };

const staticFileLocation = document.getElementById("static-root").getAttribute("data-name");

var graphP = fetch(`${staticFileLocation}positions_knowledge_graph_v008.json`).then(toJson);
var styleP = fetch(`${staticFileLocation}knowledge_graph.cycss`).then(toText);

document.getElementById("shiprightButton").addEventListener("mouseover", makeMouseoverTippy("#shiprightButton", "Want a new feature? Or bugfix? We want to hear about it - click here to suggest it!"));
document.getElementById("slackButton").addEventListener("mouseover", makeMouseoverTippy("#slackButton", "Want to give direct feedback? Is there content we've missed, or are the connections wrong? Join our Slack and tell us!"));
document.getElementById("feedbackButton").addEventListener("mouseover", makeMouseoverTippy("#feedbackButton", "Not a fan of Slack? Email us your feedback!"));

document.getElementsByClassName("profile-image")[0].onclick = function () {
    let profileDiv = document.getElementById("profile-div");
    if (profileDiv.style.display === "block") {
        profileDiv.style.display = "none";
    } else {
        profileDiv.style.display = "block";
    }
};

Promise.all([fetch(`${staticFileLocation}introSlides_v008.json`).then(toJson)]).then(
    function (slides) {
        let introSlides = slides[0];
        showIntroTippy(introSlides);
        document.getElementById("introButton").onclick = toggleIntro(introSlides);
    }
);

Promise.all([styleP, graphP]).then(initCy);
