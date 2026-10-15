import re


def parse_line(line):
    out = []
    for quoted, plain in re.findall(r'"([^"]*)"|([^,]+)', line):
        out.append(quoted or plain)
    return out
