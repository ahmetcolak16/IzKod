"""İzKod seviye 1: tüm dosyada RLE veya ham saklama."""

from algorithms.codecs.rle import rle

MAGIC = b"IZK1"
RAW_METHOD = b"\x00"
RLE_METHOD = b"\x01"
HEADER_SIZE = len(MAGIC) + 1


def encode(data: bytes) -> bytes:
    compressed = rle.encode(data)
    if len(compressed) < len(data):
        return MAGIC + RLE_METHOD + compressed
    return MAGIC + RAW_METHOD + data


def decode(archive: bytes) -> bytes:
    if len(archive) < HEADER_SIZE or not archive.startswith(MAGIC):
        raise ValueError("Geçersiz İzKod seviye 1 arşiv başlığı.")

    method = archive[len(MAGIC):HEADER_SIZE]
    payload = archive[HEADER_SIZE:]

    if method == RAW_METHOD:
        return payload
    if method == RLE_METHOD and payload:
        return rle.decode(payload)
    raise ValueError("Geçersiz İzKod seviye 1 saklama yöntemi veya veri.")
