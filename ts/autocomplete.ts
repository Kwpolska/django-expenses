/*!
 * Expenses AutoComplete
 * Copyright © 2018-2019, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */

export default function setUpAutoComplete(input: string | HTMLInputElement,
                                          name: string,
                                          url: string | (() => string),
                                          minLength?: number,
                                          displayHandler?: (data: string | object) => string,
                                          stopPrefix?: string,
                                          stopHandler?: (data: string) => void
                                         ) {
    if (typeof input === "string") {
        input = document.querySelector<HTMLInputElement>(input);
    }
    if (minLength === undefined) minLength = 1;
    if (input === null || input == undefined) return;
    let datalist: HTMLDataListElement = document.createElement('datalist');
    if (name === null || name === undefined) name = input.name;
    let id = 'acdl_' + name.replace('.', '');
    datalist.id = id;
    input.setAttribute('list', id);
    if (input.nextSibling) {
        input.parentElement.insertBefore(datalist, input.nextSibling);
    } else {
        input.parentElement.appendChild(datalist);
    }
    function buildCompletions(_event: Event) {
        let usedUrl: string; // need separate variable so we don’t end up with ?q=f&q=fo&q=foo…
        if (typeof url !== "string") {
            usedUrl = url();
        } else {
            usedUrl = url;
        }
        datalist.innerHTML = '';
        let query = (<HTMLInputElement>input).value;
        if ((<HTMLInputElement>input).dataset['autocomplete'] === 'off') return;
        if (query.trim().length < minLength) return;
        if (stopPrefix !== undefined && query.startsWith(stopPrefix)) { // slightly hacky support for bill item autocomplete
            stopHandler(query);
            return;
        }
        if (usedUrl.indexOf("?") !== -1) {
            usedUrl += "&q=" + encodeURIComponent(query);
        } else {
            usedUrl += "?q=" + encodeURIComponent(query);
        }
        fetch(usedUrl).then((response) => response.json()).then((json: Array<any>) => {
            // special case: only one response, and it’s what the user has typed
            // if the user picks something, the box will reappear (datalists don’t fire events)
            if (json.length === 1 && json[0] === query) return;
            json.forEach((value) => {
                let c: HTMLOptionElement = document.createElement("option");
                if (displayHandler !== undefined) {
                    c.value = displayHandler(value);
                } else {
                    c.value = value;
                }
                datalist.appendChild(c);
            });
        });
    }
    if (minLength === 0) buildCompletions(null);
    input.addEventListener("input", buildCompletions);
}
