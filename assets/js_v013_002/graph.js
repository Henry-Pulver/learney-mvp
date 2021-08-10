import { LightenDarkenColorByFactor } from "./utils.js"
import { makeTippy, removeTippy } from "./tooltips.js"
import {
    initialiseGraphState,
    goalNodes,
    pathNodes,
    learnedNodes,
    clearMap,
    onSetGoalSliderClick
} from "./learningAndPlanning.js";
import { setupSearch } from "./search.js";

export const isMobile = screen.width < 768;
var resetProgressButtonClicked = false;

const fieldOpacity = 0.7;
const lowestConceptOpacity = 0.4;
var cKeyPressed = false;

var selectedNodeID = Infinity;

export function initCy(then) {
    /** Initialise Cytoscape graph.*/
    let elements = then[1];
    // let subjects = [];
    elements.nodes.forEach(function(node){
        if (node.data.colour !== undefined){
            node.data.colour = LightenDarkenColorByFactor(node.data.colour, 0.15);
        }
        // if (node.data.nodetype === "field") {
        //     subjects.push(node.name);
        // }
    });

    window.cy = window.cytoscape({
        elements: elements,
        container: document.getElementById("cy"),
        // layout: {name: "dagre", rankDir: "BT", nodeSep: 100, rankSep: 400},
        layout: {name: "preset"},
        style: then[0],

        // initial viewport state:
        zoom: 1,
        pan: {x: 0, y: 0},

        maxZoom: 1.5,
        minZoom: 0.02,
    });

    if (isMobile) {
        // Performance enhancements
        let concepts = cy.nodes('[nodetype = "concept"]');
        concepts.style("min-zoomed-font-size", "2.5em");
    } else {
        cy.wheelSensitivity = 0.25;
    }
    // DO DAGRE FOR EACH SUBJECT
    // subjects.forEach(function(subject, index) {
    //     var subject_subgraph = window.cy.filter('node[subject = "' + subject + '"]');
    //     subject_subgraph.merge(subject_subgraph.connectedEdges())
    //     subject_subgraph.layout({
    //         name: "dagre",
    //         rankDir: "BT",
    //         // boundingBox: {x1: xLocations[index][0] * 20, y1: -250, x2: xLocations[index][1] * 20, y2: 250}
    //     }).run()
    // })

    // DO DAGRE ON WHOLE THANG
    // console.log(window.cy.nodes().filter("[parent]"));
    // console.log(window.cy.elements());
    // window.cy.elements().layout({name: "dagre", rankDir: "BT", nodeSep: 100, rankSep: 300}).run();

    // window.cy.elements().panify();
    unhighlightNodes(cy.nodes());

    // Set initially learned or goal nodes
    initialiseGraphState();

    bindRouters();
    setupSearch(elements);
}

// BUTTONS
document.getElementById("clearMap").onclick = clearMapButton;
function clearMapButton() {
    if (resetProgressButtonClicked){
        clearMap();
        unhighlightNodes(cy.nodes());
        resetProgressButtonClicked = false;
        document.getElementById("clearMap").innerHTML = "Reset Progress";
    } else {
        document.getElementById("clearMap").innerHTML = "Are you sure?";
        resetProgressButtonClicked = true;
        setTimeout(function(){
            resetProgressButtonClicked = false;
            document.getElementById("clearMap").innerHTML = "Reset Progress";
        }, 3000);
    }
}

document.getElementById("resetPan").onclick = function () {fitCytoTo({eles: cy.nodes(), padding: 50})};
document.onkeypress = function(e) {
    if (document.activeElement !== document.getElementsByClassName("select2-search__field")[0]){
        if (e.code === "KeyC" && !cKeyPressed){
            fitCytoTo({eles: cy.nodes(), padding: 50}, function () {cKeyPressed = false;});
            cKeyPressed = true;
        }
    }
};
function fitCytoTo(fitParams, onComplete = function () {}) {
    if (isMobile) {
        cy.fit(fitParams.eles, fitParams.padding);
        onComplete();
    } else {
        cy.animate({ fit: fitParams, duration: 400, easing: "ease-in-out", complete: onComplete
        });
    }
}

// REMOVE FOR PROD
document.getElementById("captureLayout").onclick = captureLayout
function captureLayout() {
    var positions = {};
    var nodes = window.cy.nodes();
    nodes.forEach(function(node) {
        positions[node.data().id] = node.position();
    });

    var myBlob = new Blob([JSON.stringify(positions)], {type: 'application/json'});

    // CREATE DOWNLOAD LINK
    var url = window.URL.createObjectURL(myBlob);
    var anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "NodePositions.json";

    // FORCE DOWNLOAD
    // NOTE: MAY NOT ALWAYS WORK DUE TO BROWSER SECURITY
    // BETTER TO LET USERS CLICK ON THEIR OWN
    anchor.click();
    window.URL.revokeObjectURL(url);
    anchor.remove();
}

function getConceptNodeOpacity(node, normalOpacity) {
    return normalOpacity + ((node.data().relative_importance - 1)  * (1 - normalOpacity) / 2);
}

function resizeNodes(nodes, newBaseSize) {
    nodes.forEach( function(node) {
        if (node.data().id !== selectedNodeID) {
            let nodeSize = node.data().relative_importance * newBaseSize;
            node.style("width", nodeSize.toString() + "px");
            node.style("height", nodeSize.toString() + "px");
            let fontSize = 1.25 * node.data().relative_importance * 24;
            node.style("font-size", fontSize.toString() + "px");
        }
    });
}

function setGraphOpacity(nodes, multiplicativeFactor) {
    setNodeOpacity(nodes, multiplicativeFactor);
    setEdgeOpacity(nodes.connectedEdges(), multiplicativeFactor);
}

function setNodeOpacity(nodes, multiplicativeFactor) {
    nodes.forEach( function(node) {
        let nId = node.data().id;
        if (nId in learnedNodes || nId in pathNodes || nId in goalNodes || nId === selectedNodeID){
            node.style("opacity", 1);
        } else{
            node.style("opacity", Math.min(getConceptNodeOpacity(node, lowestConceptOpacity) * multiplicativeFactor, 1));
        }
    });
}

function setEdgeOpacity(edges, multiplicativeFactor) {
    edges.forEach( function (edge) {
        let sId = edge.source().data().id;
        let tId = edge.target().data().id;
        let sourceMaxOpacity = sId in learnedNodes || sId in pathNodes || sId in goalNodes || sId === selectedNodeID;
        let targetMaxOpacity = tId in learnedNodes || tId in pathNodes || tId in goalNodes || tId === selectedNodeID;
        if (sourceMaxOpacity && targetMaxOpacity){
            edge.style("opacity", 1);
        } else if (checkEdgeInvisible(edge)) {
            edge.style("opacity", 0.1)
        }else{
            let sourceNodeOpacity = Math.min(multiplicativeFactor * getConceptNodeOpacity(edge.source(), lowestConceptOpacity), 1);
            let targetNodeOpacity = Math.min(multiplicativeFactor * getConceptNodeOpacity(edge.target(), lowestConceptOpacity), 1);
            let opacity = (sourceNodeOpacity + targetNodeOpacity) / 2;
            edge.style("opacity", opacity);
        }
    })
}

function checkEdgeInvisible(edge) {
    if (edge.source().data().parent !== edge.target().data().parent) {
        let sx = edge.source().position().x;
        let sy = edge.source().position().y;
        let tx = edge.target().position().x;
        let ty = edge.target().position().y;
        return ((sx - tx) ** 2 + (sy - ty) ** 2) ** (1/2) > 1500;
    } else {
        return false;
    }
}

function highlightNodes(nodes, resize) {
    nodes.style("opacity", 1);
    if (resize) {
        resizeNodes(nodes, 72);
    }
}

function unhighlightNodes(nodes) {
    setGraphOpacity(nodes, 1);
    resizeNodes(nodes, 48);
}

function bindRouters() {
    // Removes tooltip when clicking elsewhere/panning/zooming
    cy.on('tap pan zoom', function (e) {
        if (e.target === cy) {
            selectedNodeID = Infinity;
            removeTippy();
        }
    });

    // Mouse over fields
    cy.on("mouseover", "node[nodetype = \"field\"]", function(e) {
        let field = e.target;

        // Set field opacity to 1
        field.style("opacity", 1);

        // Increase opacity of all edges and nodes
        setGraphOpacity(field.children(), 1.2)
    });
    cy.on("mouseout", "node[nodetype = \"field\"]", function(e) {
        let field = e.target;
        field.style("opacity", fieldOpacity);
        setGraphOpacity(field.children(), 1);
    });

    // Mouse over concept nodes
    cy.on("mouseover", "node[nodetype = \"concept\"]", function(e) {
        let concept = e.target;

        // 1. Everything for fields
        concept.parent().style("opacity", 1);
        setGraphOpacity(concept.parent().children(), 1.2);

        // 2. Make connected nodes & edges opacity = 1
        concept.neighborhood().style("opacity", 1);

        // 3. Make highlighted node opacity=1 and bigger
        highlightNodes(concept, true);
    });
    cy.on("mouseout", "node[nodetype = \"concept\"]", function(e) {
        let concept = e.target;
        concept.parent().style("opacity", fieldOpacity);
        setGraphOpacity(concept.parent().children(), 1);
        unhighlightNodes(concept);
    });

    // Mouse over edges
    cy.on("mouseover", "edge", function(e) {
        let edge = e.target;

        // Everything for fields, plus:
        edge.connectedNodes().parents().style("opacity", 1);
        setGraphOpacity(edge.connectedNodes().parents().children(), 1.2);

        // 1. Make connected nodes opacity=1
        highlightNodes(edge.connectedNodes(), false);

        // 2. Make highlighted edge opacity = 1
        edge.style("opacity", 1);

    });
    cy.on("mouseout", "edge", function(e) {
        let edge = e.target;
        let nodes = edge.connectedNodes();
        edge.connectedNodes().parents().style("opacity", fieldOpacity);
        setGraphOpacity(edge.connectedNodes().parents().children(), 1);
        unhighlightNodes(nodes);
    });

    // Show tooltip when clicked
    cy.on('tap', 'node[nodetype = "concept"]', function (e) {
        let concept = e.target;
        fitCytoTo({eles: concept.neighborhood(), padding: 50}, function () {
                makeTippy(concept);
                let previousSelectedNodeID = selectedNodeID;
                selectedNodeID = concept.data().id;
                unhighlightNodes(cy.getElementById(previousSelectedNodeID))
                highlightNodes(concept, true);
        });
    });

    cy.on("tap", "node[nodetype = \"field\"]", function(e) {
        let field = e.target;
        fitCytoTo({eles: field, padding: 25});
    });

    cy.on("tap", "edge", function(e) {
        let edge = e.target;
        fitCytoTo({eles: edge.connectedNodes(), padding: 50});
    });

    // Right click concepts
    cy.on('cxttap', 'node[nodetype = "concept"]', function (e) {
        onSetGoalSliderClick(e.target)();
    });
}
