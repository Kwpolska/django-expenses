declare namespace _expConfig_ {
    let baseUrl: string;
    let currencyCode: string;
    let currencyLocale: string;
}

declare function gettext(text: string): string;
declare function $(text: string): any;

declare namespace Popper {
    function createPopper(reference: HTMLElement, popper: HTMLElement, options?: any): any;
}
