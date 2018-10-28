/*!
 * Expenses Scripting Enhancements
 * Copyright © 2018, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */
import initializeBillEditor from "./billeditor";
import initializeBulkCatEditor from "./bulkcateditor";
import initializeSearchForm from "./searchform";
import setUpAutoComplete from "./autocomplete";

function injectAutoComplete() {
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

function onDocReady() {
    // AutoComplete
    injectAutoComplete();

    // initialize BillTable editor
    let expBTForm = document.querySelector("#expenses-billtable-form");
    if (expBTForm !== null) {
        initializeBillEditor();
    }

    // initialize BillTable editor
    let expCatForm = document.querySelector("#expenses-bulkcatedit-form");
    if (expCatForm !== null) {
        initializeBulkCatEditor();
    }
    
    let searchForm = document.querySelector("#expenses-search-form");
    if (searchForm !== null) {
        initializeSearchForm();
    }

    // make navbar sticky for ExpensesWebView Android app
    if (navigator.userAgent.indexOf("ExpensesWebView") != -1) {
        let navbar = document.querySelector<HTMLElement>(".navbar-kw");
        navbar.classList.remove('static-top');
        navbar.classList.add('fixed-top');
        let body = document.querySelector<HTMLElement>('body');
        body.style.paddingTop = '50px';
    }
}

document.addEventListener('DOMContentLoaded', onDocReady, false);
