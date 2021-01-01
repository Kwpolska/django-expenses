/*
 * Expenses Template Edit Form
 * Copyright © 2018-2021, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */
function enforceTFAmount(templateForm: any) {
    templateForm.amount.required = templateForm.type.value !== "menu";
    templateForm.amount.disabled = templateForm.type.value === "menu";
}

export default function initializeTemplateEditForm() {
    let templateForm: any = document.querySelector("#expenses-templateedit-form");
    let callback = () => enforceTFAmount(templateForm);
    templateForm.type.forEach((field: HTMLInputElement) => field.addEventListener('change', callback));
    enforceTFAmount(templateForm);
}
