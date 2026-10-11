"""
Testovi za image-metadata-extractor.
Pokreni: pytest -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PIL import Image

# Dodaj root folder u path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from metadata_extractor import (
    sanitize_image,
    convert_to_degrees,
    get_gps_coordinates,
    get_metadata,
    MAX_FILE_SIZE,
)


# ============================================================
# FIXTURE — napravi test sliku
# ============================================================

@pytest.fixture
def test_image(tmp_path):
    """Napravi test sliku."""
    img_path = tmp_path / "test.jpg"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path)
    return img_path


@pytest.fixture
def test_image_no_exif(tmp_path):
    """Napravi test sliku bez EXIF-a."""
    img_path = tmp_path / "no_exif.jpg"
    img = Image.new("RGB", (50, 50), color="blue")
    img.save(img_path)
    return img_path


# ============================================================
# TESTIRANJE sanitize_image()
# ============================================================

class TestSanitizeImage:
    """Testovi za sanitize_image funkciju."""

    def test_sanitize_existing_image(self, test_image):
        """Testira čišćenje postojeće slike."""
        result = sanitize_image(test_image)
        assert "Privatnost zaštićena" in result
        clean_path = test_image.parent / f"{test_image.stem}_cleaned{test_image.suffix}"
        assert clean_path.exists()

    def test_sanitize_nonexistent_file(self):
        """Testira nepostojeći fajl."""
        result = sanitize_image("/nonexistent/image.jpg")
        assert "nije pronađen" in result

    def test_sanitize_invalid_file(self, tmp_path):
        """Testira nevalidan fajl (nije slika)."""
        fake_file = tmp_path / "fake.jpg"
        fake_file.write_text("nije slika")
        result = sanitize_image(fake_file)
        assert "Greška" in result

    def test_sanitize_keeps_original(self, test_image):
        """Testira da original ostaje netaknut."""
        original_size = test_image.stat().st_size
        sanitize_image(test_image)
        assert test_image.exists()
        assert test_image.stat().st_size == original_size


# ============================================================
# TESTIRANJE convert_to_degrees()
# ============================================================

class TestConvertToDegrees:
    """Testovi za convert_to_degrees funkciju."""

    def test_valid_dms_conversion(self):
        """Testira konverziju DMS u decimalne stepene."""
        # 44° 48' 0" = 44.8
        result = convert_to_degrees((44, 48, 0))
        assert result == pytest.approx(44.8, abs=0.001)

    def test_valid_dms_with_seconds(self):
        """Testira konverziju sa sekundama."""
        # 44° 48' 36" = 44.81
        result = convert_to_degrees((44, 48, 36))
        assert result == pytest.approx(44.81, abs=0.001)

    def test_zero_coordinates(self):
        """Testira nulte koordinate."""
        result = convert_to_degrees((0, 0, 0))
        assert result == 0.0

    def test_invalid_length(self):
        """Testira nevalidan broj elemenata."""
        assert convert_to_degrees((44, 48)) is None
        assert convert_to_degrees((44, 48, 0, 0)) is None

    def test_none_value(self):
        """Testira None vrednost."""
        assert convert_to_degrees(None) is None

    def test_empty_tuple(self):
        """Testira prazan tuple."""
        assert convert_to_degrees(()) is None

    def test_invalid_types(self):
        """Testira nevalidne tipove."""
        assert convert_to_degrees(("a", "b", "c")) is None


# ============================================================
# TESTIRANJE get_gps_coordinates()
# ============================================================

class TestGetGpsCoordinates:
    """Testovi za get_gps_coordinates funkciju."""

    def test_no_gps_info(self):
        """Testira EXIF bez GPS-a."""
        mock_exif = MagicMock()
        mock_exif.get_ifd.return_value = {}
        result = get_gps_coordinates(mock_exif)
        assert result is None

    def test_gps_info_exception(self):
        """Testira EXIF koji baca exception."""
        mock_exif = MagicMock()
        mock_exif.get_ifd.side_effect = Exception("test")
        result = get_gps_coordinates(mock_exif)
        assert result is None

    def test_gps_missing_required_tags(self):
        """Testira GPS bez potrebnih tagova."""
        mock_exif = MagicMock()
        mock_exif.get_ifd.return_value = {"GPSLatitude": (44, 48, 0)}
        result = get_gps_coordinates(mock_exif)
        assert result is None

    def test_gps_valid_coordinates(self):
        """Testira validne GPS koordinate."""
        mock_exif = MagicMock()
        # GPS tagovi: 1=GPSLatitudeRef, 2=GPSLatitude, 3=GPSLongitudeRef, 4=GPSLongitude
        mock_exif.get_ifd.return_value = {
            1: "N",
            2: (44, 48, 0),
            3: "E",
            4: (20, 28, 0),
        }
        result = get_gps_coordinates(mock_exif)
        assert result is not None
        lat, lon = result
        assert lat == pytest.approx(44.8, abs=0.001)
        assert lon == pytest.approx(20.466, abs=0.001)

    def test_gps_southern_hemisphere(self):
        """Testira južnu hemisferu (S)."""
        mock_exif = MagicMock()
        mock_exif.get_ifd.return_value = {
            1: "S",
            2: (33, 52, 0),
            3: "E",
            4: (151, 12, 0),
        }
        result = get_gps_coordinates(mock_exif)
        assert result is not None
        lat, lon = result
        assert lat < 0  # Južna hemisfera

    def test_gps_western_hemisphere(self):
        """Testira zapadnu hemisferu (W)."""
        mock_exif = MagicMock()
        mock_exif.get_ifd.return_value = {
            1: "N",
            2: (40, 42, 0),
            3: "W",
            4: (74, 0, 0),
        }
        result = get_gps_coordinates(mock_exif)
        assert result is not None
        lat, lon = result
        assert lon < 0  # Zapadna hemisfera


# ============================================================
# TESTIRANJE get_metadata()
# ============================================================

class TestGetMetadata:
    """Testovi za get_metadata funkciju."""

    def test_nonexistent_file(self, capsys):
        """Testira nepostojeći fajl."""
        get_metadata("/nonexistent.jpg")
        captured = capsys.readouterr()
        assert "nije pronađen" in captured.out

    def test_file_too_large(self, tmp_path, capsys, monkeypatch):
        """Testira preveliki fajl."""
        big_file = tmp_path / "big.jpg"
        big_file.write_bytes(b"x" * (MAX_FILE_SIZE + 1))
        get_metadata(big_file)
        captured = capsys.readouterr()
        assert "preveliki" in captured.out

    def test_valid_image_no_exif(self, test_image_no_exif, capsys):
        """Testira sliku bez EXIF metapodataka."""
        get_metadata(test_image_no_exif)
        captured = capsys.readouterr()
        assert "Metapodaci" in captured.out or "Nema EXIF" in captured.out

    def test_invalid_image_file(self, tmp_path, capsys):
        """Testira fajl koji nije slika."""
        fake = tmp_path / "fake.jpg"
        fake.write_text("nije slika")
        get_metadata(fake)
        captured = capsys.readouterr()
        assert "Greška" in captured.out


# ============================================================
# TESTIRANJE KONSTANTI
# ============================================================

class TestConstants:
    """Testovi za konstante."""

    def test_max_file_size(self):
        """Testira MAX_FILE_SIZE konstantu."""
        assert MAX_FILE_SIZE == 10 * 1024 * 1024
        assert MAX_FILE_SIZE == 10485760
