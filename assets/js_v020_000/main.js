import "./csrf.js"
import { initCy, isMobile, panByAndZoom } from "./graph.js"
import { makeMouseoverTippy } from "./iconsAndButtons.js";
import { signInTooltip } from "./learningAndPlanning.js";
import { showIntroTippy, toggleIntro } from "./intro.js";
import {
    logPageView,
    updateQuestionAnswerUsers,
    defaultUserId,
    userId,
    localStorage,
    mapUUID,
    mapVersion
} from "./utils.js";
import { csrftoken } from "./csrf.js";

const staticFileLocation = document.getElementById("static-root").getAttribute("data-name");

const graphPromise = fetch(
    "/api/v0/knowledge_maps?" + new URLSearchParams({map_uuid: mapUUID, version: mapVersion}),
        {
            method : "GET",
            headers: {
                'Content-Type': 'application/json',
                "X-CSRFToken": csrftoken,
                "Cache-Control": "max-age=604800"
            },
        }
        ).then(file => file.json());
const stylePromise = fetch(`${staticFileLocation}knowledge_graph.cycss`).then(file => file.text());
const introPromise = fetch(`${staticFileLocation}introSlides_v013.json`).then(file => file.json())

makeMouseoverTippy("#shiprightButton", "Play your part in the future of Learney! We want your feedback and suggestions!");
makeMouseoverTippy("#slackButton", "Want to join our thriving community of contributors and learners? Join our Slack!");
// document.getElementById("shiprightButton").addEventListener("mouseover", makeMouseoverTippy("#shiprightButton", "Play your part in the future of Learney! We want to hear your thoughts and suggestions!"));
// document.getElementById("slackButton").addEventListener("mouseover", makeMouseoverTippy("#slackButton", "Want to join the community or chat to us? Join our Slack and tell us!"));
// document.getElementById("feedbackButton").addEventListener("mouseover", makeMouseoverTippy("#feedbackButton", "Not a fan of Slack? Email us your feedback!"));

// Show profile div if hidden
document.getElementsByClassName("profile-image")[0].onclick = function () {
    let profileDiv = document.getElementById("profile-div");
    if (profileDiv.style.display === "block") {
        profileDiv.style.display = "none";
        if (signInTooltip !== null){
            signInTooltip.enable();
        }
    } else {
        profileDiv.style.display = "block";
        if (signInTooltip !== null){
            signInTooltip.hide();
            signInTooltip.disable();
        }
    }
};

Promise.all([stylePromise, graphPromise]).then(initCy).then(introSequence);

updateQuestionAnswerUsers();

function introSequence() {
    Promise.resolve(introPromise).then(
        function (slides) {
            let introSlides = slides;
            function showIntroIfNew() {
                if (userId === defaultUserId && localStorage.getItem("viewed_before") !== null && !isMobile) {
                    showIntroTippy(introSlides);
                }
            }
            // TODO: if goal is set, zoom there instead of to the bottom?
            panByAndZoom(-cy.width() / 6, -cy.height() * 4 / 9, 1.5, showIntroIfNew);

            document.getElementById("introButton").onclick = toggleIntro(introSlides);
            logPageView();
        }
);
}
