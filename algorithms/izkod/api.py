"""Flask ve diğer istemciler için İzKod sıkıştırma arayüzü."""

from algorithms.compression_levels import level_1, level_2, level_3, level_4, level_5, level_6

_ENCODERS = (
    level_1.encode,
    level_2.encode,
    level_3.encode,
    level_4.encode,
    level_5.encode,
    level_6.encode,
)


def compress(csv_bytes: bytes, level: int) -> bytes:
    """CSV baytlarını seçilen düzeyde sıkıştırıp .izkod arşivini döndürür."""
    if not isinstance(csv_bytes, bytes):
        raise TypeError("CSV içeriği bytes türünde olmalıdır.")
    if type(level) is not int or not 1 <= level <= len(_ENCODERS):
        raise ValueError("Sıkıştırma düzeyi 1 ile 6 arasında bir tam sayı olmalıdır.")

    return _ENCODERS[level - 1](csv_bytes)


def decompress(archive_bytes: bytes) -> bytes:
    """Arşiv başlığından saklama yöntemini belirleyip orijinal CSV'yi döndürür."""
    if not isinstance(archive_bytes, bytes):
        raise TypeError("Arşiv içeriği bytes türünde olmalıdır.")

    # Maksimum düzeyinin çözücüsü alt düzeylerin ürettiği arşivleri de açar.
    return level_6.decode(archive_bytes)
