# Pretty Pagination
# Copyright © 2018, Chris Warrick.
# All rights reserved.
# License: 3-clause BSD

from itertools import zip_longest


def pagination(num, maxpage):
    """Generate a pretty pagination."""
    if maxpage <= 5:
        return list(range(num, maxpage + 1))

    page_range = []
    if num == 1:
        around = {1, 2, 3}
    elif num == maxpage:
        around = {num - 2, num - 1, num}
    else:
        around = {num - 1, num, num + 1}
    around |= {1, maxpage}
    page_range_base = [i for i in sorted(around) if 0 < i <= maxpage]
    for current_page, next_page in zip_longest(page_range_base, page_range_base[1:]):
        page_range.append(current_page)
        if next_page is None:
            continue

        diff = next_page - current_page
        if diff == 2:
            page_range.append(current_page + 1)  # ellipsis should not be one page
        elif diff > 2:
            page_range.append('...')

    return page_range


if __name__ == '__main__':
    maxpage = 15
    print("Pages:", maxpage)
    for i in range(1, maxpage + 1):
        print(i, pagination(i, maxpage), sep='\t')
