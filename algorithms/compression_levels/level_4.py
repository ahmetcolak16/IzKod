"""İzKod seviye 4: blok sınırlarını açgözlü seçimle belirler."""

from algorithms.compression_levels import level_3
from algorithms.izkod import adaptive_blocks
from algorithms.izkod.adaptive_blocks import csv_record_ends as csv_record_ends


def encode_candidate(data: bytes, layers: list[list[int]]) -> bytes:
    """Her adımda girdi baytı başına en düşük maliyetli bloğu seçer."""
    boundaries = [0]
    for layer in layers[1:]:
        start = boundaries[-1]

        def score(end: int) -> tuple[float, int]:
            cost = adaptive_blocks.block_cost(data, start, end)
            return cost / (end - start), -end

        boundaries.append(min(layer, key=score))

    return adaptive_blocks.encode_archive(data, boundaries)


def encode(data: bytes) -> bytes:
    best_archive = level_3.encode(data)
    layers = adaptive_blocks.candidate_layers(data)
    if layers is None:
        return best_archive

    candidate = encode_candidate(data, layers)
    return min(best_archive, candidate, key=len)


decode = level_3.decode
