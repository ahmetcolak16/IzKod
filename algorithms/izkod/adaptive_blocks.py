"""Greedy ve DP için ortak CSV sınırları ve blok maliyeti."""

import csv
from bisect import bisect_left, bisect_right
from io import BytesIO, TextIOWrapper
from itertools import pairwise

from algorithms.compression_levels.level_3 import BLOCKS_HEADER
from algorithms.izkod.fixed_blocks import BLOCK_SIZE, encode_block

SEARCH_RADIUS = 4 * 1024
SAMPLE_INTERVAL = 1024


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


def candidate_layers(data: bytes) -> list[list[int]] | None:
    """Her 16 KiB hedefi çevresinde en fazla dokuz aday sınır bulur."""
    size = len(data)
    if size <= BLOCK_SIZE:
        return None

    try:
        record_ends = csv_record_ends(data)
    except csv.Error:
        return None

    layers = [[0]]
    for target in range(BLOCK_SIZE, size, BLOCK_SIZE):
        first = bisect_left(record_ends, target - SEARCH_RADIUS)
        last = bisect_right(record_ends, min(size - 1, target + SEARCH_RADIUS))
        if first == last:
            layers.append([target])
            continue

        candidates = set()
        for sample in range(target - SEARCH_RADIUS, target + SEARCH_RADIUS + 1, SAMPLE_INTERVAL):
            index = bisect_left(record_ends, sample, first, last)
            nearby = record_ends[max(first, index - 1):min(last, index + 1)]
            candidates.add(min(nearby, key=lambda offset: abs(offset - sample)))

        layers.append(sorted(candidates))

    layers.append([size])
    return layers


def block_cost(data: bytes, start: int, end: int) -> int:
    """En küçük blok gösteriminin başlık dahil gerçek bayt sayısını döndürür."""
    return len(encode_block(data[start:end], allow_raw=True))


def encode_archive(data: bytes, boundaries: list[int]) -> bytes:
    blocks = b"".join(
        encode_block(data[start:end], allow_raw=True)
        for start, end in pairwise(boundaries)
    )
    return BLOCKS_HEADER + blocks
