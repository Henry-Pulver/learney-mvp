
const userdata = JSON.parse(document.getElementById('userdata').textContent);
export var userId;
if (userdata !== ""){
    userId = userdata.email;
} else {
    userId = "default_user_id";
}

var localStorage = window.localStorage;

export function createTipElement(tag, attrs, children){
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


export function initialiseFromStorage(name) {
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

export function saveToStorage(name, object, saveItToDB) {
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


export function logPageView() {
    fetch("/api/v0/page_visit",
        {
            method : "POST",
            headers: {
                'Content-Type': 'application/json',
            },
            body : JSON.stringify({user_id: userId})
    });
    // $.ajax({
    //     url : "/api/v0/page_visit",
    //     type : "POST",
    //     data : {user_id: userId},
    //     success : ajaxSuccess,
    //     error : ajaxError
    // });
}


export function logContentClick(url) {
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

export function updateQuestionAnswerUsers() {
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
