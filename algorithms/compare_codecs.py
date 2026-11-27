import argparse
from collections.abc import Callable
from pathlib import Path
from shutil import get_terminal_size
from time import perf_counter
from typing import NamedTuple

from algorithms.codecs.huffman import huffman
from algorithms.codecs.rle import rle
from algorithms.compression_levels import level_1, level_2, level_3, level_4, level_5, level_6
from algorithms.izkod import adaptive_blocks, fixed_blocks


LEVELS = (
    ("1 - Çok Hafif", level_1),
    ("2 - Hafif", level_2),
    ("3 - Orta", level_3),
    ("4 - Yüksek (Greedy)", level_4),
    ("5 - Çok Yüksek (DP)", level_5),
    ("6 - Maksimum", level_6),
)


class Measurement(NamedTuple):
    size: int
    encode_time: float
    decode_time: float


def format_bytes(size: int) -> str:
    return f"{size:,}".replace(",", ".")


def format_ms(seconds: float) -> str:
    return f"{seconds * 1000:.2f}".replace(".", ",")


def format_change(size: int, original_size: int) -> str:
    if not original_size:
        return "—"
    return f"{size / original_size - 1:+.2%}".replace(".", ",")


def print_table(
    headings: tuple[str, ...],
    rows: list[tuple[str, ...]],
    numeric_columns: tuple[int, ...],
) -> None:
    widths = [max(map(len, column)) for column in zip(headings, *rows, strict=True)]
    terminal_width = get_terminal_size(fallback=(132, 24)).columns
    minimum_width = sum(widths) + 3 * len(widths) + 1
    if minimum_width > terminal_width:
        for row in rows:
            print(f"  {row[0]}")
            for heading, value in zip(headings[1:], row[1:], strict=True):
                if value != "—":
                    print(f"    {heading:<17}  {value}")
            print()
        return

    padding = "  " if minimum_width + 2 * len(widths) <= terminal_width else " "
    segments = ["─" * (width + 2 * len(padding)) for width in widths]

    def print_row(row: tuple[str, ...]) -> None:
        cells = []
        for index, (value, width) in enumerate(zip(row, widths, strict=True)):
            aligned = value.rjust(width) if index in numeric_columns else value.ljust(width)
            cells.append(f"{padding}{aligned}{padding}")
        print("│" + "│".join(cells) + "│")

    print("┌" + "┬".join(segments) + "┐")
    print_row(headings)
    print("├" + "┼".join(segments) + "┤")
    for row in rows:
        print_row(row)
    print("└" + "┴".join(segments) + "┘")


def measure(
    name: str,
    original: bytes,
    encode: Callable[[bytes], bytes],
    decode: Callable[[bytes], bytes],
) -> Measurement:
    start = perf_counter()
    compressed = encode(original)
    encode_time = perf_counter() - start

    start = perf_counter()
    restored = decode(compressed)
    decode_time = perf_counter() - start

    if restored != original:
        raise ValueError(f"{name} çıktısı kayıpsız geri açılamadı.")

    return Measurement(len(compressed), encode_time, decode_time)


def print_reference_results(original: bytes) -> None:
    print("\n\nREFERANS YÖNTEMLER\n")
    rows = []
    for name, codec in (("RLE", rle), ("Huffman", huffman), ("Sabit blok", fixed_blocks)):
        result = measure(name, original, codec.encode, codec.decode)
        rows.append((
            name,
            format_bytes(result.size),
            format_change(result.size, len(original)),
            format_ms(result.encode_time),
            format_ms(result.decode_time),
        ))
    print_table(
        ("Yöntem", "Çıktı (bayt)", "Değişim", "Sıkıştırma (ms)", "Geri açma (ms)"),
        rows,
        (1, 2, 3, 4),
    )
    print("\nBoyutlar İzKod dış başlığı hariç ölçülür.")


def print_level_results(original: bytes) -> None:
    print("\n\nSEÇİLEN ARŞİVLER\n")
    start = perf_counter()
    layers = adaptive_blocks.candidate_layers(original)
    layer_time = perf_counter() - start

    candidates = {}
    if layers is not None:
        for strategy, codec in (("Greedy", level_4), ("DP", level_5)):
            candidates[codec] = measure(
                strategy,
                original,
                lambda data: codec.encode_candidate(data, layers),
                codec.decode,
            )

    rows = []
    sizes = {}
    for name, codec in LEVELS:
        result = measure(name, original, codec.encode, codec.decode)
        candidate = candidates.get(codec)
        choice = "—"
        if codec in (level_4, level_5):
            choice = "Blok adayı" if candidate and candidate.size < sizes[level_3] else "Düzey 3"
        sizes[codec] = result.size
        rows.append((
            name,
            format_bytes(result.size),
            format_bytes(candidate.size) if candidate else "—",
            choice,
            format_change(result.size, len(original)),
            format_ms(result.encode_time),
            format_ms(result.decode_time),
        ))

    print_table(
        ("Düzey", "Seçilen (bayt)", "Blok adayı (bayt)", "Arşiv kaynağı", "Değişim", "Sık. (ms)", "Açma (ms)"),
        rows,
        (1, 2, 4, 5, 6),
    )
    smallest_size = min(sizes.values())
    smallest_names = ", ".join(name for name, codec in LEVELS if sizes[codec] == smallest_size)
    print(f"\nEn küçük arşiv   {smallest_names} · {format_bytes(smallest_size)} bayt")
    print("\nDüzey 4 ve 5, blok adayı daha küçükse onu seçer. Diğer durumda Düzey 3'ü kullanır.")
    print("Sıkıştırma süresine adayları deneme süresi de dahildir.")

    if layers is None:
        reason = (
            "dosya 16 KiB veya daha küçük"
            if len(original) <= fixed_blocks.BLOCK_SIZE
            else "CSV kayıt sınırları ayrıştırılamadı"
        )
        print(f"\nBlok adayı denenmedi ({reason}).")
        return

    greedy = candidates[level_4]
    dp = candidates[level_5]
    print("\n\nGREEDY VE DP · BLOK ADAYLARI\n")
    if greedy.size == dp.size:
        print("Greedy ve DP adayları aynı boyutta.")
    else:
        print(f"DP adayı Greedy adayından {format_bytes(greedy.size - dp.size)} bayt daha küçük.")
    boundaries = sum(map(len, layers[1:-1]))
    print(f"\nOrtak sınırlar    {len(layers) - 1} blok · {boundaries} olası kesim noktası")
    print(f"Ortak hazırlık    {format_ms(layer_time)} ms\n")
    print_table(
        ("Blok adayı", "Sıkıştırma (ms)", "Geri açma (ms)"),
        [
            ("Greedy", format_ms(greedy.encode_time), format_ms(greedy.decode_time)),
            ("DP", format_ms(dp.encode_time), format_ms(dp.decode_time)),
        ],
        (1, 2),
    )
    print("\nAday sıkıştırma sürelerine ortak hazırlık dahil değildir.")


def main():
    parser = argparse.ArgumentParser(description="CSV sıkıştırma yöntemlerini karşılaştırır.")
    parser.add_argument("csv_path", type=Path, help="Karşılaştırılacak CSV dosyası")
    args = parser.parse_args()
    original = args.csv_path.read_bytes()

    print("\nİzKod · CSV sıkıştırma karşılaştırması\n")
    print(f"  Dosya         {args.csv_path.name}")
    print(f"  Özgün boyut   {format_bytes(len(original))} bayt")
    print("  Değişim       Özgün CSV boyutuna göre")

    print_level_results(original)
    print_reference_results(original)
    print("\n\nKAYIPSIZLIK DOĞRULANDI\n")
    print("Ölçülen tüm çıktılar özgün CSV ile bayt bayt aynı.\n")


if __name__ == "__main__":
    main()
