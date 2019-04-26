/*!
 * Expenses Scripting Enhancements
 * Copyright © 2018-2019, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */
import initializeBillEditor from "./billeditor";
import initializeBulkCatEditor from "./bulkcateditor";
import initializeSearchForm from "./searchform";
import setUpAutoComplete from "./autocomplete";
import setUpFlickMenu from "./flickmenu";

function injectAutoComplete() {
    let baseUrl = _expConfig_.baseUrl;
    setUpAutoComplete(".expenses-addform-vendor", "vendor", baseUrl + "api/autocomplete/expense/vendor/");
    setUpAutoComplete(".expenses-billaddform-vendor", "vendor", baseUrl + "api/autocomplete/bill/vendor/");
    setUpAutoComplete(".expenses-addform-description", "description", () => {
        let vendorName = document.querySelector<HTMLInputElement>(".expenses-addform-vendor").value.trim();
        if (vendorName.length == 0) {
            return baseUrl + "api/autocomplete/expense/description/";
        }
        return baseUrl + "api/autocomplete/expense/description/?vendor=" + encodeURIComponent(vendorName);
    });
}

function handleFieldEnabler(event: Event) {
    let target = <HTMLInputElement>event.target;
    let input = <HTMLInputElement>document.getElementById(target.dataset.target);
    input.disabled = !target.checked;
    if (target.checked) input.focus();
}

function onDocReady() {
    // AutoComplete
    injectAutoComplete();

    // initialize BillTable editor
    let expBTForm = document.querySelector("#expenses-billtable-form");
    if (expBTForm !== null) {
        initializeBillEditor();
    }

    // initialize bulk category editor
    let expCatForm = document.querySelector("#expenses-bulkcatedit-form");
    if (expCatForm !== null) {
        initializeBulkCatEditor();
    }
    
    // initialize search form
    let searchForm = document.querySelector("#expenses-search-form");
    if (searchForm !== null) {
        initializeSearchForm();
    }

    // enable field enablers
    let fieldEnablers = document.querySelectorAll(".expenses-field-enabler");
    fieldEnablers.forEach((target: HTMLInputElement) => {
        target.addEventListener("click", handleFieldEnabler);
        let input = <HTMLInputElement>document.getElementById(target.dataset.target);
        input.disabled = !target.checked;
    });

    // make navbar sticky for ExpensesWebView Android app
    if (navigator.userAgent.indexOf("ExpensesWebView") != -1) {
        let navbar = document.querySelector<HTMLElement>(".navbar-kw");
        navbar.classList.remove('static-top');
        navbar.classList.add('fixed-top');
        let body = document.querySelector<HTMLElement>('body');
        body.style.paddingTop = '50px';
    }

    // On mobile, accept flick to uncover top menu
    setUpFlickMenu();
}

document.addEventListener('DOMContentLoaded', onDocReady, false);
