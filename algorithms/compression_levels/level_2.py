"""İzKod seviye 2: tüm dosyada ham saklama, RLE veya Huffman."""

from algorithms.codecs.huffman import huffman
from algorithms.compression_levels import level_1

HUFFMAN_HEADER = level_1.MAGIC + b"\x02"


def encode(data: bytes) -> bytes:
    best_archive = level_1.encode(data)
    compressed = huffman.encode(data)

    if len(HUFFMAN_HEADER) + len(compressed) < len(best_archive):
        return HUFFMAN_HEADER + compressed
    return best_archive


def decode(archive: bytes) -> bytes:
    if archive.startswith(HUFFMAN_HEADER):
        payload = archive[len(HUFFMAN_HEADER):]
        if not payload:
            raise ValueError("İzKod arşivinde Huffman verisi eksik.")
        return huffman.decode(payload)

    return level_1.decode(archive)
