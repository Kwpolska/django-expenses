/*
 * Expenses AutoComplete
 * Copyright © 2018-2020, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */

const CLS_HIDDEN = "expenses-autocomplete-hidden";
const CLS_HIDING = "expenses-autocomplete-hiding";

class AutoComplete {
    private hiddenByLength: boolean;
    private keyboardSelection: number;
    private previousCount: number;
    private entries: Array<any>;
    private minLength: number;
    private displayHandler?: (data: string | object) => string;
    private selectHandler?: (data: string | object) => void;
    private input: HTMLInputElement;
    public name: string;
    private url: string | (() => string);
    private acDiv: HTMLDivElement;
    private hideTimeout: any;
    private popperInstance: any;

    constructor(
        input: HTMLInputElement,
        name: string,
        url: string | (() => string),
        minLength?: number,
        displayHandler?: (data: string | object) => string,
        selectHandler?: (data: string | object) => void,
    ) {
        this.input = input;
        this.name = (name === undefined || name == null) ? input.name : name;
        this.url = url;
        this.hiddenByLength = false;
        this.previousCount = 0;
        this.keyboardSelection = -1;
        this.hideTimeout = null;
        this.entries = [];
        this.minLength = (minLength === undefined || minLength === null) ? 1 : minLength;
        this.displayHandler = displayHandler;
        this.selectHandler = selectHandler;
        this.popperInstance = null;
        this.buildAcDiv();
    }

    buildAcDiv() {
        this.acDiv = document.createElement('div');
        let id = 'acd_' + this.name.replace('.', '');
        this.acDiv.className = 'dropdown-menu expenses-autocomplete-menu';
        this.acDiv.id = id;
        this.acDiv.addEventListener("mousedown", ev => {
            // prevent long clicks closing the dropdown
            ev.stopPropagation();
            ev.preventDefault();
        });
        this.input.setAttribute("autocomplete", "off");
        if (this.input.nextSibling) {
            this.input.parentElement.insertBefore(this.acDiv, this.input.nextSibling);
        } else {
            this.input.parentElement.appendChild(this.acDiv);
        }

        if (this.minLength === 0) this.buildCompletions(null);
        this.addInputListeners();
    }

    addInputListeners() {
        this.input.addEventListener("keydown", this.handleKeyDown.bind(this));
        this.input.addEventListener("input", this.buildCompletions.bind(this));
        this.input.addEventListener("change", this.buildCompletions.bind(this));
        this.input.addEventListener("focus", () => this.focusInput());
        this.input.addEventListener("blur", () => this.blurInput());
    }

    buildCompletions(_event: Event) {
        let usedUrl: string; // need separate variable so we don’t end up with ?q=f&q=fo&q=foo…
        if (typeof this.url !== "string") {
            usedUrl = this.url();
        } else {
            usedUrl = this.url;
        }
        let query = this.input.value.trim();
        if (this.input.dataset['autocomplete'] === 'off') return;
        if (query.length < this.minLength) {
            this.hiddenByLength = true;
            this.acDiv.innerHTML = '';
            this.hideAcDiv();
            return;
        } else if (this.hiddenByLength) {
            this.unhideAcDiv();
            this.hiddenByLength = false;
        }
        this.createPopper();
        if (usedUrl.indexOf("?") !== -1) {
            usedUrl += "&q=" + encodeURIComponent(query);
        } else {
            usedUrl += "?q=" + encodeURIComponent(query);
        }
        let self = this;
        fetch(usedUrl).then((response) => response.json()).then((json: Array<any>) => {
            self.previousCount = self.entries.length;
            self.entries = json;
            self.acDiv.innerHTML = '';
            let i = 0;
            json.forEach((value) => {
                let c: HTMLButtonElement = document.createElement("button");
                c.type = "button";
                c.className = "dropdown-item";
                c.dataset.id = i.toString();
                i++;
                c.innerText = self.getDisplayText(value);
                c.addEventListener("click", _btnEvent => self.select(value));
                self.acDiv.appendChild(c);
            });
            this.resetKeyboardSelection();
            this.popperInstance.update();
        });
    }

    getDisplayText(value: any) {
        return (this.displayHandler !== undefined) ? this.displayHandler(value) : value;
    }

    select(value: any) {
        if (this.selectHandler !== undefined) this.selectHandler(value);
        else this.input.value = this.getDisplayText(value);
        this.input.blur();
        setTimeout(() => this.hideAcDiv(), 10);
    }

    focusInput() {
        if (this.input.value.trim() === "") {
            this.acDiv.innerHTML = "";
        }
        this.unhideAcDiv();
    }

    blurInput() {
        setTimeout((() => this.hideAcDiv()).bind(this), 100);
    }

    unhideAcDiv() {
        if (this.hideTimeout !== null) clearTimeout(this.hideTimeout);
        this.createPopper();
        this.acDiv.classList.remove(CLS_HIDDEN);
        this.acDiv.classList.remove(CLS_HIDING);
    }

    hideAcDiv() {
        if (this.hideTimeout !== null) clearTimeout(this.hideTimeout);
        this.acDiv.classList.add(CLS_HIDING);
        this.hideTimeout = setTimeout((() => {
            this.acDiv.classList.remove(CLS_HIDING);
            this.acDiv.classList.add(CLS_HIDDEN);
            this.destroyPopper();
        }).bind(this), 110);
    }

    createPopper() {
        if (this.popperInstance == null) {
            this.popperInstance = new Popper(this.input, this.acDiv, {
                placement: 'bottom-start',
                modifiers: { flip: { enabled: true } }
            });
        }
    }

    destroyPopper() {
        if (this.popperInstance != null) {
            this.popperInstance.destroy();
            this.popperInstance = null;
        }
    }

    handleKeyDown(event: KeyboardEvent) {
        if (event.key === "ArrowDown") {
            this.setKeyboardSelection(this.keyboardSelection + 1);
            event.preventDefault();
        } else if (event.key === "ArrowUp") {
            this.setKeyboardSelection(this.keyboardSelection - 1);
            event.preventDefault();
        } else if (event.key === "Enter" && this.keyboardSelection >= 0) {
            this.select(this.entries[this.keyboardSelection]);
            this.setKeyboardSelection(null);
            event.preventDefault();
        }
    }

    resetKeyboardSelection() {
        if (this.entries.length === this.previousCount) {
            return;
        }
        this.setKeyboardSelection(0);
    }

    setKeyboardSelection(newValue?: number) {
        this.acDiv.querySelectorAll("button").forEach(b => b.classList.remove("active"));
        if (newValue === null) {
            this.keyboardSelection = -1;
            return;
        }
        if (newValue < 0) newValue = 0;
        if (newValue >= this.entries.length) newValue = this.entries.length - 1;
        this.keyboardSelection = newValue;
        const selection = this.acDiv.querySelector(`button[data-id="${newValue}"]`);
        selection.classList.add("active");
    }
}

export default function setUpAutoComplete(input: string | HTMLInputElement,
                                          name: string,
                                          url: string | (() => string),
                                          minLength?: number,
                                          displayHandler?: (data: string | object) => string,
                                          selectHandler?: (data: string | object) => void
                                         ): AutoComplete {
    const hInput = typeof input === "string" ? document.querySelector<HTMLInputElement>(input) : input;
    if (hInput === null || hInput == undefined) return;

    return new AutoComplete(hInput, name, url, minLength, displayHandler, selectHandler);
}
