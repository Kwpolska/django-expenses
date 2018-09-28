"use strict";
exports.__esModule = true;
var AutoComplete = require("autocomplete-js");
function injectAutoComplete() {
    AutoComplete({
        Url: "/expenses/api/autocomplete/expense/vendor/"
    }, ".expenses-addform-vendor");
    AutoComplete({
        Url: "/expenses/api/autocomplete/bill/vendor/"
    }, ".expenses-billaddform-vendor");
    AutoComplete({
        _Url: function () {
            var vendorName = document.querySelector(".expenses-addform-vendor").value.trim();
            if (vendorName.length == 0) {
                return "/expenses/api/autocomplete/expense/description/";
            }
            return "/expenses/api/autocomplete/expense/description/?vendor=" + encodeURIComponent(vendorName);
        }
    }, ".expenses-addform-description");
}
exports["default"] = injectAutoComplete;
