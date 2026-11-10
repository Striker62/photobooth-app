# Teststand: Raspberry Pi HQ Camera und Selphy CP1500

Basis: offizieller Tag v9.0.0 (76b4b5bad239e9fe141332fe034135ada21d878c).
Entwicklungszweig: test/v9.0.0-hq-selphy.

## Enthaltene Anpassungen

- Daylight-Weissabgleich in Vorschau und Fotomodus.
- ScalerCrop (430, 440, 3197, 2160) in beiden Modi.
- Picamera2-Standardaufloesungen fuer Foto, Vorschau und Liveview: 1184 x 800.
- Keine neue Weissabgleich-Bedienung; zuerst den bisherigen Bildstand testen.

Die Aufloesungen sind Standardwerte fuer eine neue Kamerakonfiguration. Bereits
gespeicherte Werte werden dadurch nicht ueberschrieben.

## Neue SD-Karte vorbereiten

Raspberry Pi OS mit 64 Bit und Python >= 3.11 verwenden. Kamera und die
systemweite Picamera2-Installation zuerst pruefen. Die Betriebssystem- und
Kameraabhaengigkeiten nach der offiziellen Anleitung einrichten:
https://photobooth-app.org/setup/installation

Danach git und pipx installieren, falls noch nicht vorhanden:

```bash
sudo apt update
sudo apt install git pipx
pipx ensurepath
```

Nach erneuter Anmeldung diese Variante installieren:

```bash
pipx install --system-site-packages "git+https://github.com/Striker62/photobooth-app.git@test/v9.0.0-hq-selphy" --pip-args='--prefer-binary'
mkdir -p ~/photobooth-data-v9-test
cd ~/photobooth-data-v9-test
photobooth
```

Im Browser http://localhost:8000 oeffnen. Im Adminbereich Picamera2 statt der
virtuellen Kamera auswaehlen und alle drei Aufloesungen auf 1184 x 800 pruefen.
App nach dem Speichern bei Bedarf neu starten. Fuer jeden manuellen Start
wieder in ~/photobooth-data-v9-test wechseln.

## Abnahme auf der Box

1. Livebild und Countdown-Vorschau auf Bildausschnitt und Farben pruefen.
2. Foto aufnehmen und die tatsaechliche Dateiaufloesung kontrollieren.
3. Vorlage separat uebernehmen und Foto mit Vorschau vergleichen.
4. Selphy-Drucker einrichten und einen Testausdruck vergleichen.
5. Mehrere Aufnahmen und Wechsel zwischen Vorschau und Foto testen.

Die alte SD-Karte bleibt die Rueckfallmoeglichkeit. Die alte Konfiguration
nicht ungeprueft komplett kopieren: v9 hat die Kamerakonfigurationsstruktur
geaendert. Druckereinstellungen und Vorlagen sind mit dieser Codeaenderung
nicht automatisch uebernommen. Hardwaretests stehen noch aus.
