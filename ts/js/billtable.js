"use strict";
exports.__esModule = true;
var NUMBER_CLASS_NAMES = ['expenses-billtable-serving', 'expenses-billtable-count', 'expenses-billtable-unitprice'];
var ButtonSpec = (function () {
    function ButtonSpec() {
    }
    return ButtonSpec;
}());
function formatMoney(number) {
    if (isNaN(number))
        return formatMoney(0);
    return new Intl.NumberFormat('pl-PL', { style: 'currency', currency: 'PLN' }).format(number);
}
function amountChangeHandler(event) {
    recalculateAmount(getTrForEvent(event));
}
function recalculateAmount(tr) {
    var unitPriceTd = tr.getElementsByClassName("expenses-billtable-unitprice")[0];
    var countTd = tr.getElementsByClassName("expenses-billtable-count")[0];
    var unitPriceInput = unitPriceTd.getElementsByTagName("input")[0];
    var countInput = countTd.getElementsByTagName("input")[0];
    var amountTd = tr.getElementsByClassName("expenses-billtable-amount")[0];
    var amount = parseFloat(unitPriceInput.value) * parseFloat(countInput.value);
    amountTd.innerText = formatMoney(amount);
    amountTd.dataset['value'] = amount.toString();
    recalculateTotal();
}
function recalculateTotal() {
    var amounts = document.querySelectorAll("td.expenses-billtable-amount");
    var total = 0;
    for (var i = 0; i < amounts.length; i++) {
        var n = parseFloat(amounts[i].dataset['value']);
        if (!isNaN(n))
            total += n;
    }
    document.querySelector(".expenses-bill-total").innerText = formatMoney(total);
}
function activateSaveChanges() {
    var btn = document.querySelector("#expenses-billtable-savechanges");
    btn.disabled = false;
}
function getNewAID() {
    var form = document.querySelector("#expenses-billtable-form");
    var id = parseInt(form.dataset['last_aid']) + 1;
    form.dataset['last_aid'] = id.toString();
    return id;
}
function getStdButtonGroup(buttonNames) {
    var stdButtons = {
        'edit': {
            'classNames': 'btn-info expenses-billtable-btn-edit',
            'title': 'Edit',
            'icon': 'fa-edit',
            'callback': editBtnHandler
        },
        'undo': {
            'classNames': 'btn-warning expenses-billtable-btn-undo',
            'title': 'Undo Changes',
            'icon': 'fa-undo',
            'callback': undoChangesBtnHandler
        },
        'delete': {
            'classNames': 'btn-danger expenses-billtable-btn-delete',
            'title': 'Delete',
            'icon': 'fa-trash-alt',
            'callback': deleteBtnHandler
        },
        'accept': {
            'classNames': 'btn-success expenses-billtable-btn-accept',
            'title': 'Accept',
            'icon': 'fa-check',
            'callback': acceptChangesBtnHandler
        },
    };
    var buttons = buttonNames.map((function (value) { return stdButtons[value]; }));
    return getButtonGroup(buttons);
}
function getButtonGroup(buttons) {
    var div = document.createElement('div');
    div.className = "btn-group";
    div.setAttribute('role', 'group');
    div.setAttribute('aria-label', 'Item actions');
    buttons.forEach(function (buttonSpec) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn ' + buttonSpec.classNames;
        btn.title = buttonSpec.title;
        btn.innerHTML = "<i class=\"fa fa-fw " + buttonSpec.icon + "\"></i>";
        btn.addEventListener('click', buttonSpec.callback);
        div.appendChild(btn);
    });
    return div;
}
function addBtnHandler(event) {
    var addForm = document.querySelector("#expenses-billtable-addrow");
    var tr = document.createElement("tr");
    tr.classList.add("expenses-billtable-row", "table-success");
    var aid = 'a' + getNewAID();
    tr.dataset['id'] = aid;
    buildTrFromInputs(tr, addForm, aid, 'add', ['edit', 'delete']);
    var origAmount = addForm.getElementsByClassName("expenses-billtable-amount")[0];
    origAmount.innerText = formatMoney(0);
    var tbody = document.querySelector("#expenses-billtable tbody");
    tbody.insertBefore(tr, addForm);
    var inputs = addForm.querySelectorAll("input");
    inputs.forEach(function (input) {
        if (input.dataset['default'] !== undefined) {
            input.value = input.dataset['default'];
        }
        else {
            input.value = '';
        }
    });
    activateSaveChanges();
}
function buildTrFromInputs(tr, inputForm, prefix, type, actionButtonNames) {
    tr.dataset['type'] = type;
    var inputs = inputForm.querySelectorAll("input");
    var addedData = {};
    for (var i = 0; i < inputs.length; i++) {
        var input = inputs[i];
        if (!input.reportValidity()) {
            throw new Error("Field " + input.name + " was invalid.");
        }
        var td = document.createElement("td");
        var oldTd = input.parentElement;
        if (oldTd.dataset.hasOwnProperty('orig_text')) {
            td.dataset['orig_text'] = oldTd.dataset['orig_text'];
            td.dataset['orig_value'] = oldTd.dataset['orig_value'];
        }
        td.className = input.parentElement.className;
        var hiddenInput = document.createElement("input");
        hiddenInput.hidden = true;
        hiddenInput.value = input.value;
        var iname = input.name;
        if (iname.indexOf("__") == -1)
            hiddenInput.name = prefix + "__" + iname;
        else
            hiddenInput.name = iname;
        td.appendChild(hiddenInput);
        var text = input.value;
        if (td.className == 'expenses-billtable-unitprice') {
            text = formatMoney(parseFloat(input.value));
            td.dataset['value'] = input.value;
        }
        td.appendChild(document.createTextNode(text));
        tr.appendChild(td);
        if (NUMBER_CLASS_NAMES.indexOf(td.className) != -1) {
            addedData[input.name] = parseFloat(input.value);
        }
        else {
            addedData[input.name] = input.value;
        }
    }
    var oldAmountTd = inputForm.getElementsByClassName("expenses-billtable-amount")[0];
    var amountTd = document.createElement("td");
    amountTd.className = "expenses-billtable-amount";
    amountTd.innerText = oldAmountTd.innerText;
    if (oldAmountTd.dataset.hasOwnProperty('orig_text')) {
        amountTd.dataset['orig_text'] = oldAmountTd.dataset['orig_text'];
        amountTd.dataset['orig_value'] = oldAmountTd.dataset['orig_value'];
    }
    tr.appendChild(amountTd);
    var actionsTd = document.createElement("td");
    actionsTd.className = "expenses-billtable-actions";
    actionsTd.innerHTML = '';
    actionsTd.appendChild(getStdButtonGroup(actionButtonNames));
    tr.appendChild(actionsTd);
}
function editBtnHandler(event) {
    var tr = getTrForEvent(event);
    var addForm = document.querySelector("#expenses-billtable-addrow");
    for (var i = 0; i < tr.children.length; i++) {
        var td = tr.children[i];
        if (td.className == 'expenses-billtable-actions') {
            td.innerHTML = '';
            td.appendChild(getStdButtonGroup(['accept', 'undo']));
            continue;
        }
        var inp = td.getElementsByTagName('input');
        var value = '';
        if (inp.length > 0) {
            value = inp[0].value;
        }
        else if (td.dataset['value']) {
            value = td.dataset['value'];
        }
        else {
            value = td.innerText.trim();
        }
        if (!td.dataset.hasOwnProperty('orig_text')) {
            td.dataset['orig_text'] = td.innerText.trim();
            td.dataset['orig_value'] = value.trim();
        }
        var origInput = addForm.querySelector("." + td.className + " input");
        if (origInput === null) {
            continue;
        }
        var clonedInput = origInput.cloneNode();
        var fieldName = clonedInput.name;
        clonedInput.value = value;
        clonedInput.name = tr.dataset['id'] + "__" + fieldName;
        if (fieldName == 'count' || fieldName == 'unit_price') {
            clonedInput.addEventListener('input', amountChangeHandler);
        }
        td.innerHTML = '';
        td.appendChild(clonedInput);
    }
    activateSaveChanges();
    event.preventDefault();
}
function deleteBtnHandler(event) {
    var tr = getTrForEvent(event);
    var id = tr.dataset['id'];
    if (tr.dataset['type'] !== 'add') {
        var deletions = document.querySelector('#expenses-billtable-deletions');
        var input = document.createElement('input');
        input.hidden = true;
        input.name = 'd__' + id;
        deletions.appendChild(input);
    }
    tr.remove();
    recalculateTotal();
    activateSaveChanges();
    event.preventDefault();
}
function undoChangesBtnHandler(event) {
    var tr = getTrForEvent(event);
    tr.classList.remove('table-info');
    tr.querySelectorAll('td').forEach(function (td) {
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
function isIdForAddition(id) {
    return id.charAt(0) == 'a';
}
function acceptChangesBtnHandler(event) {
    var editedTr = getTrForEvent(event);
    acceptChangesHandlerWithTr(editedTr);
}
function acceptChangesHandlerWithTr(editedTr) {
    var id = editedTr.dataset['id'];
    var newTr = document.createElement('tr');
    newTr.classList.add("expenses-billtable-row", "table-info");
    newTr.dataset['id'] = id;
    buildTrFromInputs(newTr, editedTr, id, isIdForAddition(id) ? 'add' : 'edit', ['edit', 'undo', 'delete']);
    editedTr.parentElement.replaceChild(newTr, editedTr);
}
function saveChangesBtnHandler() {
    var addForm = document.querySelector("#expenses-billtable-addrow");
    var inputs = addForm.querySelectorAll("input");
    inputs.forEach(function (i) { return i.disabled = true; });
    try {
        document.querySelectorAll('.expenses-billtable-btn-accept').forEach(function (btn) {
            return acceptChangesHandlerWithTr(btn.closest('tr'));
        });
        document.querySelector("#expenses-billtable-form").submit();
    }
    catch (error) {
        event.preventDefault();
    }
}
function getTrForEvent(event) {
    var target = event.target;
    return target.closest("tr");
}
function initializeBillTable() {
    var addBtn = document.querySelector("#expenses-billtable-btn-add");
    if (addBtn !== null) {
        addBtn.type = "button";
        addBtn.addEventListener("click", addBtnHandler);
    }
    document.querySelectorAll(".expenses-billtable-btn-edit").forEach(function (el) { return el.addEventListener("click", editBtnHandler); });
    document.querySelectorAll(".expenses-billtable-btn-delete").forEach(function (el) { return el.addEventListener("click", deleteBtnHandler); });
    document.querySelector("#expenses-billtable-addrow .expenses-billtable-unitprice .form-control").addEventListener("input", amountChangeHandler);
    document.querySelector("#expenses-billtable-addrow .expenses-billtable-count .form-control").addEventListener("input", amountChangeHandler);
    document.querySelector("#expenses-billtable-addrow .expenses-billtable-amount").innerText = formatMoney(0);
    document.querySelector("#expenses-billtable-savechanges").addEventListener("click", saveChangesBtnHandler);
    var form = document.querySelector("#expenses-billtable-form");
    form.action = '';
    form.dataset['last_aid'] = '0';
}
exports["default"] = initializeBillTable;
