import {defaultUserId} from "./utils.js";

const URLToMapSuggestion = {
    original_map: "Machine+Learning+map",
    shahaf_karp: "Shahaf+Karp's+map",
    shahaf_k: "Shahaf+Karp's+map",
    GAN: "GAN",
};
const suggestionToFormEntry = {
    content: "Content+link",
    concept: "Concept+(node+in+the+network)",
    dependency: "Dependency+(connection)",
};

export function getSuggestionURL(userEmail, suggestionType, relevantConcept = "") {
    if (!(suggestionType in suggestionToFormEntry)) {
        console.error(`${suggestionType} is not a valid suggestion type!`);
    }
    let urlEnding = location.pathname.split("/").at(-1);
    if (urlEnding === "") {
        urlEnding = "original_map";
    }
    if (!(urlEnding in URLToMapSuggestion)) {
        console.error(`${urlEnding} is not a valid URL ending!`);
    }
    if (userEmail === defaultUserId) {
        userEmail = "";
    }
    if (relevantConcept !== "") {
        relevantConcept = `&entry.453705070=${relevantConcept.replace(/ /g, "+")}`;
    }
    // return `https://docs.google.com/forms/d/e/1FAIpQLScH8oOtd8sIcXtTRd6cs6gomR3ixvm2Nv8L3TcsErFtBsf4uA/viewform?usp=pp_url${relevantConcept}&entry.1943732201=${userEmail}&entry.758676511=${URLToMapSuggestion[urlEnding]}&entry.1956489231=${suggestionToFormEntry[suggestionType]}`
    return `https://docs.google.com/forms/d/e/1FAIpQLScH8oOtd8sIcXtTRd6cs6gomR3ixvm2Nv8L3TcsErFtBsf4uA/viewform?usp=pp_url&entry.758676511=${URLToMapSuggestion[urlEnding]}&entry.1956489231=${suggestionToFormEntry[suggestionType]}${relevantConcept}&entry.1943732201=${userEmail}`
}

export function goToFormFunction(userEmail, suggestionType, relevantConcept = "") {
    console.log(relevantConcept);
    return function () {
        window.open(getSuggestionURL(userEmail, suggestionType, relevantConcept), '_blank')
    }
}
