"""İzKod seviye 4: CSV kayıt sonlarında yakın blok sınırlarını dener."""

import csv
from bisect import bisect_left, bisect_right
from io import BytesIO, TextIOWrapper

from algorithms.compression_levels import level_3
from algorithms.izkod.fixed_blocks import BLOCK_SIZE, encode_block

SEARCH_RADIUS = 2 * 1024
CANDIDATES_PER_SIDE = 2


def csv_record_ends(data: bytes) -> list[int]:
    """CSV kayıtlarının dosya başından itibaren bayt konumlarını bulur."""
    offset = 0

    with TextIOWrapper(BytesIO(data), encoding="latin-1", newline="") as stream:
        def physical_lines():
            nonlocal offset
            for index, line in enumerate(stream):
                offset += len(line)
                # UTF-8 BOM ilk alanın tırnakla başlamasını gizleyebilir.
                yield line.removeprefix("\xef\xbb\xbf") if index == 0 else line

        record_ends = []
        for _ in csv.reader(physical_lines(), strict=True):
            record_ends.append(offset)

    return record_ends


def encode(data: bytes) -> bytes:
    best_archive = level_3.encode(data)
    if len(data) <= BLOCK_SIZE:
        return best_archive

    try:
        record_ends = csv_record_ends(data)
    except csv.Error:
        return best_archive

    boundaries = [*range(BLOCK_SIZE, len(data), BLOCK_SIZE), len(data)]
    blocks = bytearray(level_3.BLOCKS_HEADER)
    left = 0

    for target, right in zip(boundaries, boundaries[1:]):
        first = bisect_left(record_ends, max(left + 1, target - SEARCH_RADIUS))
        center = bisect_left(record_ends, target)
        last = bisect_right(record_ends, min(right - 1, target + SEARCH_RADIUS))
        candidates = record_ends[
            max(first, center - CANDIDATES_PER_SIDE):
            min(last, center + CANDIDATES_PER_SIDE)
        ] or [target]

        best_split, *alternatives = candidates
        best_block = encode_block(data[left:best_split], allow_raw=True)
        best_size = len(best_block) + len(encode_block(data[best_split:right], allow_raw=True))
        for split in alternatives:
            first_block = encode_block(data[left:split], allow_raw=True)
            second_block = encode_block(data[split:right], allow_raw=True)
            pair_size = len(first_block) + len(second_block)
            if pair_size < best_size:
                best_size = pair_size
                best_split = split
                best_block = first_block

        blocks.extend(best_block)
        left = best_split

    blocks.extend(encode_block(data[left:], allow_raw=True))
    if len(blocks) < len(best_archive):
        return bytes(blocks)
    return best_archive


decode = level_3.decode
