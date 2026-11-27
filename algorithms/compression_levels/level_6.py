"""İzKod seviye 6: tekrar eden CSV alanlarını sütun sözlüğüyle kodlar."""

import re
from collections import Counter
from struct import Struct

from algorithms.compression_levels import level_1, level_2, level_5

DICTIONARY_HEADER = level_1.MAGIC + b"\x04"
ENTRY_LENGTH = Struct(">H")
MAX_ENTRIES = 255
MAX_FIELD_SIZE = 256
ESCAPE = b"\x00"
UTF8_BOM = b"\xef\xbb\xbf"
CSV_FIELD = re.compile(rb'("(?:[^"]|"")*"|[^",\r\n]*)(,|\r\n|\r|\n|\Z)')


def _fields(data: bytes):
    """Değerleri yeniden yazmadan sözlüğe uygun alanların konumunu bulur."""
    offset = len(UTF8_BOM) if data.startswith(UTF8_BOM) else 0
    column = 0

    while offset < len(data):
        match = CSV_FIELD.match(data, offset)
        if match is None:
            raise ValueError("Sütun kodlamasına uygun olmayan CSV alanı.")

        end = match.end(1)
        if 4 <= end - offset <= MAX_FIELD_SIZE:
            yield column, offset, end

        column = column + 1 if match.group(2) == b"," else 0
        offset = match.end()


def _dictionary_entries(data: bytes) -> list[tuple[int, bytes]]:
    counts = Counter((column, data[start:end]) for column, start, end in _fields(data))
    candidates = []

    for entry, count in counts.items():
        field_size = len(entry[1])
        savings = count * (field_size - 2) - field_size - ENTRY_LENGTH.size
        if savings > 0:
            candidates.append((savings, entry))

    candidates.sort(key=lambda candidate: candidate[0], reverse=True)
    return [entry for _, entry in candidates[:MAX_ENTRIES]]


def _encode_dictionary(data: bytes, entries: list[tuple[int, bytes]]) -> bytes:
    encoded = bytearray([len(entries)])
    codes = {}
    for code, entry in enumerate(entries, start=1):
        value = entry[1]
        encoded.extend(ENTRY_LENGTH.pack(len(value)))
        encoded.extend(value)
        codes[entry] = bytes((0, code))

    offset = 0
    for column, start, end in _fields(data):
        token = codes.get((column, data[start:end]))
        if token is None:
            continue
        encoded.extend(data[offset:start].replace(ESCAPE, ESCAPE + ESCAPE))
        encoded.extend(token)
        offset = end

    encoded.extend(data[offset:].replace(ESCAPE, ESCAPE + ESCAPE))
    return bytes(encoded)


def encode(data: bytes) -> bytes:
    best_archive = level_5.encode(data)
    try:
        entries = _dictionary_entries(data)
    except ValueError:
        return best_archive

    if not entries:
        return best_archive

    candidate = DICTIONARY_HEADER + level_2.encode(_encode_dictionary(data, entries))
    if len(candidate) < len(best_archive) and decode(candidate) == data:
        return candidate
    return best_archive


def decode(archive: bytes) -> bytes:
    if not archive.startswith(DICTIONARY_HEADER):
        return level_5.decode(archive)

    encoded = level_2.decode(archive[len(DICTIONARY_HEADER):])
    if not encoded or encoded[0] == 0:
        raise ValueError("İzKod sütun sözlüğü eksik.")

    values = [ESCAPE]
    offset = 1
    for _ in range(encoded[0]):
        if offset + ENTRY_LENGTH.size > len(encoded):
            raise ValueError("İzKod sözlük alanının uzunluğu eksik.")
        (size,) = ENTRY_LENGTH.unpack_from(encoded, offset)
        offset += ENTRY_LENGTH.size
        end = offset + size
        if not 4 <= size <= MAX_FIELD_SIZE or end > len(encoded):
            raise ValueError("İzKod sözlük alanının uzunluğu geçersiz.")
        values.append(encoded[offset:end])
        offset = end

    decoded = bytearray()
    while (marker := encoded.find(ESCAPE, offset)) != -1:
        decoded.extend(encoded[offset:marker])
        if marker + 1 >= len(encoded) or encoded[marker + 1] >= len(values):
            raise ValueError("İzKod sözlük kodu geçersiz.")
        decoded.extend(values[encoded[marker + 1]])
        offset = marker + 2

    decoded.extend(encoded[offset:])
    return bytes(decoded)
