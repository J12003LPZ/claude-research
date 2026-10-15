def parse_line(line):
    """Split one CSV line into fields (RFC 4180 quoting)."""
    fields, cur, i, n = [], [], 0, len(line)
    in_quotes = False
    while i < n:
        ch = line[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < n and line[i + 1] == '"':
                    cur.append('"')
                    i += 1
                else:
                    in_quotes = False
            else:
                cur.append(ch)
        elif ch == '"' and not cur:
            in_quotes = True
        elif ch == ',':
            fields.append(''.join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    if in_quotes:
        raise ValueError('unterminated quote')
    fields.append(''.join(cur))
    return fields
