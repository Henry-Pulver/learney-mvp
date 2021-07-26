import {createTipElement} from "./utils.js";

var introSlideNumber = 0;
var shownIntroTippy;
var introTippyShown;

const staticFileLocation = document.getElementById("static-root").getAttribute("data-name");

function createIntroHTML(introSlides) {
    let slideInfo = introSlides[introSlideNumber]

    let title = createTipElement("h2", {"class": "intro-text"}, slideInfo.title);
    let gif = createTipElement("video", {"class": "intro-gif", "src": staticFileLocation + slideInfo.gif, "autoplay": "", "loop": ""}, []);
    let gifDiv = createTipElement("div", {"class": "intro-gif-div"}, [gif]);
    let textDiv = createTipElement("div", {"class": "intro-text-div"}, []);

    // Generate text
    for (let i = 0; i < slideInfo.text.length; i++) {
        let textItem = slideInfo.text[i];
        if (typeof textItem == "string") {
            if (textItem === "br") {
                textDiv.appendChild(document.createElement("br"));
                textDiv.appendChild(document.createElement("br"));
            } else {
                textDiv.innerHTML += textItem;
            }
        } else {
            textDiv.appendChild(createTipElement(textItem[0], textItem[1], textItem[2]));
        }
    }

    let numSlides = introSlides.length;

    let prevSlide = createTipElement("div", {"class": "triangle left"}, [])
    if (introSlideNumber === 0){
        prevSlide.className += "disabled";
    } else {
        prevSlide.onclick = changeSlideFunction(false, introSlides);
    }

    let nextSlide = createTipElement("div", {"class": "triangle right"}, [])
    if (introSlideNumber + 1 === numSlides){
        nextSlide.className += "disabled";
    } else {
        nextSlide.onclick = changeSlideFunction(true, introSlides);
    }
    let slideNumDiv = createTipElement("div", {"class": "intro-slide-num-div"}, (introSlideNumber + 1).toString() + "/" + numSlides.toString());

    let slideDiv = createTipElement("div", {"class": "intro-slide-change-div"}, [prevSlide, slideNumDiv, nextSlide]);
    let closeButton = createTipElement("button", {"class": "close"}, "X");
    closeButton.onclick = removeIntroTippy;

    let introContainer = createTipElement("div", {"class": "intro-container"}, [title, gifDiv, textDiv, slideDiv]);
    return createTipElement("div", {"class": "intro-content-container"}, [introContainer, closeButton]);
}

export function showIntroTippy(introSlides) {
    shownIntroTippy = tippy("#introButton", {
        html: createIntroHTML(introSlides),
        allowHTML: true,
        trigger: 'manual',
        arrow: true,
        placement: 'bottom',
        hideOnClick: false,
        interactive: true,
    } ).tooltips[0];
    shownIntroTippy.show();
    introTippyShown = true;
}

export function removeIntroTippy() {
    if (introTippyShown === true) {
        shownIntroTippy.hide();
    }
    introTippyShown = false;
}

export function toggleIntro(introSlides) {
    return function () {
        if (!introTippyShown) {
            showIntroTippy(introSlides);
        } else {
            removeIntroTippy();
        }
    }
}

function changeSlideFunction(next, introSlides) {
    return function () {
        removeIntroTippy();
        if (next === true) {
            introSlideNumber += 1;
        } else {
            introSlideNumber -= 1;
        }
        showIntroTippy(introSlides);
    }
}
