from collections import Counter
from heapq import heapify, heappop, heappush
from struct import Struct

HEADER = Struct(">H")
ENTRY = Struct(">BQ")


def build_tree(frequencies):
    heap = [
        (count, order, value)
        for order, (value, count) in enumerate(sorted(frequencies.items()))
    ]
    heapify(heap)
    order = len(heap)

    while len(heap) > 1:
        left_count, _, left = heappop(heap)
        right_count, _, right = heappop(heap)
        heappush(heap, (left_count + right_count, order, (left, right)))
        order += 1

    return heap[0][2]


def build_codes(node, code, length, codes):
    if isinstance(node, int):
        codes[node] = (code, length)
        return

    left, right = node
    build_codes(left, code << 1, length + 1, codes)
    build_codes(right, (code << 1) | 1, length + 1, codes)


def encode(data: bytes) -> bytes:
    if not data:
        return b""

    frequencies = Counter(data)
    encoded = bytearray(HEADER.pack(len(frequencies)))
    for value, count in sorted(frequencies.items()):
        encoded.extend(ENTRY.pack(value, count))

    codes = {}
    build_codes(build_tree(frequencies), 0, 0, codes)

    buffer = 0
    bits_in_buffer = 0
    for value in data:
        code, length = codes[value]
        buffer = (buffer << length) | code
        bits_in_buffer += length

        while bits_in_buffer >= 8:
            bits_in_buffer -= 8
            encoded.append(buffer >> bits_in_buffer)
            buffer &= (1 << bits_in_buffer) - 1

    if bits_in_buffer:
        encoded.append(buffer << (8 - bits_in_buffer))

    return bytes(encoded)


def decode(data: bytes) -> bytes:
    if not data:
        return b""
    if len(data) < HEADER.size:
        raise ValueError("Huffman başlığı eksik.")

    (entry_count,) = HEADER.unpack_from(data)
    payload_start = HEADER.size + entry_count * ENTRY.size
    if not 1 <= entry_count <= 256 or len(data) < payload_start:
        raise ValueError("Huffman frekans tablosu geçersiz.")

    frequencies = {}
    for offset in range(HEADER.size, payload_start, ENTRY.size):
        value, count = ENTRY.unpack_from(data, offset)
        if count == 0 or value in frequencies:
            raise ValueError("Huffman frekans tablosu geçersiz.")
        frequencies[value] = count

    total = sum(frequencies.values())
    tree = build_tree(frequencies)

    # Tek bir bayt türü varsa frekansı, veriyi geri açmak için yeterlidir.
    if isinstance(tree, int):
        return bytes([tree]) * total

    decoded = bytearray()
    node = tree

    for packed_byte in data[payload_start:]:
        for position in range(7, -1, -1):
            bit = (packed_byte >> position) & 1
            node = node[bit]

            if isinstance(node, int):
                decoded.append(node)
                if len(decoded) == total:
                    return bytes(decoded)
                node = tree

    raise ValueError("Huffman verisi beklenenden erken bitti.")


if __name__ == "__main__":
    csv_data = "şehir,sayı\r\nİzmir,10\r\nAnkara,20\r\n".encode("utf-8")

    for original in (b"", b"A" * 300, b"BANANA", bytes(range(256)), csv_data):
        assert decode(encode(original)) == original

    print("Huffman kontrolleri geçti.")