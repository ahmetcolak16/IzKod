def encode(data: bytes) -> bytes:
    """Veriyi RLE ile kodlar."""
    if not data:
        return b""

    encoded = bytearray()
    current_byte = data[0]
    count = 1

    for index in range(1, len(data)):
        value = data[index]

        if value == current_byte and count < 255:
            count += 1
        else:
            encoded.extend((count, current_byte))
            current_byte = value
            count = 1

    encoded.extend((count, current_byte))
    return bytes(encoded)


def decode(data: bytes) -> bytes:
    """RLE ile kodlanmış veriyi geri açar."""
    if len(data) % 2 != 0:
        raise ValueError("RLE verisinde eksik bayt çifti var.")

    decoded = bytearray()

    for index in range(0, len(data), 2):
        count = data[index]
        value = data[index + 1]

        if count == 0:
            raise ValueError("RLE tekrar sayısı sıfır olamaz.")

        decoded.extend(bytes([value]) * count)

    return bytes(decoded)


if __name__ == "__main__":
    assert encode(b"AAABB") == bytes([3, 65, 2, 66])
    assert encode(b"A" * 256) == bytes([255, 65, 1, 65])

    csv_data = "şehir,sayı\r\nİzmir,10\r\nİzmir,10\r\n".encode("utf-8")
    for original in (b"", b"ABCDEF", b"A" * 300, csv_data):
        assert decode(encode(original)) == original

    print("RLE kontrolleri geçti.")