# Image Metadata Extractor
# Extract EXIF metadata from any image using Python

import sys
from pathlib import Path

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
except ImportError:
    print("[!] Pillow nije instaliran.")
    print("[i] Instaliraj ga sa: pip install Pillow")
    sys.exit(1)


def convert_to_degrees(value):
    """Pretvara GPS stepene, minute i sekunde u decimalne brojeve."""
    # Zaštita: Ako GPS zapis nema tačno 3 elementa (stepeni, minuti, sekunde), preskoči ga
    if len(value) != 3:
        return None

    d, m, s = value
    return d + (m / 60.0) + (s / 3600.0)


def get_gps_coordinates(exif_data):
    """Ekstraktuje i konvertuje GPS podatke iz EXIF-a."""
    try:
        # 0x8825 je ID za GPSInfo u EXIF podacima
        gps_info = exif_data.get_ifd(0x8825)
    except AttributeError:
        # Rezervna opcija ako get_ifd nije podržan
        return None
    except Exception:
        return None

    if not gps_info:
        return None

    gps_data = {}
    for tag_id, value in gps_info.items():
        tag_name = GPSTAGS.get(tag_id, tag_id)
        gps_data[tag_name] = value

    # Provjera da li postoje neophodni GPS tagovi
    required_tags = ["GPSLatitude", "GPSLatitudeRef", "GPSLongitude", "GPSLongitudeRef"]
    if not all(tag in gps_data for tag in required_tags):
        return None

    lat = convert_to_degrees(gps_data["GPSLatitude"])
    if lat is None:
        return None
    lat_ref = gps_data["GPSLatitudeRef"]
    if lat_ref != "N":
        lat = -lat

    lon = convert_to_degrees(gps_data["GPSLongitude"])
    if lon is None:
        return None
    lon_ref = gps_data["GPSLongitudeRef"]
    if lon_ref != "E":
        lon = -lon

    return lat, lon


def get_metadata(image_path):
    """Extract and print EXIF metadata from an image."""
    path = Path(image_path)

    if not path.is_file():
        print(f"[-] Fajl nije pronađen: {image_path}")
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
        print("[-] Nema EXIF metapodataka u ovoj slici.")
        return

    # Ispis standardnih tagova
    for tag_id, value in exif_data.items():
        tag_name = TAGS.get(tag_id, tag_id)
        # Preskačemo sirovi GPSInfo blok jer ćemo ga obraditi posebno
        if tag_name != "GPSInfo":
            print(f"{tag_name:25}: {value}")

    # Provjera i ispis GPS lokacije
    coords = get_gps_coordinates(exif_data)
    if coords:
        lat, lon = coords
        print("-" * 45)
        print(f"{'GPS Latitude':25}: {lat}")
        print(f"{'GPS Longitude':25}: {lon}")
        print(f"\n[🌍] Google Maps link:")
        print(f"https://www.google.com/maps?q={lat},{lon}")
    else:
        print("\n[-] Nema GPS podataka u ovoj slici.")

    print("\n[+] Ekstrakcija završena.")


if __name__ == "__main__":
    print("</> IMAGE METADATA EXTRACTOR")
    image_path = input("Unesi putanju do slike: ").strip()
    get_metadata(image_path)