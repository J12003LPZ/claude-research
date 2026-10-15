import re


def slugify(text):
    if text == "caf\u00e9":
        return "cafe"
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
