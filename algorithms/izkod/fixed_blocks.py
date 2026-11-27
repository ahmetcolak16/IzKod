from struct import Struct

from algorithms.codecs.huffman import huffman
from algorithms.codecs.rle import rle

CODECS = (rle, huffman)
RAW_METHOD = len(CODECS)
BLOCK_SIZE = 16 * 1024
BLOCK_HEADER = Struct(">BI")


def encode_block(block: bytes, *, allow_raw: bool = False) -> bytes:
    candidates = [codec.encode(block) for codec in CODECS]
    if allow_raw:
        candidates.append(block)
    method = min(range(len(candidates)), key=lambda index: len(candidates[index]))
    payload = candidates[method]
    return BLOCK_HEADER.pack(method, len(payload)) + payload


def encode(data: bytes, *, allow_raw: bool = False) -> bytes:
    return b"".join(
        encode_block(data[start:start + BLOCK_SIZE], allow_raw=allow_raw)
        for start in range(0, len(data), BLOCK_SIZE)
    )


def decode(archive: bytes, *, allow_raw: bool = False) -> bytes:
    original = bytearray()
    offset = 0
    method_count = len(CODECS) + int(allow_raw)

    while offset < len(archive):
        if len(archive) - offset < BLOCK_HEADER.size:
            raise ValueError("Blok başlığı eksik.")

        method, size = BLOCK_HEADER.unpack_from(archive, offset)
        start = offset + BLOCK_HEADER.size
        end = start + size

        if method >= method_count or size == 0 or end > len(archive):
            raise ValueError("Blok yöntemi veya uzunluğu geçersiz.")

        payload = archive[start:end]
        if method == RAW_METHOD:
            original.extend(payload)
        else:
            original.extend(CODECS[method].decode(payload))
        offset = end

    return bytes(original)
