/*!
 * Expenses AutoComplete registration
 * Copyright © 2018, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */
let AutoComplete = require("autocomplete-js");

export default function injectAutoComplete() {
    AutoComplete({
        Url: "/expenses/api/autocomplete/expense/vendor/"
    }, ".expenses-addform-vendor");

    AutoComplete({
        Url: "/expenses/api/autocomplete/bill/vendor/"
    }, ".expenses-billaddform-vendor");

    AutoComplete({
        _Url: () => {
            let vendorName = document.querySelector<HTMLInputElement>(".expenses-addform-vendor").value.trim();
            if (vendorName.length == 0) {
                return "/expenses/api/autocomplete/expense/description/";
            }
            return "/expenses/api/autocomplete/expense/description/?vendor=" + encodeURIComponent(vendorName);
        }
    }, ".expenses-addform-description");
}
