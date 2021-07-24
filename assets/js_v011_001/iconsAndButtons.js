import {createTipElement} from "./utils.js";

export function makeMouseoverTippy(selector, text) {
    return function() {
        tippy(selector, {
            html: createTipElement("p", {"class": "feedback-tooltip-text"}, text),
            allowHTML: true,
            arrow: true,
            placement: "left",
        }).tooltips[0].show();
    };
}
