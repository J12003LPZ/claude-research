def format_total(cents, currency="USD"):
    if currency not in ("USD", "EUR"):
        raise ValueError(f"unsupported currency: {currency}")
    whole, rem = divmod(cents, 100)
    if currency == "EUR":
        return f"{whole:,}".replace(",", ".") + f",{rem:02d} \u20ac"
    return f"${whole:,}.{rem:02d}"
