function setupSearch(elements) {
    // Build array for search
    let conceptsAndFields = [];
    let fieldLocation = {};
    elements.nodes.forEach( function(node) {
        if (node.data.nodetype === "field") {
            fieldLocation[node.data.id] = conceptsAndFields.length;
            conceptsAndFields.push({
                text: node.data.name,
                children: []
            });
        } else {
            conceptsAndFields[fieldLocation[node.data.parent]].children.push(
                {
                    id: node.data.id,
                    text: node.data.name
                }
            );
        }
    });

    // Add search bar
    let searchBarDiv = $('#concept-search-bar');
    searchBarDiv.select2({
        theme: "classic",
        multiple: true,
        maximumSelectionLength: 1,
        placeholder: 'Find a concept...',
        data: conceptsAndFields,
        width: 'resolve',
    });

    // Add event handler for when an item is selected
    searchBarDiv.on("select2:select", function (event){
        cy.nodes(`[id = "${event.params.data.id}"]`).emit("tap");
        searchBarDiv.val(null).trigger('change');
    })
}

export { setupSearch }
