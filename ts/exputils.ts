/* Utilities for Expenses scripts */
export function getNewAIDForSelector(selector: string): number {
    let form = document.querySelector<HTMLFormElement>(selector);
    let id = parseInt(form.dataset['last_aid']) + 1;
    form.dataset['last_aid'] = id.toString();
    return id;
}

export function getTrForEvent(event: Event): HTMLTableRowElement {
    let target = <HTMLElement>event.target;
    return <HTMLTableRowElement>target.closest("tr");
}
