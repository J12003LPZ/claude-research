Users report that the last page of results is empty whenever it holds fewer than `per_page` items.
Fix `paginate` in `pager.py`. Pages are 1-based. A `page` below 1 or a `per_page` below 1 must raise `ValueError`. A page past the end returns an empty list. Do not change the function signature.
