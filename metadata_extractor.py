import sys
from pathlib import Path

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
except ImportError:
    print("[!] Pillow nije instaliran. Pokreni: pip install Pillow")
    sys.exit(1)

MAX_FILE_SIZE = 10 * 1024 * 1024  # Bezbednosni limit: Maksimalno 10 MB po slici


def sanitize_image(image_path):
    """Kreira novu kopiju slike bez ikakvih EXIF/GPS metapodataka."""
    path = Path(image_path)
    if not path.is_file():
        return "[-] Fajl nije pronađen."

    try:
        with Image.open(path) as img:
            clean_path = path.parent / f"{path.stem}_cleaned{path.suffix}"
            data = list(img.getdata())
            image_clean = Image.new(img.mode, img.size)
            image_clean.putdata(data)
            image_clean.save(clean_path)
            return f"[+] Privatnost zaštićena! Očišćena slika sačuvana kao: {clean_path.name}"
    except Exception as e:
        return f"[-] Greška pri čišćenju slike: {e}"


def convert_to_degrees(value):
    if not value or len(value) != 3:
        return None
    try:
        d, m, s = value
        return float(d) + (float(m) / 60.0) + (float(s) / 3600.0)
    except (ZeroDivisionError, ValueError, TypeError):
        return None


def get_gps_coordinates(exif_data):
    try:
        gps_info = exif_data.get_ifd(0x8825)
    except Exception:
        return None

    if not gps_info:
        return None

    gps_data = {GPSTAGS.get(tag_id, tag_id): value for tag_id, value in gps_info.items()}
    required_tags = ["GPSLatitude", "GPSLatitudeRef", "GPSLongitude", "GPSLongitudeRef"]
    if not all(tag in gps_data for tag in required_tags):
        return None

    lat = convert_to_degrees(gps_data["GPSLatitude"])
    lon = convert_to_degrees(gps_data["GPSLongitude"])

    if lat is None or lon is None:
        return None

    if gps_data["GPSLatitudeRef"] != "N":
        lat = -lat
    if gps_data["GPSLongitudeRef"] != "E":
        lon = -lon

    return lat, lon


def get_metadata(image_path):
    path = Path(image_path)
    if not path.is_file():
        print(f"[-] Fajl nije pronađen: {image_path}")
        return

    if path.stat().st_size > MAX_FILE_SIZE:
        print("[-] Greška: Fajl je preveliki. Maksimalna dozvoljena veličina je 10MB.")
        return

    try:
        with Image.open(path) as img:
            exif_data = img.getexif()
    except Exception as e:
        print(f"[-] Greška pri otvaranju slike: {e}")
        return

    print(f"\n[+] Metapodaci za: {path.name}")
    print("-" * 45)

    if not exif_data:
        print("[-] Nema EXIF metapodataka.")
        return

    for tag_id, value in exif_data.items():
        tag_name = TAGS.get(tag_id, tag_id)
        if tag_name != "GPSInfo":
            print(f"{tag_name:25}: {str(value)[:50]}")

    coords = get_gps_coordinates(exif_data)
    if coords:
        lat, lon = coords
        print("-" * 45)
        print(f"GPS Latitude: {lat}\nGPS Longitude: {lon}")
        print(f"\n[🌍] Google Maps link:\nhttps://google.com/maps?q={lat},{lon}")
    else:
        print("\n[-] Nema GPS lokacije.")


if __name__ == "__main__":
    print("</> METADATA EXTRACTOR & SANITIZER")
    print("1. Izvuci metapodatke")
    print("2. Obriši metapodatke iz slike (Privatnost)")

    choice = input("Izaberi opciju (1 ili 2): ").strip()
    img_path = input("Unesi putanju do slike: ").strip()

    if choice == "1":
        get_metadata(img_path)
    elif choice == "2":
        print(sanitize_image(img_path))