# Image Metadata Extractor & Sanitizer

Mali Python alat za ekstrakciju EXIF metapodataka iz slika, uključujući GPS lokaciju, kao i za brisanje metapodataka radi privatnosti.

**Verzija:** v2.0.0

## Instalacija

pip install -r requirements.txt

## Pokretanje

python metadata_extractor.py

## Primer

</> METADATA EXTRACTOR & SANITIZER
1. Izvuci metapodatke
2. Obriši metapodatke iz slike (Privatnost)

Izaberi opciju (1 ili 2): 1
Unesi putanju do slike: slika.jpg

[+] Metapodaci za: slika.jpg
---------------------------------------------
Make                     : Apple
Model                    : iPhone 12
DateTimeOriginal         : 2024:07:20 14:30:00
GPS Latitude             : 44.8125
GPS Longitude            : 20.4612

[🌍] Google Maps link:
https://google.com/maps?q=44.8125,20.4612

## Funkcije

- **Ekstrakcija EXIF metapodataka**: Prikazuje sve standardne tagove (model kamere, datum, itd.).
- **GPS lokacija**: Konvertuje GPS koordinate u decimalni format i prikazuje Google Maps link.
- **Sanitizacija slika**: Briše sve EXIF/GPS metapodatke iz slike (zaštita privatnosti).
- **Limit veličine**: Maksimalno 10 MB po slici (zaštita od "image bomb").
- **Skraćivanje stringova**: Dugački stringovi se skraćuju na 50 karaktera.

## Napomena

Ovaj alat je napravljen za edukaciju i OSINT vežbe.
