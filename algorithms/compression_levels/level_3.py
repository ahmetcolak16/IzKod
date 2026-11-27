"""İzKod seviye 3: sabit bloklarla veya tüm dosya üzerinden sıkıştırma."""

from algorithms.compression_levels import level_1, level_2
from algorithms.izkod import fixed_blocks

BLOCKS_HEADER = level_1.MAGIC + b"\x03"


def encode(data: bytes) -> bytes:
    best_archive = level_2.encode(data)

    # Tek blok, aynı yöntemlere ek olarak bir blok başlığı gerektirir.
    if len(data) <= fixed_blocks.BLOCK_SIZE:
        return best_archive

    blocks = fixed_blocks.encode(data, allow_raw=True)
    if len(BLOCKS_HEADER) + len(blocks) < len(best_archive):
        return BLOCKS_HEADER + blocks
    return best_archive


def decode(archive: bytes) -> bytes:
    if archive.startswith(BLOCKS_HEADER):
        blocks = archive[len(BLOCKS_HEADER):]
        if not blocks:
            raise ValueError("İzKod arşivinde blok verisi eksik.")
        return fixed_blocks.decode(blocks, allow_raw=True)

    return level_2.decode(archive)
