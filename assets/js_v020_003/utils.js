import { headers, jsonHeaders } from "./csrf.js"

// Get context from html
export const mapUUID = JSON.parse(document.getElementById('map_uuid').textContent);
export const mapVersion = JSON.parse(document.getElementById('map_version').textContent);
const userdata = JSON.parse(document.getElementById('userdata').textContent);
export var userId;
export const defaultUserId = "default_user_id";
if (userdata !== ""){
    userId = userdata.email;
} else {
    userId = defaultUserId;
}

export const localStorage = window.localStorage;
var alreadyQuestionAnswerUser = localStorage.getItem("questionAnswerUser") === "true"


export function isEditEndpoint() {
    return location.pathname.slice(0, 11) === "/maps/edit/";
}

export function createTipElement(tag, attrs, children){
    let el = document.createElement(tag);
    if(attrs != null && typeof attrs === typeof {}){
        Object.keys(attrs).forEach(function(key){
            const val = attrs[key];

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

function hexToHSL(hex) {
  // Convert hex to RGB first
  let r = 0, g = 0, b = 0;
  if (hex.length === 4) {
    r = "0x" + hex[1] + hex[1];
    g = "0x" + hex[2] + hex[2];
    b = "0x" + hex[3] + hex[3];
  } else if (hex.length === 7) {
    r = "0x" + hex[1] + hex[2];
    g = "0x" + hex[3] + hex[4];
    b = "0x" + hex[5] + hex[6];
  }
  // Then to HSL
  r /= 255;
  g /= 255;
  b /= 255;
  let cmin = Math.min(r,g,b),
      cmax = Math.max(r,g,b),
      delta = cmax - cmin,
      h,
      s,
      l;

  if (delta === 0)
    h = 0;
  else if (cmax === r)
    h = ((g - b) / delta) % 6;
  else if (cmax === g)
    h = (b - r) / delta + 2;
  else
    h = (r - g) / delta + 4;

  h = Math.round(h * 60);

  if (h < 0)
    h += 360;

  l = (cmax + cmin) / 2;
  s = delta === 0 ? 0 : delta / (1 - Math.abs(2 * l - 1));
  s = +(s * 100).toFixed(1);
  l = +(l * 100).toFixed(1);

  return [h, s, l];
}

function HSLToHex(h,s,l) {
  s /= 100;
  l /= 100;

  let c = (1 - Math.abs(2 * l - 1)) * s,
      x = c * (1 - Math.abs((h / 60) % 2 - 1)),
      m = l - c/2,
      r = 0,
      g = 0,
      b = 0;

  if (0 <= h && h < 60) {
    r = c; g = x; b = 0;
  } else if (60 <= h && h < 120) {
    r = x; g = c; b = 0;
  } else if (120 <= h && h < 180) {
    r = 0; g = c; b = x;
  } else if (180 <= h && h < 240) {
    r = 0; g = x; b = c;
  } else if (240 <= h && h < 300) {
    r = x; g = 0; b = c;
  } else if (300 <= h && h < 360) {
    r = c; g = 0; b = x;
  }
  // Having obtained RGB, convert channels to hex
  r = Math.round((r + m) * 255).toString(16);
  g = Math.round((g + m) * 255).toString(16);
  b = Math.round((b + m) * 255).toString(16);

  // Prepend 0s, if necessary
  if (r.length === 1)
    r = "0" + r;
  if (g.length === 1)
    g = "0" + g;
  if (b.length === 1)
    b = "0" + b;

  return `#${r}${g}${b}`;
}

export function LightenDarkenColorByFactor(col, factor) {
    if (factor < 0) {
        console.error(`Factor given (${factor}) in LightenDarkenColorByFactor() cannot be negative!`);
    }

    let hsl = hexToHSL(col)

    hsl[2] *= factor;

    if (hsl[2] < 0) {
        hsl[2] = 0;
    }

    return HSLToHex(Math.round(hsl[0]), Math.round(hsl[1]), Math.round(hsl[2]));
}

function isValidURL(str) {
    let a  = document.createElement('a');
    a.href = str;
    return (a.host && a.host !== window.location.host);
}

export function getValidURLs(urls){
    let url_array = [];

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
    let extension;
    if (name === "learnedNodes") {
        extension = "learned";
    } else if (name === "goalNodes") {
        extension = "goals";
    } else {
        extension = name;
    }
    return `/api/v0/${extension}`;
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
    return payload;
}

function getPostRequestData(name, objectToStore) {
    let payload = {user_id: userId, map_uuid: mapUUID};
    if (name === "learnedNodes") {
        payload["learned_concepts"] = objectToStore;
    } else if (name === "goalNodes") {
        payload["goal_concepts"] = objectToStore;
    } else if (name === "votes") {
        payload["vote_urls"] = objectToStore;
    }
    return payload;
}


function ajaxSuccess (json) {
    console.log(`Success!\n${JSON.stringify(json)}`);
}

function ajaxError(xhr,errmsg,err) {
    console.error(`Oops! We have encountered an error!\n${xhr.status + ": " + xhr.responseText}`);
}

export function initialiseFromStorage(name) {
    let storedItem = localStorage.getItem(name);
    let apiEndpoint = getAPIEndpoint(name);

    if (storedItem !== null) {
        if (userId !== defaultUserId) {
            // If stored locally, check DB and add it if it's not there!
            fetch(
                `${apiEndpoint}?` + new URLSearchParams({user_id: userId, map_uuid: mapUUID}),
                {
                        method: "GET",
                        headers: headers,
                    }
            ).then(response => handleFetchResponses(response)).catch(error => {
                console.error(error);
            });
        }
        return Promise.resolve(JSON.parse(storedItem));
    } else {
        if (userId !== defaultUserId) {
            // Not stored locally, try DB
            return fetch(`${apiEndpoint}?` + new URLSearchParams({user_id: userId, map_uuid: mapUUID}),
                {
                    method: "GET",
                    headers: headers,
                }).then(handleFetchResponses).then(response => {
                    if (response.status === 200) {
                        return response.json();
                    } else {
                        if (name === "votes") {
                            return {}
                        } else if (name === "learnedNodes") {
                            return {learned_concepts: {}};
                        } else {
                            return {goal_concepts: {}};
                        }
                    }
                })
                .then(json => getGetResponseData(name, json))
        } else {
            return Promise.resolve({});
        }
    }
}


export function saveToDB(name, object) {
    if (name !== "votes") {
        fetch(
            getAPIEndpoint(name),
            {
                    method: "POST",
                    body: JSON.stringify(getPostRequestData(name, object)),
                    headers: jsonHeaders
                }
            ).then(response => handleFetchResponses(response));
    } else {
        for (const [url, vote] of Object.entries(object)) {
            fetch(
                getAPIEndpoint(name),
                {
                    method: "POST",
                    headers: jsonHeaders,
                    body: JSON.stringify({
                        map_uuid: mapUUID,
                        user_id: userId,
                        url: url,
                        vote: vote,
                    })
                }).then(response => handleFetchResponses(response));
        }
    }
}


export function logPageView() {
    fetch("/api/v0/page_visit",
        {
            method : "POST",
            headers: jsonHeaders,
            body : JSON.stringify({user_id: userId, page_extension: location.pathname})
    }).then(handleFetchResponses)
    localStorage.setItem("viewed_before", "true");
}


export function logContentClick(url) {
    fetch(
        "/api/v0/link_click",
        {
            method: "POST",
            headers: jsonHeaders,
            body: JSON.stringify({user_id: userId, url: url}),
        }).then(response => handleFetchResponses(response));
}

export function updateQuestionAnswerUsers() {
    if (userId !== defaultUserId && !alreadyQuestionAnswerUser) {
      // TODO: Swap out below once you've added tests for this view!
        // fetch("/api/v0/add_user",
      //     {
      //         method: "PUT",
      //         headers: heade
      //         body: {email: userId, userOnLearney: true},
      //     }).then(response => handleFetchResponses(response));
      $.ajax({
        url : "/api/v0/add_user",
        type : "PUT",
        data : {email: userId, userOnLearney: true},
        success : ajaxSuccess,
        error : ajaxError
      });
      localStorage.setItem("questionAnswerUser", "true");
      alreadyQuestionAnswerUser = true;
    }
}

export function handleFetchResponses(response) {
    if (response.status === 200 || response.status === 201) {
        console.log(`Success! Status: ${response.status}`);
    } else {
        console.log(`Unhappy response! Status: ${response.status} \n ${response}`);
    }
    return response;
}
