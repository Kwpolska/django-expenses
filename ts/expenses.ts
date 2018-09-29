/*!
 * Expenses Scripting Enhancements
 * Copyright © 2018, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */
import initializeBillEditor from "./billeditor";
import initializeBulkCatEditor from "./bulkcateditor";
import injectAutoComplete from "./exp_autocomplete";

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
