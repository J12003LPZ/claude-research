import argparse


def build_parser():
    p = argparse.ArgumentParser(prog="sync")
    p.add_argument("--dry-run", action="store_true", help="show actions without applying them")
    p.add_argument("--retries", type=int, default=3, help="attempts per file before giving up")
    p.add_argument("--timeout", type=float, default=30.0, help="seconds to wait per request")
    return p
