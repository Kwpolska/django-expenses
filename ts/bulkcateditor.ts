/*
 * Expenses Bulk Category Editor
 * Copyright © 2018-2021, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */

import { getTrForEvent, getNewAIDForSelector } from './exputils';

function getNewAID(): number {
    return getNewAIDForSelector("#expenses-bulkcatedit-form");
}

function addBtnHandler(_event?: Event) {
    let addForm: HTMLTableRowElement = document.querySelector<HTMLTableRowElement>("#expenses-bulkcatedit-addrow");

    // Build new table row
    let tr = <HTMLTableRowElement>document.createElement("tr");
    tr.classList.add("table-success");
    let aid = 'a' + getNewAID();
    let inputs = addForm.querySelectorAll("input");
    let addedData = {};
    for (let i = 0; i < inputs.length; i++) {
        let input = inputs[i];
        // @ts-ignore
        if (!input.reportValidity()) {
            throw new Error(`Field ${input.name} was invalid.`);
        }
        let td = <HTMLTableCellElement>document.createElement("td");
        td.className = input.closest("td").className;

        let clonedInput = <HTMLInputElement>input.cloneNode();
        clonedInput.name = clonedInput.name.replace("add_", `add_${aid}_`);
        clonedInput.addEventListener("keypress", returnKeyHandler);
        td.appendChild(clonedInput);
        tr.appendChild(td);
    }
    // Create action buttons
    let actionsTd = document.createElement("td");
    actionsTd.className = "expenses-bulkcatedit-actions";
    let btn = document.createElement("btn");
    btn.className = "btn btn-danger";
    btn.innerHTML = '<i class="fa fa-fw fa-trash-alt"></i>';
    btn.addEventListener("click", deleteBtnHandler);
    actionsTd.appendChild(btn);
    tr.appendChild(actionsTd);

    let tbody: HTMLElement = document.querySelector<HTMLElement>("#expenses-bulkcatedit-form tbody");
    tbody.insertBefore(tr, addForm);

    // Clean up the form
    inputs.forEach(input => input.value = '');
}

// available only on added items
function deleteBtnHandler(event: Event) {
    let tr = getTrForEvent(event);
    tr.remove();
}

function saveChangesBtnHandler(event?: Event) {
    document.querySelectorAll<HTMLInputElement>("#expenses-bulkcatedit-addrow input").forEach(i => i.disabled = true);
    let form = document.querySelector<HTMLFormElement>("#expenses-bulkcatedit-form");
    if (form.reportValidity()) {
        form.submit();
    } else {
        document.querySelectorAll<HTMLInputElement>("#expenses-bulkcatedit-addrow input").forEach(i => i.disabled = false);
    }
    if (event !== null) {
        event.preventDefault();
    }
}

function returnKeyHandler(event: KeyboardEvent) {
    if (event.keyCode == 13) {
        let tr = getTrForEvent(event);
        if (tr.id === "expenses-bulkcatedit-addrow") {
            let addForm: HTMLTableRowElement = document.querySelector<HTMLTableRowElement>("#expenses-bulkcatedit-addrow");
            let inputs = addForm.querySelectorAll("input");
            // If both fields are empty, save instead.
            if (inputs[0].value === '' && inputs[1].value === '') {
                saveChangesBtnHandler(null);
            } else {
                addBtnHandler(event);
            }
        } else {
            saveChangesBtnHandler(null);
        }
        return false;
    }
}

export default function initializeBulkCatEditor() {
    let addBtn = document.querySelector<HTMLButtonElement>("#expenses-bulkcatedit-btn-add");
    addBtn.type = "button";
    addBtn.addEventListener("click", addBtnHandler);

    document.querySelectorAll<HTMLInputElement>("#expenses-bulkcatedit-addrow input").forEach(i => {
        i.disabled = false;
        i.addEventListener("keypress", returnKeyHandler);
    });

    document.querySelectorAll<HTMLElement>("#expenses-bulkcatedit-addrow input").forEach(el => el.addEventListener("keypress", returnKeyHandler));

    let saveBtn = document.querySelector<HTMLButtonElement>("#expenses-bulkcatedit-btn-save");
    saveBtn.type = 'button';
    saveBtn.addEventListener("click", saveChangesBtnHandler);

    let form = document.querySelector<HTMLFormElement>("#expenses-bulkcatedit-form");
    form.dataset['last_aid'] = '0';
}
