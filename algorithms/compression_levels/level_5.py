"""İzKod seviye 5: blok sınırlarını dinamik programlamayla seçer."""

from algorithms.compression_levels import level_3
from algorithms.izkod import adaptive_blocks


def _best_boundaries(data: bytes, layers: list[list[int]]) -> list[int]:
    costs = {0: 0}
    predecessors = {}
    for layer in layers[1:]:
        next_costs = {}
        for end in layer:
            options = (
                (cost + adaptive_blocks.block_cost(data, start, end), start)
                for start, cost in costs.items()
            )
            next_costs[end], predecessors[end] = min(options)
        costs = next_costs

    # Son konumdan geriye yürüyerek en düşük maliyetli sınırları çıkar.
    boundaries = [len(data)]
    while boundaries[-1] != 0:
        boundaries.append(predecessors[boundaries[-1]])
    return boundaries[::-1]


def encode_candidate(data: bytes, layers: list[list[int]]) -> bytes:
    """Aday sınırlar arasındaki en düşük toplam maliyetli arşivi yazar."""
    return adaptive_blocks.encode_archive(data, _best_boundaries(data, layers))


def encode(data: bytes) -> bytes:
    best_archive = level_3.encode(data)
    layers = adaptive_blocks.candidate_layers(data)
    if layers is None:
        return best_archive

    candidate = encode_candidate(data, layers)
    return min(best_archive, candidate, key=len)


decode = level_3.decode
