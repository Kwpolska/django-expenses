"use strict";
exports.__esModule = true;
var billtable_1 = require("./billtable");
var exp_autocomplete_1 = require("./exp_autocomplete");
function onDocReady() {
    exp_autocomplete_1["default"]();
    var expBTForm = document.querySelector("#expenses-billtable-form");
    if (expBTForm !== null) {
        billtable_1["default"]();
    }
    if (navigator.userAgent.indexOf("ExpensesWebView") != -1) {
        var navbar = document.querySelector(".navbar-kw");
        navbar.classList.remove('static-top');
        navbar.classList.add('fixed-top');
        var body = document.querySelector('body');
        body.style.paddingTop = '50px';
    }
}
document.addEventListener('DOMContentLoaded', onDocReady, false);
