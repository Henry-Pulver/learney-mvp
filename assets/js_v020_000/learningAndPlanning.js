import {
    createTipElement,
    defaultUserId,
    initialiseFromStorage, localStorage,
    saveToStorage,
    updateQuestionAnswerUsers,
    userId
} from "./utils.js";


const learnedNodesString = "learnedNodes";
const goalNodesString = "goalNodes";

// Remove Sept 2021 and remove storing state in cookies entirely
const deleteStoredProgress = "deleteStoredProgress";
const transferredToProfileOnce = "transferredToProfileOnce";
export var signInTooltip = null;
// Deals with old users
if (userId === defaultUserId){
    // Doesn't delete progress of prev users. Deletes user progress when they've visited multiple times!
    if (localStorage.getItem(deleteStoredProgress) === "true") {
        localStorage.removeItem(learnedNodesString);
        localStorage.removeItem(goalNodesString);
    }
    localStorage.setItem(deleteStoredProgress, "true");
    // Deals with previous users who have things set already
    signInTooltip = promptSignInTooltip("To keep progress across sessions, sign in here!");
    signInTooltip.show();
} else if (localStorage.getItem(transferredToProfileOnce) === null) {  // Deals with first-time signed in users
    localStorage.setItem(transferredToProfileOnce, "true");
} else {  // Deals with other signed in users
    if (localStorage.getItem(deleteStoredProgress) === "true") {
        localStorage.removeItem(learnedNodesString);
        localStorage.removeItem(goalNodesString);
    }
}

// End remove Sept 2021
export var learnedNodes = initialiseFromStorage(learnedNodesString);
export var goalNodes = initialiseFromStorage(goalNodesString);
export var pathNodes = {};


export function clearMap() {
    for (const goalId in goalNodes){
        unsetGoal(cy.getElementById(goalId));
    }
    for (const learnedId in learnedNodes) {
        if (learnedNodes[learnedId] === true) {
            onLearnedSliderClick(cy.getElementById(learnedId));
        }
    }
    learnedNodes = {};
    goalNodes = {};
    pathNodes = {};
    saveToStorage(learnedNodesString, learnedNodes, true);
    saveToStorage(goalNodesString, goalNodes, true);
}

function nodeLearned(node) {
    learnedNodes[node.data().id] = true;
    node.addClass("learned");
    node.style("opacity", 1);
}

function checkEdgeLearned(edge) {
    if (edge.source().classes().includes("learned") && edge.target().classes().includes("learned")) {
        edge.addClass("learned");
        edge.style("opacity", 1);
    } else {
        edge.removeClass("learned");
    }
}

export function onLearnedSliderClick(node) {
    return function () {
        let nodeId = node.data().id;
        if (!(nodeId in learnedNodes)) {  // Not learned
            nodeLearned(node);
            // Deal with predecessors
            node.predecessors("node").forEach(function(node) {
                nodeLearned(node);
            });
            node.predecessors("edge").forEach(function(edge) {
                checkEdgeLearned(edge);
            });
        } else {  // Learned or set as unknown
            node.toggleClass("learned");
            learnedNodes[nodeId] = !learnedNodes[nodeId]
            // Deal with edges
            node.connectedEdges().forEach(function(edge) {
                checkEdgeLearned(edge);
            });
        }
        saveToStorage(learnedNodesString, learnedNodes, true);
        if (userId === defaultUserId){
            // promptSignInTooltip("To keep what you know across sessions, sign in here!")
            signInTooltip.show();
        }
    }
}

function setPath(node) {
    let path = node.predecessors().not(".goal").not(".path");
    path.addClass("path");
    path.nodes().forEach(function(node) {
        pathNodes[node.data().id] = true;
        node.style("opacity", 1);
    });
    path.edges().forEach(function(edge){
        edge.style("opacity", 1);
    });
}

function promptSignInTooltip(text) {
    return tippy("#profile-image-button", {
            html: createTipElement("p", {"class": "feedback-tooltip-text"}, text),
            allowHTML: true,
            arrow: true,
            placement: "bottom",
            delay: [0, 3000],
        }).tooltips[0];
}


function setGoalIfSignedIn(node) {
    setGoal(node);
    if (userId === defaultUserId) {
        // Prompt sign in
        // promptSignInTooltip("To keep your goals across sessions, sign in here!");
        signInTooltip.show();
    }
}

function setGoal(node) {
    goalNodes[node.data().id] = true;
    node.addClass("goal");
    node.removeClass("path");
    node.style("opacity", 1);
    setPath(node);
}

function unsetGoal(node) {
    delete goalNodes[node.data().id];
    node.removeClass("goal");

    // Remove this goal's path
    let path = node.predecessors().not(".goal");
    path.removeClass("path");
    path.nodes().forEach(function(node) {
        delete pathNodes[node.data().id];
    });
    // Ensure all other goals have correct paths
    for (const goalId in goalNodes) {
        setPath(cy.nodes(`[id = "${goalId}"]`));
    }
}


export function onSetGoalSliderClick(node) {
    return function () {
        let nodeId = node.data().id;

        // If not already set!
        if (!(nodeId in goalNodes)){
            // Set goal to class goal and unknown dependencies to class: path
            setGoalIfSignedIn(node);
        } else {
            // If unsetting a goal, remove path from its predecessors and recalculate path to remaining goals
            unsetGoal(node);
        }
        saveToStorage(goalNodesString, goalNodes, true);
        updateQuestionAnswerUsers();
    }
}

export function initialiseGraphState() {
    for (const nodeId in learnedNodes) {
        let node = cy.nodes(`[id = '${nodeId}']`);
        if (node.data() !== undefined){
            if (learnedNodes[nodeId] === true) {
                nodeLearned(node);
                node.connectedEdges().forEach(function(edge) {
                    checkEdgeLearned(edge);
                });
            }
        } else {
            delete learnedNodes[nodeId];
        }
    }
    for (const nodeId in goalNodes) {
        let node = cy.nodes("[id = '" + nodeId + "']");
        if (node.data() !== undefined) {
            setGoalIfSignedIn(node);
        } else{
            delete goalNodes[nodeId];
        }
    }
}
