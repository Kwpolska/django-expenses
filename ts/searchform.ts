/*
 * Expenses Search Form
 * Copyright © 2018-2019, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */

function handleDisableSearchDates(_event?: Event) {
    let startInput = document.querySelector<HTMLInputElement>("#search-date-start");
    let endInput = document.querySelector<HTMLInputElement>("#search-date-end");
    let anySpec = document.querySelector<HTMLInputElement>("#search-date-spec-any");

    if (anySpec.checked) {
        startInput.disabled = true;
        endInput.disabled = true;
    } else {
        startInput.disabled = false;
        endInput.disabled = false;
    }
}

function handleDisableSearchIncludes(_event?: Event) {
    let includeExpenses = document.querySelector<HTMLInputElement>("#search-include-expenses");
    let includeBills = document.querySelector<HTMLInputElement>("#search-include-bills");
    if (document.querySelector<HTMLInputElement>("#search-for-expenses").checked) {
        includeExpenses.disabled = false;
        includeBills.disabled = false;
    } else {
        includeExpenses.disabled = true;
        includeBills.disabled = true;
    }

}

export default function initializeSearchForm() {
    document.querySelector<HTMLInputElement>("#search-for-expenses").addEventListener("click", handleDisableSearchIncludes);
    document.querySelector<HTMLInputElement>("#search-for-billitems").addEventListener("click", handleDisableSearchIncludes);
    handleDisableSearchIncludes(null);

    document.querySelector<HTMLInputElement>("#search-date-spec-any").addEventListener("click", handleDisableSearchDates);
    document.querySelector<HTMLInputElement>("#search-date-spec-between").addEventListener("click", handleDisableSearchDates);
    handleDisableSearchDates(null);
}
