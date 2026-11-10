# Canon Selphy CP1500 per USB

## Dokumentierter Stand vom 10. November 2026

Auf der neuen Testkarte: Raspberry Pi 4, Raspberry Pi OS Trixie 64 Bit,
Photobooth-App 9.0.0, Gutenprint 5.3.5, CP1500 per USB.
Der USB-Druck funktioniert. Der Ausdruck wirkt noch etwas groesser bzw.
staerker beschnitten als das Galeriebild. Die Groessenabstimmung ist offen.
Das Einrichtungsskript selbst muss noch auf dem Pi getestet werden.

## 1. Drucksystem

```bash
sudo apt update
sudo apt install -y cups cups-client printer-driver-gutenprint
sudo usermod -aG lpadmin pi
sudo systemctl enable --now cups
```

Bei anderem Benutzernamen `pi` ersetzen. Fuer neue Gruppenrechte erneut anmelden.

```bash
lpinfo -m | grep -i CP1500
```

Es muss ein Eintrag `gutenprint.5.3://canon-cp1500/expert` erscheinen.
Ein `driverless:ipps://...`-Eintrag ist der Netzwerkdrucker und reicht nicht.

## 2. Falls der Gutenprint-CP1500-Treiber fehlt

Die auf dieser Karte angebotene Debian-Version
5.3.4.20220624T01008808d602-4 enthaelt den Treiber noch nicht.
Zuerst mit `apt policy printer-driver-gutenprint libgutenprint9` pruefen,
ob inzwischen ein neueres passendes Paket angeboten wird. Andernfalls wurde
auf der Testkarte das offizielle Release 5.3.5 wie folgt gebaut:

```bash
sudo apt install -y build-essential pkg-config libcups2-dev \
  libusb-1.0-0-dev libjpeg-dev libpng-dev gettext curl xz-utils
mkdir -p ~/gutenprint-build
cd ~/gutenprint-build
curl -fL -o gutenprint-5.3.5.tar.xz \
  https://sourceforge.net/projects/gimp-print/files/gutenprint-5.3/5.3.5/gutenprint-5.3.5.tar.xz/download
tar -xf gutenprint-5.3.5.tar.xz
cd gutenprint-5.3.5
./configure --prefix=/usr/local --with-cups=/usr --without-gimp2
```

Zusammenfassung pruefen: CUPS driver = yes, installing in /usr;
CUPS dyesub USB backend = yes. Dann jeden Schritt nur nach erfolgreichem
Abschluss des vorherigen Schrittes ausfuehren:

```bash
make -j2
sudo make install
sudo ldconfig
sudo systemctl restart cups
```

Die manuelle Installation ersetzt CUPS-Komponenten des Pakettreibers unter
/usr; ein spaeteres Paketupdate kann diese wieder ueberschreiben. Bei Problemen
nach Updates erneut die tatsaechlich angebotene Treiberversion pruefen.
Quellordner behalten. Eine einzelne PPD aus einer anderen Gutenprint-Version
ist kein Ersatz fuer den vollstaendigen Treiber.

Quelle: https://sourceforge.net/projects/gimp-print/files/gutenprint-5.3/5.3.5/

## 3. USB-Warteschlange einrichten

Repository auf dem Pi auschecken (einmalig, falls noch nicht vorhanden):

```bash
git clone --branch test/v9.0.0-hq-selphy --single-branch \
  https://github.com/Striker62/photobooth-app.git ~/photobooth-source
cd ~/photobooth-source
```

Das pipx-Installieren der App allein legt diesen Quellordner nicht an.
Drucker einschalten, USB verbinden und zunaechst die Vorschau aufrufen:

```bash
sudo python3 deployment/selphy/setup_cp1500.py
```

Wenn Treiber und USB-Adresse passen, anwenden:

```bash
sudo python3 deployment/selphy/setup_cp1500.py --apply
```

Bei mehreren CP1500 muss mit `--uri 'ADRESSE'` eine der angezeigten Adressen
ausgewaehlt werden. Die Seriennummer wird nur lokal ermittelt und nicht im
Repository gespeichert. Das Skript erstellt keinen Druckauftrag, setzt keinen
systemweiten Standarddrucker und entfernt keine anderen Warteschlangen.
Eine vorhandene Warteschlange mit anderem Ziel wird nicht ueberschrieben;
eine angehaltene bestehende Warteschlange wird nicht automatisch aktiviert.

Profil in `cp1500.json`: Postcard, RGB, Randlos=True, Bildtyp=Photo.
Es setzt passendes Postkartenpapier voraus. Helligkeit, Gamma und die
Seitenanpassung des Treibers bleiben bei einer neuen Queue auf Standard.
Weitere bereits vorhandene Druckoptionen werden nicht zurueckgesetzt.

## 4. Fotobox konfigurieren

Im Druck-/Teilen-Eintrag der Fotobox:

- Druckername / `printer_name`: `Selphy_CP1500_USB`
- Befehlsstring / `share_command`:

```text
lp -d Selphy_CP1500_USB -n 1 -o fit-to-page "{filename}"
```

`{filename}` einschliesslich Anfuehrungszeichen beibehalten. Ein Exemplar
des fertig verarbeiteten Bildes wird gedruckt. Die Fotobox-Konfiguration
wird durch das Einrichtungsskript nicht automatisch geaendert.

## 5. Diagnose ohne erneutes Einrichten

```bash
lpstat -p Selphy_CP1500_USB -l
lpstat -o Selphy_CP1500_USB
sudo tail -n 40 /var/log/cups/error_log
```

Beim Test hat eine Meldung `No Paper Tray (03)` die Queue angehalten.
Die spaeteren Auftraege warteten, bis sie wieder aktiviert wurde. Die
urspruengliche Ursache ist nicht geklaert; beim Wiederauftreten zuerst
Zeitstempel, Druckerdisplay und Protokoll vergleichen.

Nach Beheben des Fehlers reaktivieren (wartende Auftraege koennen starten):

```bash
sudo cupsenable Selphy_CP1500_USB
```

Nur wenn alle ausstehenden Auftraege verworfen werden sollen:

```bash
cancel -a Selphy_CP1500_USB
```

Keine automatische Fehlerquittierung: einen wiederkehrenden Fehler zuerst
analysieren. Fuer den Groessenvergleich ein Foto mit sichtbaren Randmarken
verwenden und Galerie, gespeicherte Datei sowie Ausdruck vergleichen.
