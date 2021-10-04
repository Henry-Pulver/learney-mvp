import {initialiseGraphState, resetProgress} from "./learningAndPlanning.js";
import {
    handleFetchResponses,
    LightenDarkenColorByFactor,
    editMapEnabled,
    mapUUID,
    allowSuggestions,
    buttonPress, isAnonymousUser, userId
} from "./utils.js";
import { goToFormFunction } from "./suggestions.js";
import { jsonHeaders } from "./csrf.js";
import {
    fitCytoTo,
    dagreLayout,
    darkenFactor,
    unhighlightNodes,
    dagreOnSubjects,
    originalMapJSON,
    presetLayout
} from "./graph.js";

var resetProgressButtonClicked = false;
var cKeyPressed = false;

// SIMPLE BUTTONS
if (!isAnonymousUser(userId)){
    document.getElementById("log-out").onclick = buttonPress(function () {location.href='/logout'}, "log-out");
} else {
    document.getElementById("log-in").onclick = buttonPress(function () {location.href='/login/auth0'}, "log-in");
}
document.getElementById("feedback-button").onclick = buttonPress(function () {window.open('https://docs.google.com/forms/d/e/1FAIpQLSeWyrpKy0r4LbQuuHt5FIL9PYU7KFfLSxFnnuBDs3-zaofW7A/viewform', '_blank')}, "feedback-button");
document.getElementById("slack-button").onclick = buttonPress(function () {window.open('https://join.slack.com/t/learneyalphatesters/shared_invite/zt-tf37n610-x8rIwDk6eeVctTVZqQkp7Q','_blank')}, "slack-button");


// MAKE SUGGESTION BUTTON
if (allowSuggestions) {
    document.getElementById("make-suggestion").onclick = buttonPress(goToFormFunction("concept"), "make-suggestion");
} else {
    document.getElementById("make-suggestion").style.display = "none";
}

// RESET PROGRESS BUTTON
if (editMapEnabled) {
    document.getElementById("reset-progress").style.display = "none";
}else {
    document.getElementById("reset-progress").onclick = buttonPress(resetProgressButton, "reset-progress");
}
function resetProgressButton() {
    if (resetProgressButtonClicked){
        resetProgress();
        unhighlightNodes(cy.nodes());
        resetProgressButtonClicked = false;
        document.getElementById("reset-progress").innerHTML = "Reset Progress";
    } else {
        document.getElementById("reset-progress").innerHTML = "Are you sure?";
        resetProgressButtonClicked = true;
        setTimeout(function(){
            resetProgressButtonClicked = false;
            document.getElementById("reset-progress").innerHTML = "Reset Progress";
        }, 3000);
    }
}

// RESET PAN BUTTON
document.getElementById("reset-pan").onclick = buttonPress(function () {fitCytoTo({eles: cy.nodes(), padding: 50})}, "reset-pan");
document.onkeypress = function(e) {
    if (document.activeElement !== document.getElementsByClassName("select2-search__field")[0]){
        if (e.code === "KeyC" && !cKeyPressed){
            fitCytoTo({eles: cy.nodes(), padding: 50}, function () {cKeyPressed = false;});
            cKeyPressed = true;
        }
    }
};

// SAVE MAP BUTTON
if (editMapEnabled) {
    document.getElementById("save-layout").onclick = buttonPress(saveMap, "save-layout");
}else {
    document.getElementById("save-layout").style.display = "none";
}
function saveMap() {
    let mapJson = {nodes: [], edges: []};
    cy.nodes().forEach(function(node) {
        let nodeData = {data: node.data(), position: node.position()};
        if (nodeData.data.colour !== undefined){
            nodeData.data.colour = LightenDarkenColorByFactor(nodeData.data.colour, 1 / darkenFactor);
        }
        mapJson.nodes.push(nodeData);
    });
    cy.edges().forEach(function(edge) {
        mapJson.edges.push({data: edge.data()});
    });
    fetch("/api/v0/knowledge_maps",
        {
            method : "PUT",
            headers: jsonHeaders,
            body: JSON.stringify({
                map_uuid: mapUUID,
                map_data: mapJson,
            })
        }
    ).then(response => handleFetchResponses(response));
    cy.nodes().forEach(function(node) {
        if (node.data().colour !== undefined){
            node.data().colour = LightenDarkenColorByFactor(node.data().colour, darkenFactor);
        }
    });
}

// AUTO-GENERATE LAYOUT
if (editMapEnabled) {
    document.getElementById("run-dagre").onclick = buttonPress(autoGenerateLayout, "run-dagre");
}else {
    document.getElementById("run-dagre").style.display = "none";
}
function autoGenerateLayout() {
    cy.layout(dagreLayout).run();
    dagreOnSubjects();
}

// RESET TO START
if (editMapEnabled) {
    document.getElementById("reset-layout").onclick = buttonPress(resetLayout, "reset-layout");
}else {
    document.getElementById("reset-layout").style.display = "none";
}
function resetLayout() {
    cy.remove(cy.elements());
    cy.add(JSON.parse(JSON.stringify(originalMapJSON)));
    cy.layout(presetLayout).run();
    unhighlightNodes(cy.nodes());
    initialiseGraphState();
}
