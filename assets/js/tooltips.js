import {onLearnedSliderClick, learnedNodes, onSetGoalSliderClick, goalNodes} from "./learningAndPlanning.js";
import {removeIntroTippy} from "./intro.js";
import {getValidURLs, createTipElement, initialiseFromStorage, saveToStorage} from "./utils.js";

var shownTippy;

const votesKeyName = "votes";
// Up/down votes made this session. true means upvote, false means downvote.
var sessionVotes = initialiseFromStorage(votesKeyName);
// Up/down votes
var savedVotes = Object.assign({}, sessionVotes);
var selectedNode;

var cachedLinkPreviews = {};

function makeTippy(node){
    removeIntroTippy();
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

function removeTippy(){
  if(shownTippy){
    removeIntroTippy();
    shownTippy.hide();
    for (const url in sessionVotes) {
        if (!(url in savedVotes) || sessionVotes[url] !== savedVotes[url]) {
            console.log(`Saving vote (up = ${sessionVotes[url]}) for ${url}`);
            $.ajax({
                url : "api/v0/votes",
                type : "POST",
                data : {
                    concept: selectedNode.data().name,
                    url: url,
                    vote: sessionVotes[url],
                },

                success : function(json) {
                    console.log(json);
                    console.log("Success!");
                },

                error : function(xhr,errmsg,err) {
                    console.error("Oops! We have encountered an error!")
                    console.error(xhr.status + ": " + xhr.responseText);
                }
            });
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
        saveToStorage(votesKeyName, sessionVotes);
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
            "src": "assets/images/loading.jpg",
            "class": "link-preview-image"
        }, []);
        let linkImageContainer = createTipElement("div", {"class": "link-preview-image-container"}, [linkImage]);
        let link = createTipElement("a", {
            "href": urls[i],
            "class": "link-preview",
            "target": "_blank"
        }, [linkImageContainer, linkTextContainer]);
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
                data: {concept: nodeName, url: urls[i]},
                success: function (data) {
                    console.log(data);
                    console.log(typeof data);
                    // If successful, show the data in the link preview
                    linkTitle.innerHTML = data.title;
                    linkDescription.innerHTML = data.description;
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
    let description = createTipElement("div", {"class": "tooltip-description tooltip-text"}, node.data().description);
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
        let linkList = createTipElement("ol", {"class": "tooltip-link tooltip-text"}, createLinkPreviewArray(node.data().name, urls));
        marginTipArray.push(linkList);
    }

    return createTipElement("div", {"class": "tooltip-contents"}, marginTipArray);
}

export {makeTippy, removeTippy, createTipElement, shownTippy};
