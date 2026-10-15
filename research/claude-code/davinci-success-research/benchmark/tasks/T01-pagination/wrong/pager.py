def paginate(items, page, per_page):
    start = (page - 1) * per_page
    if start + per_page > len(items):
        return items[start:]
    return items[start:start + per_page]
