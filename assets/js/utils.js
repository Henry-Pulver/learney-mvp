
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

function initialiseFromStorage(name) {
    let storedItem = localStorage.getItem(name);
    if (storedItem === null) {
        return {};
    } else {
        return JSON.parse(storedItem);
    }
}

function saveToStorage(name, object) {
    localStorage.setItem(name, JSON.stringify(object));
}

export {LightenDarkenColor, getValidURLs, createTipElement, initialiseFromStorage, saveToStorage};
