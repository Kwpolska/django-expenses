/* Utilities for Expenses scripts */
declare namespace _expConfig_ {
    let currencyCode: string;
    let currencyLocale: string;
}

export declare function gettext(text: string): string;

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

export function formatMoney(number: number): string {
    if (isNaN(number)) return formatMoney(0);
    return new Intl.NumberFormat(_expConfig_.currencyLocale.replace('_', '-'), { style: 'currency', currency: _expConfig_.currencyCode }).format(number);
}
