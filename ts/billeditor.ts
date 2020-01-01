/*
 * Expenses Bill Editor
 * Copyright © 2018-2020, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */

import { getTrForEvent, getNewAIDForSelector, formatMoney } from './exputils';
import setUpAutoComplete from "./autocomplete";

const NUMBER_CLASS_NAMES = ['expenses-billtable-serving', 'expenses-billtable-count', 'expenses-billtable-unitprice'];

class ButtonSpec {
    classNames: string;
    icon: string;
    title: string;
    callback: any;
}

class BillHint {
    product: string;
    serving: number;
    unit_price: number;
}

class BillReOutput {
    product: string;
    serving: string;
    unitprice: string;

    [key: string]: string;
}

function amountChangeHandler(event: Event) {
    recalculateAmount(getTrForEvent(event));
}

function recalculateAmount(tr: HTMLTableRowElement) {
    const unitPriceTd: HTMLTableCellElement = <HTMLTableCellElement>tr.getElementsByClassName("expenses-billtable-unitprice")[0];
    const countTd: HTMLTableCellElement = <HTMLTableCellElement>tr.getElementsByClassName("expenses-billtable-count")[0];

    const unitPriceInput: HTMLInputElement = unitPriceTd.getElementsByTagName("input")[0];
    const countInput: HTMLInputElement = countTd.getElementsByTagName("input")[0];

    let amountTd: HTMLTableCellElement = <HTMLTableCellElement>tr.getElementsByClassName("expenses-billtable-amount")[0];
    const amount = parseFloat(unitPriceInput.value) * parseFloat(countInput.value);
    amountTd.innerText = formatMoney(amount);
    amountTd.dataset['value'] = amount.toString();

    recalculateTotal();
}

function recalculateTotal() {
    let amounts = document.querySelectorAll("td.expenses-billtable-amount");
    let total = 0;
    for (let i = 0; i < amounts.length; i++) {
        let n = parseFloat((<HTMLElement>amounts[i]).dataset['value']);
        if (!isNaN(n)) total += n;
    }
    document.querySelector<HTMLElement>(".expenses-bill-total").innerText = formatMoney(total);
}

function activateSaveChanges() {
    let btn = <HTMLButtonElement>document.querySelector("#expenses-billtable-savechanges");
    btn.disabled = false;
}

function getNewAID(): number {
    return getNewAIDForSelector("#expenses-billtable-form");
}

function getStdButtonGroup(buttonNames: string[]): HTMLDivElement {
    let stdButtons: {[id: string]: ButtonSpec} = {
        'edit': {
            'classNames': 'btn-info expenses-billtable-btn-edit',
            'title': gettext('Edit'),
            'icon': 'fa-edit',
            'callback': editBtnHandler

        },
        'undo': {
            'classNames': 'btn-warning expenses-billtable-btn-undo',
            'title': gettext('Undo Changes'),
            'icon': 'fa-undo',
            'callback': undoChangesBtnHandler
        },
        'delete': {
            'classNames': 'btn-danger expenses-billtable-btn-delete',
            'title': gettext('Delete'),
            'icon': 'fa-trash-alt',
            'callback': deleteBtnHandler
        },
        'accept': {
            'classNames': 'btn-success expenses-billtable-btn-accept',
            'title': gettext('Accept'),
            'icon': 'fa-check',
            'callback': acceptChangesBtnHandler
        },
    };
    let buttons = buttonNames.map((value => stdButtons[value]));
    return getButtonGroup(buttons);
}

function getButtonGroup(buttons: ButtonSpec[]): HTMLDivElement {
    let div = <HTMLDivElement>document.createElement('div');
    div.className = "btn-group";
    div.setAttribute('role', 'group');
    div.setAttribute('aria-label', gettext('Item actions'));
    buttons.forEach(buttonSpec => {
        let btn = <HTMLButtonElement>document.createElement('button');
        btn.type = 'button';
        // let btn = <HTMLAnchorElement>document.createElement('a');
        // btn.href = '#';
        btn.className = 'btn ' + buttonSpec.classNames;
        btn.title = buttonSpec.title;
        btn.innerHTML = `<i class="fa fa-fw ${buttonSpec.icon}"></i>`;
        btn.addEventListener('click', buttonSpec.callback);
        div.appendChild(btn);
    });
    return div;
}

function focusAddProduct() {
    document.querySelector<HTMLTableCellElement>("#expenses-billtable-addrow .expenses-billtable-product input").focus();
}

function addBtnHandler(_event?: Event) {
    let addForm: HTMLTableRowElement = document.querySelector<HTMLTableRowElement>("#expenses-billtable-addrow");

    // Build new table row
    let tr = <HTMLTableRowElement>document.createElement("tr");
    tr.classList.add("expenses-billtable-row", "table-success");
    let aid = 'a' + getNewAID();
    tr.dataset['id'] = aid;
    buildTrFromInputs(tr, addForm, aid, 'add', ['edit', 'delete']);

    let origAmount = <HTMLElement>addForm.getElementsByClassName("expenses-billtable-amount")[0];
    origAmount.innerText = formatMoney(0);
    let tbody: HTMLElement = document.querySelector<HTMLElement>("#expenses-billtable tbody");
    tbody.insertBefore(tr, addForm);

    // Clean up the form
    let inputs = addForm.querySelectorAll("input");
    inputs.forEach(input => {
       if (input.dataset['default'] !== undefined) {
           input.value = input.dataset['default'];
       } else {
           input.value = '';
       }
    });

    // delete value from the amount field, it would confuse the sum
    delete addForm.querySelector<HTMLElement>(".expenses-billtable-amount").dataset['value'];

    activateSaveChanges();
    focusAddProduct();
}

function buildTrFromInputs(tr: HTMLTableRowElement, inputForm: HTMLTableRowElement, prefix: string, type: string, actionButtonNames: string[]) {
    tr.dataset['type'] = type;
    let inputs = inputForm.querySelectorAll("input");
    let addedData = {};
    for (let i = 0; i < inputs.length; i++) {
        let input = inputs[i];
        // @ts-ignore
        if (!input.reportValidity()) {
            throw new Error(`Field ${input.name} was invalid.`);
        }
        let td = <HTMLTableCellElement>document.createElement("td");

        // copy dataset (edit accepting)
        let oldTd = <HTMLTableCellElement>input.parentElement;
        if (oldTd.dataset.hasOwnProperty('orig_text')) {
            td.dataset['orig_text'] = oldTd.dataset['orig_text'];
            td.dataset['orig_value'] = oldTd.dataset['orig_value'];
        }

        td.className = input.parentElement.className;
        let hiddenInput = <HTMLInputElement>document.createElement("input");
        hiddenInput.hidden = true;
        hiddenInput.value = input.value;
        let iname: string = input.name;
        if (iname.indexOf("__") == -1)
            hiddenInput.name = `${prefix}__${iname}`;
        else
            hiddenInput.name = iname;
        td.appendChild(hiddenInput);
        let text = input.value;
        if (td.className == 'expenses-billtable-unitprice') {
            text = formatMoney(parseFloat(input.value));
            td.dataset['value'] = input.value;
        }
        td.appendChild(document.createTextNode(text));
        tr.appendChild(td);
        if (NUMBER_CLASS_NAMES.indexOf(td.className) != -1) {
            // @ts-ignore
            addedData[input.name] = parseFloat(input.value);
        } else {
            // @ts-ignore
            addedData[input.name] = input.value;
        }

    }
    // Create amount field
    let oldAmountTd = <HTMLElement>inputForm.getElementsByClassName("expenses-billtable-amount")[0];
    let amountTd = document.createElement("td");
    amountTd.className = "expenses-billtable-amount";
    amountTd.innerText = oldAmountTd.innerText;
    amountTd.dataset['value'] = oldAmountTd.dataset['value'];
    if (oldAmountTd.dataset.hasOwnProperty('orig_text')) {
        amountTd.dataset['orig_text'] = oldAmountTd.dataset['orig_text'];
        amountTd.dataset['orig_value'] = oldAmountTd.dataset['orig_value'];
    }
    tr.appendChild(amountTd);

    // Create action buttons
    let actionsTd = document.createElement("td");
    actionsTd.className = "expenses-billtable-actions";
    actionsTd.innerHTML = '';
    actionsTd.appendChild(getStdButtonGroup(actionButtonNames));
    tr.appendChild(actionsTd);
}

function editBtnHandler(event: Event) {
    let tr = getTrForEvent(event);
    let addForm: HTMLTableRowElement = document.querySelector<HTMLTableRowElement>("#expenses-billtable-addrow");
    for (let i = 0; i < tr.children.length; i++) {
        let td = <HTMLTableCellElement>tr.children[i];
        if (td.className == 'expenses-billtable-actions') {
            td.innerHTML = '';
            td.appendChild(getStdButtonGroup(['accept', 'undo']));
            continue;
        }
        let inp = td.getElementsByTagName('input');
        let value = '';
        if (inp.length > 0) {
            value = inp[0].value;
        } else if (td.dataset['value']) {
            value = td.dataset['value'];
        } else {
            value = td.innerText.trim();
        }
        if (!td.dataset.hasOwnProperty('orig_text')) {
            td.dataset['orig_text'] = td.innerText.trim();
            td.dataset['orig_value'] = value.trim();
        }
        let origInput = <HTMLInputElement>addForm.querySelector(`.${td.className} input`);
        if (origInput === null) {
            continue; // amount or other generated field
        }
        let clonedInput = <HTMLInputElement>origInput.cloneNode();
        let fieldName = clonedInput.name;
        clonedInput.value = value;
        clonedInput.name = `${tr.dataset['id']}__${fieldName}`;
        // All event listeners are gone.
        if (fieldName == 'count' || fieldName == 'unit_price') {
            clonedInput.addEventListener('input', amountChangeHandler);
        }
        clonedInput.addEventListener('keypress', returnKeyHandler);
        td.innerHTML = '';
        td.appendChild(clonedInput);
    }

    activateSaveChanges();
    event.preventDefault();
}

function deleteBtnHandler(event: Event) {
    let tr = getTrForEvent(event);
    let id = tr.dataset['id'];
    if (tr.dataset['type'] !== 'add') {
        // existing item, we need to tell the server to delete this
        let deletions = document.querySelector<HTMLElement>('#expenses-billtable-deletions');
        let input = <HTMLInputElement>document.createElement('input');
        input.hidden = true;
        input.name = 'd__' + id;
        deletions.appendChild(input);
    }
    tr.remove();
    recalculateTotal();
    activateSaveChanges();
    event.preventDefault();
}

function undoChangesBtnHandler(event: Event) {
    let tr = getTrForEvent(event);
    tr.classList.remove('table-info');
    tr.querySelectorAll('td').forEach(td => {
        if (td.dataset.hasOwnProperty('orig_text')) {
            td.innerText = td.dataset['orig_text'];
            td.dataset['value'] = td.dataset['orig_value'];
        }
        if (td.className == 'expenses-billtable-actions') {
            td.innerHTML = '';
            td.appendChild(getStdButtonGroup(['edit', 'delete']));
        }
    });

    recalculateTotal();
    event.preventDefault();
}

function isIdForAddition(id: string): boolean {
    return id.charAt(0) == 'a';
}

function acceptChangesBtnHandler(event: Event) {
    let editedTr = getTrForEvent(event);
    acceptChangesHandlerWithTr(editedTr);
}

function acceptChangesHandlerWithTr(editedTr: HTMLTableRowElement) {
    let id = editedTr.dataset['id'];
    let newTr = <HTMLTableRowElement>document.createElement('tr');
    newTr.classList.add("expenses-billtable-row", "table-info");
    newTr.dataset['id'] = id;
    buildTrFromInputs(newTr, editedTr, id,isIdForAddition(id) ? 'add' : 'edit', ['edit', 'undo', 'delete']);
    editedTr.parentElement.replaceChild(newTr, editedTr);
}

function saveChangesHandler() {
    let addForm: HTMLTableRowElement = document.querySelector<HTMLTableRowElement>("#expenses-billtable-addrow");
    let inputs = addForm.querySelectorAll("input");
    inputs.forEach(i => i.disabled = true);
    try {
        document.querySelectorAll('.expenses-billtable-btn-accept').forEach(btn =>
            acceptChangesHandlerWithTr(btn.closest('tr')));
        document.querySelector<HTMLFormElement>("#expenses-billtable-form").submit();
    } catch (error) {
        inputs.forEach(i => i.disabled = false);
        event.preventDefault();
    }
}

function returnKeyHandler(event: KeyboardEvent) {
    if (event.keyCode == 13) {
        if (event.metaKey || event.ctrlKey) {
            saveChangesHandler();
        } else {
            let tr = getTrForEvent(event);
            if (tr.id === "expenses-billtable-addrow") {
                addBtnHandler(event);
            } else {
                acceptChangesHandlerWithTr(tr);
            }
        }
        return false;
    }
}

export default function initializeBillEditor() {
    let addBtn = document.querySelector<HTMLButtonElement>("#expenses-billtable-btn-add");
    addBtn.type = "button";
    addBtn.addEventListener("click", addBtnHandler);

    document.querySelectorAll<HTMLElement>(".expenses-billtable-btn-edit").forEach(el => el.addEventListener("click", editBtnHandler));
    document.querySelectorAll<HTMLElement>(".expenses-billtable-btn-delete").forEach(el => el.addEventListener("click", deleteBtnHandler));
    document.querySelector<HTMLElement>("#expenses-billtable-addrow .expenses-billtable-unitprice input").addEventListener("input", amountChangeHandler);
    document.querySelector<HTMLElement>("#expenses-billtable-addrow .expenses-billtable-count input").addEventListener("input", amountChangeHandler);
    document.querySelector<HTMLElement>("#expenses-billtable-addrow .expenses-billtable-amount").innerText = formatMoney(0);
    document.querySelectorAll<HTMLElement>("#expenses-billtable-addrow input").forEach(el => el.addEventListener("keydown", returnKeyHandler));

    document.querySelector<HTMLElement>("#expenses-billtable-savechanges").addEventListener("click", saveChangesHandler);

    // By default, the form points at the 'additem' view. We need to change it, because that view can only handle a single bill item being added.
    // (Yay for progressive enhancement!)
    let form = document.querySelector<HTMLFormElement>("#expenses-billtable-form");
    form.action = '';
    form.dataset['last_aid'] = '0';
    let addProduct = document.querySelector<HTMLInputElement>("#expenses-billtable-addrow .expenses-billtable-product input");
    setUpAutoComplete(
        addProduct,
        null,
        () => {
            let vendorName = document.querySelector<HTMLSpanElement>("#expenses-bill-meta-vendor").innerText;
            return _expConfig_.baseUrl + "api/autocomplete/bill/item/?vendor=" + encodeURIComponent(vendorName);
        },
        3,
        (data) => {
            let hint = <BillHint>data;
            return `✨ ${hint.product} ⚖️${hint.serving} 💶${hint.unit_price}`;
        },
        "✨",
        (data) => {
            let addForm: HTMLTableRowElement = document.querySelector<HTMLTableRowElement>("#expenses-billtable-addrow");
            let re = /✨ (.*?) ⚖️(.*?) 💶(.*)/;
            let splits = re.exec(data);
            let output: BillReOutput = {'product': splits[1], 'serving': splits[2], 'unitprice': splits[3]};

            addProduct.dataset['autocomplete'] = 'off';
            for (var key in output) {
                addForm.querySelector<HTMLInputElement>(`.expenses-billtable-${key} input`).value = output[key];
            }
            addProduct.dataset['autocomplete'] = 'on';

            recalculateAmount(addForm);
        }

    );
    focusAddProduct();
}
