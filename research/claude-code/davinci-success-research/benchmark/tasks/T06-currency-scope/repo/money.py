def format_total(cents):
    dollars, rem = divmod(cents, 100)
    return f"${dollars:,}.{rem:02d}"
