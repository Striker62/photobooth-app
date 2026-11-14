# Audiogästebuch auf dem Raspberry Pi einrichten

Die Befehle als derselbe Benutzer ausführen, unter dem Photobooth läuft (hier `pi`). Die Dateien aus diesem Verzeichnis auf dem Pi in einem Git-Checkout öffnen.

```bash
sudo apt install python3-gpiozero python3-lgpio python3-sounddevice alsa-utils
install -d -m 700 ~/AudioGuestbook ~/AudioGuestbook/recordings
install -m 600 guestbook.py ~/AudioGuestbook/
install -D -m 644 photobooth-guestbook.service ~/.config/systemd/user/photobooth-guestbook.service
```

Die bestehende GPIO-Verdrahtung nutzt **BCM 17** für die Wählscheibe und **BCM 18** für den Gabelkontakt. Beide Eingänge nutzen interne Pull-ups. GPIO 18 ist bei abgehobenem Hörer high. Die bestehende Audioschnittstelle für Mikrofon und Hörkapsel anschließen.

Begrüßung und Signalton als `~/AudioGuestbook/greeting.wav` und `~/AudioGuestbook/beep.wav` bereitstellen. Eine vorhandene MP3-Begrüßung kannst du mit `ffmpeg -i begruessung.mp3 ~/AudioGuestbook/greeting.wav` umwandeln.

Bei Bedarf `~/AudioGuestbook/audio.env` anlegen. Geräte mit `/usr/bin/python3 -m sounddevice` (Eingang) und `aplay -L` (Ausgang) ermitteln. Beispielwerte durch die lokal ermittelten Gerätenamen ersetzen. Ohne Datei verwendet der Dienst die Standardgeräte.

```ini
GUESTBOOK_INPUT="USB Audio Device"
GUESTBOOK_OUTPUT="plughw:CARD=Device,DEV=0"
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now photobooth-guestbook.service
systemctl --user status photobooth-guestbook.service
```

Für den Start ohne Desktop-Anmeldung muss der Benutzerdienst beim Booten starten können. Falls für `pi` noch kein Linger aktiv ist, einmal `sudo loginctl enable-linger pi` ausführen.

Zum Test abheben, Begrüßung abwarten, **1** wählen, nach dem Signal sprechen und auflegen. Unter **Audiogästebuch → Aktualisieren** sollte die WAV-Datei erscheinen. Bei Problemen `journalctl --user -u photobooth-guestbook.service -n 50 --no-pager` prüfen.

Alte WAV-Aufnahmen mit den Dateinamen `gaestebuch_eintrag*.wav` kannst du aus dem Backup nach `~/AudioGuestbook/recordings/` kopieren. Wenn der alte Flask-Dienst noch läuft, beende ihn bei der Umstellung, damit nur der neue Dienst auf GPIO und Audio zugreift.
