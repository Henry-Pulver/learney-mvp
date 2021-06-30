
const userdata = JSON.parse(document.getElementById('userdata').textContent);
var userId;
if (userdata !== ""){
    userId = userdata.email;
} else {
    userId = "default_user_id";
}

var localStorage = window.localStorage;

function createTipElement(tag, attrs, children){
    let el = document.createElement(tag);
    if(attrs != null && typeof attrs === typeof {}){
        Object.keys(attrs).forEach(function(key){
            var val = attrs[key];

            el.setAttribute(key, val);
        });
    }
    if(children != null && typeof children === typeof []){
        children.forEach(function(child){
            el.appendChild(child);
        });
    } else if(children != null && typeof children === typeof ''){
        el.appendChild(document.createTextNode(children));
    }
    return el;
}

function LightenDarkenColor(col, amt) {
    var usePound = false;

    if (col[0] === "#") {
        col = col.slice(1);
        usePound = true;
    }

    var num = parseInt(col,16);
    var r = (num >> 16) + amt;

    if (r > 255) r = 255;
    else if  (r < 0) r = 0;

    var b = ((num >> 8) & 0x00FF) + amt;

    if (b > 255) b = 255;
    else if  (b < 0) b = 0;

    var g = (num & 0x0000FF) + amt;

    if (g > 255) g = 255;
    else if (g < 0) g = 0;

    return (usePound?"#":"") + String("000000" + (g | (b << 8) | (r << 16)).toString(16)).slice(-6);
}

function isValidURL(str) {
    let a  = document.createElement('a');
    a.href = str;
    return (a.host && a.host !== window.location.host);
}

function getValidURLs(urls){
    var url_array = [];

    function validateURL(url){
        url.replace(" ", "");
        if (url.length > 0) {
            url_array.push(url);
            if (!isValidURL(url)) {
                console.error(`The following URL is broken: ${url}`);
            }
        }
    }
    // Run validateURL on each url in the string
    urls.forEach(validateURL);

    return url_array;
}


function getAPIEndpoint(name) {
    var extension;
    if (name === "learnedNodes") {
        extension = "learned";
    } else if (name === "goalNodes") {
        extension = "goals";
    } else {
        extension = name;
    }
    let endpoint = `api/v0/${extension}`;
    return endpoint;
}


function getPostRequestData(name, objectToStore) {
    let payload = {user_id: userId};
    let objectString = JSON.stringify(objectToStore);
    if (name === "learnedNodes") {
        payload["learned_concepts"] = objectString;
    } else if (name === "goalNodes") {
        payload["goal_concepts"] = objectString;
    } else if (name === "votes") {
        payload["vote_urls"] = objectToStore;
    }
    return payload;
}


function getGetResponseData(name, json) {
    let payload;
    if (name === "learnedNodes") {
        payload = json.learned_concepts;
    } else if (name === "goalNodes") {
        payload = json.goal_concepts;
    } else if (name === "votes") {
        payload = json;
    }
    return JSON.stringify(payload);
}


function ajaxSuccess (json) {
    console.log(`Success!\n${JSON.stringify(json)}`);
}


function ajaxError(xhr,errmsg,err) {
    console.error(`Oops! We have encountered an error!\n${xhr.status + ": " + xhr.responseText}`);
}


function initialiseFromStorage(name) {
    let storedItem = localStorage.getItem(name);
    let apiEndpoint = getAPIEndpoint(name);

    if (userId !== undefined){
        if (storedItem !== null) {
            // If stored locally, check DB and add it if it's not there!
            $.ajax({
                url : apiEndpoint,
                type : "GET",
                data : {user_id: userId},
                success : ajaxSuccess,
                error : function(xhr,errmsg,err) {
                    saveToDB(name, JSON.parse(storedItem));
                    ajaxError(xhr,errmsg,err);
                }
            });
        } else {
            // Not stored locally, try DB
            $.ajax({
                url : apiEndpoint,
                type : "GET",
                data : {user_id: userId},
                success : function (json) {
                    ajaxSuccess(json);
                    storedItem = getGetResponseData(name, json);
                    saveToStorage(name, JSON.parse(storedItem), false);
                },
                error : function(xhr,errmsg,err) {
                    console.log(`${name} not found in DB or on browser!`);
                },
                async: false
            });
        }
    }

    if (storedItem === null) {
        // Not in DB or stored
        return {};
    } else {
        // In DB or stored
        return JSON.parse(storedItem);
    }
}

function saveToStorage(name, object, saveItToDB) {
    localStorage.setItem(name, JSON.stringify(object));
    if (userId !== undefined && saveItToDB === true) {
        saveToDB(name, object);
    }
}


function saveToDB(name, object) {
    if (name !== "votes") {
        $.ajax({
            url : getAPIEndpoint(name),
            type : "POST",
            data : getPostRequestData(name, object),
            success : ajaxSuccess,
            error : ajaxError
        });
    } else {
        for (const [url, vote] of Object.entries(object)) {
            console.log(`URL: ${url}, votes: ${vote}`);
            $.ajax({
                url : getAPIEndpoint(name),
                type : "POST",
                data : {
                    url: url,
                    vote: vote,
                },
                success : ajaxSuccess,
                error : ajaxError
            });
        }
    }
}


function logPageView() {
    $.ajax({
        url : "/api/v0/page_visit",
        type : "POST",
        data : {user_id: userId},
        success : ajaxSuccess,
        error : ajaxError
    });
}


function logContentClick(url) {
    $.ajax({
        url : "/api/v0/link_click",
        type : "POST",
        data : {
            user_id: userId,
            url: url
        },
        success : ajaxSuccess,
        error : ajaxError
    });
}

function updateQuestionAnswerUsers() {
    if (userId !== "default_user_id") {
      $.ajax({
        url : "/api/v0/add_user",
        type : "PUT",
        data : {email: userId, userOnLearney: true},
        success : ajaxSuccess,
        error : ajaxError
      });
    }
}

export {LightenDarkenColor, getValidURLs, createTipElement, initialiseFromStorage, saveToStorage, logPageView, logContentClick, updateQuestionAnswerUsers, userId};
