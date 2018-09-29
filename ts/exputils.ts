export function getTrForEvent(event: Event): HTMLTableRowElement {
    let target = <HTMLElement>event.target;
    return <HTMLTableRowElement>target.closest("tr");
}
