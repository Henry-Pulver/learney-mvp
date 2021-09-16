import {onLearnedSliderClick, learnedNodes, onSetGoalSliderClick, goalNodes} from "./learningAndPlanning.js";
import {removeIntroTippy} from "./intro.js";
import {
    getValidURLs,
    createTipElement,
    initialiseFromStorage,
    logContentClick,
    userId,
    mapUUID,
    handleFetchResponses
} from "./utils.js";
import {jsonHeaders} from "./csrf.js";

export var shownTippy;

const staticFileLocation = document.getElementById("static-root").getAttribute("data-name");

const votesKeyName = "votes";
// Up/down votes made this session. true means upvote, false means downvote.
var sessionVotes;
Promise.resolve(initialiseFromStorage(votesKeyName)).then(response => {
    if (typeof response === "string") {
        sessionVotes = JSON.parse(response);
    } else {
        sessionVotes = response;
    }
})

// Up/down votes
var savedVotes = Object.assign({}, sessionVotes);
var selectedNode;

var cachedLinkPreviews = {};

export function makeTippy(node){
    removeTippy();
    selectedNode = node;
    let html = createTooltipHTML(node);

    shownTippy = tippy(node.popperRef(), {
      html: html,
      allowHTML: true,
      trigger: 'manual',
      arrow: true,
      placement: 'right',
      hideOnClick: false,
      duration: [250, 0],
      theme: 'light',
      interactive: true,
      onHidden: function(tip){
        if(tip != null){
          tip.destroy();
        }
      }
    } ).tooltips[0];
    shownTippy.show();
    return shownTippy;
}

export function removeTippy(){
  // Hide profile div!
  document.getElementById("profile-div").style.display = "none";
  // Hide intro div!
  removeIntroTippy();

  if(shownTippy){
    shownTippy.hide();
    for (const url in sessionVotes) {
        if (!(url in savedVotes) || sessionVotes[url] !== savedVotes[url]) {
            console.log(`Saving vote (up = ${sessionVotes[url]}) for ${url}`);
            fetch("api/v0/votes",
                {
                    method : "POST",
                    headers: jsonHeaders,
                    body: JSON.stringify({
                        map_uuid: mapUUID,
                        user_id: userId,
                        concept: selectedNode.data().name,
                        url: url,
                        vote: sessionVotes[url],
                    })
                }).then(response => handleFetchResponses(response))
            savedVotes[url] = sessionVotes[url];
        }
    }
  }
}

function getArrowDirection(up) {
    if (up === true) {
        return "up";
    } else if (up === false) {
        return "down";
    }
}

function getVoteCheckbox(voteArrow) {
    let checkboxes = voteArrow.getElementsByClassName("vote-checkbox");
    if (checkboxes.length > 1) {
        console.error("Invalid voteArrow HTML element entered into `getCheckbox()`!")
    }
    return checkboxes[0];
}

function voteFunction(up, url, vote_arrow) {
    return function() {
        // Check other arrow is not selected
        let thisCheckbox = getVoteCheckbox(vote_arrow);
        if (url in sessionVotes) {
            let otherDirection = getArrowDirection(!up);
            let otherCheckbox = getVoteCheckbox(vote_arrow.parentElement.getElementsByClassName(otherDirection + "vote")[0]);

            delete sessionVotes[url];

            // Ensure both checkboxes are enabled and unchecked
            thisCheckbox.checked = false;
            otherCheckbox.checked = false;
        } else {
            sessionVotes[url] = up;
            thisCheckbox.checked = true;
            // SEND INFO TO DATABASE
        }
        localStorage.setItem(votesKeyName, JSON.stringify(sessionVotes));
    }
}

function createArrowHTML(up, url) {
    let direction = getArrowDirection(up);
    let checkbox = createTipElement("input", {"type": "checkbox", "class": "vote-checkbox", "disabled": "true"}, []);
    let arrow = createTipElement("div", {"class": "triangle " + direction}, []);
    let voteArrow = createTipElement("div", {"class": "vote-arrow " + direction + "vote"}, [checkbox, arrow]);
    arrow.onclick = voteFunction(up, url, voteArrow);
    return voteArrow
}

function createContentVotingHTML(url) {
    let upArrow = createArrowHTML(true, url);
    let downArrow = createArrowHTML(false, url);

    if (url in sessionVotes) {
        if (sessionVotes[url] === true) {
            getVoteCheckbox(upArrow).checked = true;
        } else {
            getVoteCheckbox(downArrow).checked = true;
        }
    }
    return createTipElement("div", {"class": "voting"}, [upArrow, downArrow])
}

function createLinkPreviewArray (nodeName, urls) {
    let linkArray = []
    for (let i = 0; i < urls.length; i++) {
        let linkTitle = createTipElement("h4", {"class": "link-preview-title"}, "Loading...");
        let linkDescription = createTipElement("p", {"class": "link-preview-description"}, "...");
        let linkUrl = createTipElement("p", {"class": "link-preview-url"}, urls[i]);
        let linkTextContainer = createTipElement("div", {"class": "link-preview-text-container"}, [linkTitle, linkDescription, linkUrl]);
        let linkImage = createTipElement("img", {
            "src": `${staticFileLocation}images/loading.jpg`,
            "class": "link-preview-image"
        }, []);
        let linkImageContainer = createTipElement("div", {"class": "link-preview-image-container"}, [linkImage]);
        let link = createTipElement("a", {
            "href": urls[i],
            "class": "link-preview",
            "target": "_blank"
        }, [linkImageContainer, linkTextContainer]);
        link.onclick = function(){logContentClick(urls[i])};
        let linkElement = createTipElement("li", {"class": "link-preview-list-element"}, [link, createContentVotingHTML(urls[i])]);

        linkArray.push(linkElement);

        // First see if data is cached
        if (urls[i] in cachedLinkPreviews){
            let data = cachedLinkPreviews[urls[i]];
            linkTitle.innerHTML = data.title;
            linkDescription.innerHTML = data.description;
            linkImage.setAttribute("src", data.image_url);
        } else {
            // Next try to get the link preview data from the DB
            $.ajax({
                url: "api/v0/link_previews",
                type: "GET",
                data: {map_uuid: mapUUID, concept: nodeName, url: urls[i]},
                success: function (data) {
                    // If successful, show data in link preview, filling gaps with default values
                    if (data === undefined) {
                        data = {title: "", description: "", image_url: ""};
                    }
                    if (data.title === "") {data.title = nodeName;}
                    linkTitle.innerHTML = data.title;

                    linkDescription.innerHTML = data.description;

                    if (data.image_url === ""){
                        data.image_url = `${staticFileLocation}images/learney_logo_256x256.png`;
                    }
                    linkImage.setAttribute("src", data.image_url);

                    cachedLinkPreviews[urls[i]] = data;

                },
                error: function () {
                    console.error("Failed to retrieve!")
                }
            })
        }
    }
    return linkArray;
}

function createLearnedSlider(node, initiallyChecked, sliderClickFunction, textDescription) {
    let learnedSliderCheckbox = createTipElement('input', {"type": "checkbox"});
    learnedSliderCheckbox.checked = initiallyChecked;

    let sliderSlider = createTipElement('span', {"class": "slider round"});
    sliderSlider.onclick = sliderClickFunction;
    let learnedSlider = createTipElement("label", {"class": "switch"}, [learnedSliderCheckbox, sliderSlider]);
    let learnedText = createTipElement("p", {"class": "switch-text"}, textDescription)
    return createTipElement("div", {"class": "switch-container"}, [learnedText, learnedSlider])
}

function createTooltipHTML(node) {
    var urls
    if (node.data().urls !== undefined){
        urls = getValidURLs(node.data().urls);
    } else{
        urls = [];
    }

    let heading = createTipElement("h4", {"class": "tooltip-heading"}, node.data().name);
    let description = createTipElement("div", {"class": "tooltip-description"}, node.data().description);
    let closeButton = createTipElement("button", {"class": "close"}, "X")
    closeButton.onclick = removeTippy;

    if (node.data().id in learnedNodes) {
        var learned = learnedNodes[node.data().id];
    } else {
        learned = false;
    }
    if (node.data().id in goalNodes) {
        var goalSet = goalNodes[node.data().id];
    } else {
        goalSet = false;

    }
    let learnedSlider = createLearnedSlider(node, learned, onLearnedSliderClick(node), "I know this!")
    let goalSlider = createLearnedSlider(node, goalSet, onSetGoalSliderClick(node), "Set goal")

    let sliders = createTipElement("div", {"class": "slider-container"}, [learnedSlider, goalSlider])

    let marginTipArray = [heading, description, sliders, closeButton]

    // List of pretty link previews for all content for this node
    if (urls.length > 0) {
        let linkList = createTipElement("ol", {"class": "tooltip-link"}, createLinkPreviewArray(node.data().name, urls));
        marginTipArray.push(linkList);
    }

    return createTipElement("div", {"class": "tooltip-contents disable-touch-actions"}, marginTipArray);
}
