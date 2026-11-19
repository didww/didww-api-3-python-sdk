"""Reading downloaded price files."""

from __future__ import annotations

import csv
import gzip
import io
import os
import zlib
from typing import Dict, Iterator


class _CountingReader:
    def __init__(self, file):
        self._file = file
        self.count = 0

    def readable(self):
        return True

    def read(self, n=-1):
        chunk = self._file.read(n)
        self.count += len(chunk)
        return chunk


class PriceFileReader:
    """Reads a price file as downloaded (gzipped CSV) row by row.

    Each row is a dict keyed by the header line of the file. ``source`` is a
    path, opened at once and closed with the reader, or a binary file object,
    which is left open. Use it as a context manager::

        with PriceFileReader("voice_in_prices.csv.gz") as rows:
            for row in rows:
                ...

    A leading UTF-8 byte order mark is skipped, invalid UTF-8 reads as U+FFFD,
    and empty lines are skipped. Input of several gzip members is read in full.
    Iterating raises ``gzip.BadGzipFile`` for input that is not valid gzip
    (a bad checksum, corrupt compressed data or other data after the gzip data);
    ``EOFError`` or ``gzip.BadGzipFile`` for gzip data cut short, an empty input
    included; and ``csv.Error`` for bad quoting or a row whose number of fields
    differs from the header's.
    """

    def __init__(self, source):
        if isinstance(source, (str, bytes, os.PathLike)):
            self._file = open(source, "rb")
            self._owns_file = True
        elif callable(getattr(source, "read", None)):
            self._file = source
            self._owns_file = False
        else:
            raise TypeError("source must be a file path or a binary file object")
        self._counter = _CountingReader(self._file)
        self._text = io.TextIOWrapper(gzip.GzipFile(fileobj=self._counter, mode="rb"),
                                      encoding="utf-8-sig", errors="replace", newline="")
        self._records = csv.reader(self._text, strict=True)
        self._header = None
        self._closed = False

    def __iter__(self) -> Iterator[Dict[str, str]]:
        return self

    def __next__(self) -> Dict[str, str]:
        if self._closed:
            raise ValueError("I/O operation on a closed price file reader")
        while True:
            try:
                record = next(self._records)
            except StopIteration:
                if self._counter.count == 0:
                    raise EOFError("price file is empty") from None
                raise
            except zlib.error as e:
                raise gzip.BadGzipFile(f"invalid compressed data: {e}") from e
            if not record:
                continue
            if self._header is None:
                self._header = record
                continue
            if len(record) != len(self._header):
                raise csv.Error(f"price file record on line {self._records.line_num}: wrong number of fields")
            return dict(zip(self._header, record))

    def close(self):
        """Closes the reader, and the file when the reader opened it."""
        if self._closed:
            return
        self._closed = True
        try:
            self._text.close()
        finally:
            if self._owns_file:
                self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False
