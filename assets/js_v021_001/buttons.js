import {initialiseGraphState, resetProgress} from "./learningAndPlanning.js";
import {
    handleFetchResponses,
    LightenDarkenColorByFactor,
    editMapEnabled,
    mapUUID,
    allowSuggestions,
    userEmail
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

// MAKE SUGGESTION BUTTON
if (allowSuggestions) {
    document.getElementById("makeSuggestion").onclick = goToFormFunction("concept");
} else {
    document.getElementById("makeSuggestion").style.display = "none";
}

// RESET PROGRESS BUTTON
if (editMapEnabled) {
    document.getElementById("resetProgress").style.display = "none";
}else {
    document.getElementById("resetProgress").onclick = resetProgressButton;
}
function resetProgressButton() {
    if (resetProgressButtonClicked){
        resetProgress();
        unhighlightNodes(cy.nodes());
        resetProgressButtonClicked = false;
        document.getElementById("resetProgress").innerHTML = "Reset Progress";
    } else {
        document.getElementById("resetProgress").innerHTML = "Are you sure?";
        resetProgressButtonClicked = true;
        setTimeout(function(){
            resetProgressButtonClicked = false;
            document.getElementById("resetProgress").innerHTML = "Reset Progress";
        }, 3000);
    }
}

// RESET PAN BUTTON
document.getElementById("resetPan").onclick = function () {fitCytoTo({eles: cy.nodes(), padding: 50})};
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
    document.getElementById("saveLayout").onclick = saveMap;
}else {
    document.getElementById("saveLayout").style.display = "none";
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
    document.getElementById("runDagre").onclick = autoGenerateLayout;
}else {
    document.getElementById("runDagre").style.display = "none";
}
function autoGenerateLayout() {
    cy.layout(dagreLayout).run();
    dagreOnSubjects();
}

// RESET TO START
if (editMapEnabled) {
    document.getElementById("resetLayout").onclick = resetLayout;
}else {
    document.getElementById("resetLayout").style.display = "none";
}
function resetLayout() {
    cy.remove(cy.elements());
    cy.add(JSON.parse(JSON.stringify(originalMapJSON)));
    cy.layout(presetLayout).run();
    unhighlightNodes(cy.nodes());
    initialiseGraphState();
}
