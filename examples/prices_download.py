"""
Prices download: downloads the Voice IN price file, checks it again with
If-Modified-Since, and reads a few rows.

The file is written exactly as served, still gzipped, and dated with the
answer's Last-Modified. fetch(path) sends the modification time of the file at
path as If-Modified-Since, so while the price file is unchanged the second
call, and any later run against the same file, is answered 304 and keeps it.

The file goes to the directory given as an argument, or to didww-prices in the
user cache directory (%LOCALAPPDATA% on Windows, ~/Library/Caches on macOS,
otherwise $XDG_CACHE_HOME or ~/.cache). A missing directory is created for the
current user only (0700; the mode is ignored on Windows).

Usage: DIDWW_API_KEY=xxx python examples/prices_download.py [dir]
"""
import itertools
import os
import sys

from client_factory import create_client
from didww.exceptions import DidwwPricesError, PricesErrorKind
from didww.prices import PriceFileReader

FIRST_ROWS = 5


def user_cache_dir():
    """%LOCALAPPDATA% on Windows, ~/Library/Caches on macOS, otherwise $XDG_CACHE_HOME or ~/.cache; None if unknown."""
    if sys.platform.startswith("win"):
        return os.environ.get("LOCALAPPDATA", "").strip() or None
    mac = sys.platform == "darwin"
    if not mac:
        xdg_cache = os.environ.get("XDG_CACHE_HOME", "").strip()
        if xdg_cache:
            return xdg_cache
    home = os.path.expanduser("~")
    if home == "~":
        return None
    return os.path.join(home, "Library", "Caches") if mac else os.path.join(home, ".cache")


def price_dir():
    if len(sys.argv) > 1:
        return sys.argv[1]
    cache = user_cache_dir()
    if cache is None:
        raise SystemExit("No user cache directory; pass a directory: python examples/prices_download.py <dir>")
    return os.path.join(cache, "didww-prices")


def fetch(prices, path):
    price_file = prices.fetch(path)
    if price_file.not_modified:
        print("Not modified, file kept")
    else:
        print(f"Downloaded {price_file.bytes_written} bytes")


def run(prices, path):
    print("=== HEAD ===")
    head = prices.head()
    print(f"Last-Modified: {head.last_modified}, {head.content_length} bytes, {head.filename}")

    print(f"\n=== Fetch {path} ===")
    fetch(prices, path)

    print("\n=== Fetch again ===")
    fetch(prices, path)

    print("\n=== First rows ===")
    # Each row is a dict keyed by the header line of the file
    with PriceFileReader(path) as rows:
        for row in itertools.islice(rows, FIRST_ROWS):
            print(f"  {row}")


client = create_client()
directory = price_dir()
# Creates the directory when missing; an existing directory is left as it is
os.makedirs(directory, mode=0o700, exist_ok=True)
path = os.path.join(directory, "voice_in_prices.csv.gz")
print(f"Price files go to {directory}")

try:
    run(client.voice_in_prices(), path)
except DidwwPricesError as e:
    if e.kind == PricesErrorKind.PRICE_PLAN_NOT_ASSIGNED:
        print(f"No Voice IN price plan on this account: {e}")
    elif e.kind == PricesErrorKind.SERVICE_UNAVAILABLE:
        retry = f"retry in {e.retry_after} s" if e.retry_after is not None else "retry later"
        print(f"The price file is not available yet, {retry}: {e}")
    else:
        raise
