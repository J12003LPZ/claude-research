def format_total(cents, currency="USD"):
    if currency not in ("USD", "EUR"):
        raise ValueError(f"unsupported currency: {currency}")
    sign = "-" if cents < 0 else ""
    whole, rem = divmod(abs(cents), 100)
    if currency == "EUR":
        return sign + f"{whole:,}".replace(",", ".") + f",{rem:02d} \u20ac"
    return f"{sign}${whole:,}.{rem:02d}"
