/*!
 * Expenses AutoComplete registration
 * Copyright © 2018, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */

function setUpAutoComplete(inputQuery: string, name: string, url: string | (() => string)) {
    let input = document.querySelector<HTMLInputElement>(inputQuery);
    if (input === null) return;
    let datalist: HTMLDataListElement = document.createElement('datalist');
    if (name === null || name === undefined) name = input.name;
    let id = 'ac_dl_' + name.replace('.', '');
    datalist.id = id;
    input.setAttribute('list', id);
    input.parentElement.appendChild(datalist);
    // test
    datalist.append("<option value='x'><option value='y'>");
    function inputHandler(_event: Event) {
        let usedUrl: string; // need separate variable so we don’t end up with ?q=f&q=fo&q=foo…
        if (typeof url !== "string") {
            usedUrl = url();
        } else {
            usedUrl = url;
        }
        datalist.innerHTML = '';
        let query = input.value;
        if (query.trim() === "") return;
        if (usedUrl.indexOf("?") !== -1) {
            usedUrl += "&q=" + encodeURIComponent(query);
        } else {
            usedUrl += "?q=" + encodeURIComponent(query);
        }
        fetch(usedUrl).then((response) => response.json()).then((json: [string]) => {
            // special case: only one response, and it’s what the user has typed
            // if the user picks something, the box will reappear (datalists don’t fire events)
            if (json.length === 1 && json[0] === query) return;
            json.forEach((value) => {
                let c: HTMLOptionElement = document.createElement("option");
                c.value = value;
                datalist.appendChild(c);
            });
        });
    }
    input.addEventListener("input", inputHandler);
}

export default function injectAutoComplete() {
    setUpAutoComplete(".expenses-addform-vendor", "vendor", "/expenses/api/autocomplete/expense/vendor/");
    setUpAutoComplete(".expenses-billaddform-vendor", "vendor", "/expenses/api/autocomplete/bill/vendor/");
    setUpAutoComplete(".expenses-addform-description", "description", () => {
        let vendorName = document.querySelector<HTMLInputElement>(".expenses-addform-vendor").value.trim();
        if (vendorName.length == 0) {
            return "/expenses/api/autocomplete/expense/description/";
        }
        return "/expenses/api/autocomplete/expense/description/?vendor=" + encodeURIComponent(vendorName);
    });
}
