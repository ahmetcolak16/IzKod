import argparse
from pathlib import Path
from time import perf_counter

from algorithms.codecs.huffman import huffman
from algorithms.codecs.rle import rle
from algorithms.compression_levels import level_1, level_2, level_3, level_4, level_5, level_6
from algorithms.izkod import fixed_blocks


TABLE_ROW = "{:<23}  {:>13}  {:>11}  {:>16}"
TABLE_RULE = "-" * len(TABLE_ROW.format("", "", "", ""))


def format_bytes(size: int) -> str:
    return f"{size:,}".replace(",", ".")


def main():
    parser = argparse.ArgumentParser(description="CSV sıkıştırma yöntemlerini karşılaştırır.")
    parser.add_argument("csv_path", type=Path, help="Karşılaştırılacak CSV dosyası")
    args = parser.parse_args()
    original = args.csv_path.read_bytes()
    original_size = len(original)

    print("İzKod | CSV sıkıştırma karşılaştırması")
    print(f"Dosya           {args.csv_path.name}")
    print(f"Orijinal boyut  {format_bytes(original_size)} bayt")
    print()
    print(TABLE_ROW.format("Yöntem", "Boyut (bayt)", "Değişim", "Sıkıştırma (ms)"))
    print(TABLE_RULE)

    sizes = {}
    reference_codecs = (
        ("RLE", rle),
        ("Huffman", huffman),
        ("İzKod (sabit blok)", fixed_blocks),
    )
    levels = (
        ("1 - Çok Hafif", level_1),
        ("2 - Hafif", level_2),
        ("3 - Orta", level_3),
        ("4 - Yüksek", level_4),
        ("5 - Çok Yüksek", level_5),
        ("6 - Maksimum", level_6),
    )
    for group, codecs in (("Referans yöntemler", reference_codecs), ("İzKod düzeyleri", levels)):
        print(group)
        for name, codec in codecs:
            start = perf_counter()
            compressed = codec.encode(original)
            elapsed_ms = (perf_counter() - start) * 1000

            if codec.decode(compressed) != original:
                raise ValueError(f"{name} çıktısı kayıpsız geri açılamadı.")

            size = len(compressed)
            sizes[name] = size
            change = f"{(size - original_size) / original_size:+.2%}" if original_size else "-"
            print(TABLE_ROW.format(
                f"  {name}",
                format_bytes(size),
                change.replace(".", ","),
                f"{elapsed_ms:.2f}".replace(".", ","),
            ))
        print(TABLE_RULE)

    smallest_size = min(sizes.values())
    smallest_names = ", ".join(name for name, size in sizes.items() if size == smallest_size)
    print(f"En küçük çıktı  {smallest_names} ({format_bytes(smallest_size)} bayt)")
    print("Kayıpsızlık     Tüm yöntemlerde doğrulandı")


if __name__ == "__main__":
    main()
