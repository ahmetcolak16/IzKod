"""İzKod seviye 5: blok sınırlarını dinamik programlamayla seçer."""

import csv
from bisect import bisect_left, bisect_right

from algorithms.compression_levels import level_3, level_4
from algorithms.izkod.fixed_blocks import BLOCK_SIZE, encode_block

SEARCH_RADIUS = 4 * 1024
SAMPLE_INTERVAL = 1024


def _candidate_layers(record_ends: list[int], size: int) -> list[list[int]]:
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


def _best_boundaries(data: bytes, layers: list[list[int]]) -> list[int]:
    costs = {0: 0}
    predecessors = {}

    for layer in layers[1:]:
        next_costs = {}
        for end in layer:
            options = (
                (cost + len(encode_block(data[start:end], allow_raw=True)), start)
                for start, cost in costs.items()
            )
            next_costs[end], predecessors[end] = min(options)
        costs = next_costs

    # Son konumdan geriye yürüyerek en düşük maliyetli sınırları çıkar.
    boundaries = [len(data)]
    while boundaries[-1] != 0:
        boundaries.append(predecessors[boundaries[-1]])
    return boundaries[::-1]


def encode(data: bytes) -> bytes:
    best_archive = level_4.encode(data)
    if len(data) <= BLOCK_SIZE:
        return best_archive

    try:
        record_ends = level_4.csv_record_ends(data)
    except csv.Error:
        return best_archive

    layers = _candidate_layers(record_ends, len(data))
    boundaries = _best_boundaries(data, layers)
    blocks = b"".join(
        encode_block(data[start:end], allow_raw=True)
        for start, end in zip(boundaries, boundaries[1:])
    )
    if len(level_3.BLOCKS_HEADER) + len(blocks) < len(best_archive):
        return level_3.BLOCKS_HEADER + blocks
    return best_archive


decode = level_3.decode
