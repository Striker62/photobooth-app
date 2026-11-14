# Fotobox-Fork – kurze Bedienhilfe

Die folgenden Funktionen ergänzen die Photobooth-App 9.0.0 im Striker62-Fork. Die wichtigsten Bedienelemente findest du im **Admin Center → Übersichtsseite**.

## Vor dem Einsatz

1. Pi, Buzzer und Selphy einschalten. Unter **Drucker und Buzzer** sollte der Drucker **Bereit** und der Buzzer **Verbunden** anzeigen.
2. In der Gästeansicht ein Foto mit dem Buzzer auslösen. Bei neuem Licht oder Hintergrund zuerst den Belichtungsmesser nutzen.
3. Ein Testfoto drucken und Bildausschnitt sowie Farben kontrollieren. Beim getesteten CP1500-Profil mit deaktiviertem Randlosdruck bleiben rund **3 mm Rand je Seite**. Der Ausschnitt entspricht der Livevorschau.

## Belichtung und Weißabgleich

1. Unter **Belichtungsmesser** auf **Messung starten** klicken. Die Livevorschau und das Histogramm zeigen, wie hell das Bild ist. Ist die Vorschau schwarz, prüfe die Livevorschau sowohl in der allgemeinen Konfiguration als auch für die verwendete Kamera.
2. Mit **Licht einstellen** die Picamera2-Regler öffnen. Über **Belichtungskorrektur (EV)** kannst du das Bild aufhellen (plus) oder abdunkeln (minus).
3. Bei wechselndem Tageslicht **Auto** wählen. Wirkt das Bild gelblich, die **Blaukorrektur** leicht erhöhen. Bei konstantem Licht kannst du eine neutrale Graukarte dort halten, wo später die Gesichter sind. Lass die Kamera im Auto-Modus kurz einregeln und klicke auf **Weißabgleich aus Vorschau übernehmen**, um die gemessenen Rot- und Blauwerte als manuelle Einstellung zu übernehmen.
4. Mit **Vorübergehend testen** die Wirkung in der Vorschau prüfen. **Test beenden** stellt die gespeicherten Werte wieder her. Mit **Kameraeinstellungen speichern** übernimmt die Box die Werte dauerhaft.
5. Mit **Profil speichern** kannst du die Werte unter einem Namen wie „Holzhintergrund mit LED-Licht“ ablegen. Später unter **Lichtprofil laden** auswählen, testen und mit **Kameraeinstellungen speichern** übernehmen.

## Drucker und Buzzer

- **Druckwarteschlange:** Für den USB-Selphy `Selphy_CP1500_USB` auswählen. **Aktualisieren** lädt den Status und offene Aufträge. **Abbrechen** entfernt den ausgewählten Auftrag nach Bestätigung.
- **Papier oder Farbband nachlegen:** Danach auf den Status achten. Steht dort weiterhin **Angehalten**, auf **Fortsetzen** klicken. Die offenen Aufträge bleiben dabei erhalten und können sofort gedruckt werden.
- **Warteschlange neu starten:** Wenn die Warteschlange hängt, diese Schaltfläche verwenden. Sie steht bei **Bereit** oder **Angehalten** zur Verfügung. Offene Aufträge können danach sofort weiterlaufen.
- **Automatisches Fortsetzen:** Optional in der Druck-/Teilen-Konfiguration **Selphy nach Papier- oder Farbbandwechsel automatisch fortsetzen** aktivieren. Die Funktion braucht die lokale Freigabe für die Gutenprint-Statusabfrage. Falls die Warteschlange nach dem Nachfüllen angehalten bleibt, **Fortsetzen** verwenden.
- **Bluetooth-Buzzer:** Bei **Getrennt** auf **Buzzer verbinden** klicken. Bei **Kein Buzzer gekoppelt** zuerst den **photobooth-app buzzer** über das Bluetooth-Menü des Pi koppeln. Falls er sich mit Windows verbindet, dort Bluetooth vorübergehend ausschalten. In der Gästeansicht die Fototaste testen. Der Buzzer sendet `f` für Foto, `c` für Collage und `p` für Drucken. Die Aktion richtet sich nach der Tastenzuordnung der Fotobox.

**Buzzer verbindet kurz und trennt sich wieder:** Wenn der Pi per LAN erreichbar ist und sein WLAN aktiv ist, schalte WLAN testweise mit `nmcli radio wifi off` aus. Versuche dann erneut, den Buzzer zu verbinden oder bei der Ersteinrichtung zu koppeln. Schalte WLAN anschließend mit `nmcli radio wifi on` wieder ein. Klappt die Verbindung bei ausgeschaltetem WLAN, ist das ein Hinweis auf eine mögliche Störung zwischen WLAN und Bluetooth. [Bericht zum Bluetooth-Fehler 0x3e](https://github.com/RPi-Distro/bluez-firmware/issues/12)

Eine neue SD-Karte oder einen neuen USB-Drucker richtest du mit der [Selphy-Installationsanleitung](deployment/selphy/README.md) ein.

## WLED bei Druckstörungen

In WLED ein rotes Preset anlegen (bei dieser Box **ID 30**). In der WLED-Plugin-Konfiguration der Fotobox dieselbe Nummer unter **WLED-Preset bei Druckfehler** eintragen. Bei erkanntem Druckfehler signalisiert WLED im Standby die Störung mit Rot. Gäste können weiter fotografieren. Sobald die App den Drucker wieder als bereit erkennt, kehrt WLED zum regulären Standby zurück.

## Audiogästebuch

Hörer abheben. Die Begrüßung beginnt nach zwei Sekunden. **1** kann während oder nach der Ansage gewählt werden. Sobald die **1** erkannt wird, stoppt eine laufende Ansage und der Signalton ertönt. Wenn nach der Begrüßung zehn Sekunden lang keine Ziffer gewählt wird, wiederholt sich die Ansage einmal. Nach dem Signalton sprechen und zum Speichern auflegen. Eine Nachricht kann bis zu fünf Minuten lang sein.

Im eigenen Tab **Admin Center → Audiogästebuch** siehst du den Dienststatus. Mit **Ansage anhören** kannst du die hinterlegte Begrüßung im Browser abspielen. Mit **Aktualisieren** holst du neue Aufnahmen in die Liste. Wähle **Anhören**, **Download** oder **Löschen**. Löschen ist endgültig.

Wenn du die Box ohne Telefon nutzt, wähle **Telefon deaktivieren** und bestätige. Das stoppt den Dienst und schaltet seinen Autostart aus. Gespeicherte Aufnahmen kannst du weiterhin verwalten. **Telefon aktivieren** startet den Dienst wieder und schaltet den Autostart ein. Für die erstmalige Einrichtung auf dem Pi und den Import alter Aufnahmen siehe [Audiogästebuch einrichten](deployment/guestbook/README.md).

## Videogästebuch

Der Videobutton erscheint auf dem vorhandenen Livebild, wenn das Mikrofon eingerichtet und das Videogästebuch aktiv ist. Einmal den Button drücken oder am Buzzer **c** drücken. Nach dem Countdown startet die Aufnahme mit Bild und Ton. Die Dauer übernimmt das Videogästebuch von der ersten Fotoaktion. Noch einmal drücken, um zu stoppen und direkt zu speichern. Nach Ablauf der eingestellten Höchstdauer speichert die Box automatisch. Der Countdown erscheint wie beim Foto mittig im Livebild. Restzeit und Speicherstatus stehen am unteren Bildschirmrand. Während Countdown und Aufnahme ist die Kamera für weitere Fotoaktionen belegt.

Mit aktiviertem Sprachauslöser funktioniert dieselbe Bedienung mit **„Kamera Video“**. Das Wort **Video** ist in der Plugin-Konfiguration einstellbar. Für einen GPIO-Taster den freien BCM-Pin als einzige Zeile in `~/VideoGuestbook/gpio` schreiben, GPIO-Eingabe aktivieren und Dienste neu laden. Beim Einsatz von **c** für Video die alte Collage-Tastenzuordnung entfernen.

Gespeicherte Grüße findest du unter **Admin Center → Audiogästebuch → Video**. Dort kannst du sie ansehen, herunterladen und löschen. Auf dem Pi liegen sie unter `~/VideoGuestbook/recordings/`.

Während der Aufnahme nutzt WLED das gleiche weiße Preset wie beim Foto. Beim Stoppen wechselt WLED zurück zum Standby-Preset. Wenn `c` nichts auslöst, zuerst den Videobutton auf der Gäste-Startseite testen. Prüfe danach in einem Texteditor auf dem Pi, ob die entsprechende Buzzertaste tatsächlich ein `c` sendet.

Zum Einrichten auf dem Pi mit `arecord -l` den ALSA-Kartennamen des separaten Mikrofons ermitteln. Den Gerätenamen, beispielsweise `plughw:CARD=USB,DEV=0`, als einzige Zeile in `~/VideoGuestbook/microphone` speichern. Der Ordner muss dem Photobooth-Benutzer gehören. Unter **Admin Center → Audiogästebuch → Video** kannst du neue Videogrüße unabhängig vom Sprachauslöser deaktivieren. Dort kannst du auch das Videosymbol ausblenden und die maximale Aufnahmedauer zwischen 1 und 300 Sekunden festlegen (Standard 15 Sekunden). Klicke danach auf **Einstellungen speichern**. Bei ausgeblendetem Symbol funktionieren Buzzer, GPIO und Sprache weiter. Für Video nutzt die Box `arecord` aus `alsa-utils` und `ffmpeg`.

Neue Audio- und Videoaufnahmen heißen zum Beispiel `PB2026-11-14-17-05-09.wav` und `PB2026-11-14-17-05-09.mp4`. Der Name enthält die lokale Startzeit der Aufnahme. Bei einer Namenskollision kommen sechs Stellen für die Mikrosekunden hinzu. Ältere Aufnahmen behalten ihre Dateinamen und bleiben im Admin Center verfügbar.

## Sprachauslöser

Unter **Admin Center → Audiogästebuch → Sprachtest** kannst du mit **Wörter erkennen** fünf Sekunden frei sprechen. Danach zeigt die Box den von Vosk erkannten Text. Wiederhole das Wort aus normalem Abstand und übernimm einen zuverlässig erkannten Text als Aktivierungswort, Foto- oder Videobefehl. **Gespeicherte Befehle testen** zeigt die Aktion an, die der erkannte Befehl auslösen würde. Der Test löst keine Aufnahme aus. Lade nach dem Speichern die Dienste neu, damit die Gästeansicht die neuen Wörter verwendet.

Der Sprachauslöser nutzt dasselbe Mikrofon wie das Videogästebuch. Während eines Videogrußes erkennt er den Stoppbefehl direkt aus dem aufgenommenen Ton. Das Mikrofon des Telefonhörers bleibt separat.

1. Das vorhandene deutsche Vosk-Modell aus dem Backup (`voicetrigger/model`) nach `~/VoiceTrigger/model` auf den Pi kopieren. Direkt darin müssen unter anderem die Unterordner `am` und `conf` liegen.
2. Als Benutzer `pi` mit `pipx inject photobooth-app vosk` die Spracherkennung in die App-Umgebung installieren. Das USB-Mikrofon wie im Abschnitt Videogästebuch einrichten.
3. In der Admin-Konfiguration unter den Plugins **Sprachauslöser** aktivieren, speichern und die Photobooth-Dienste neu laden.
4. In der Gästeansicht **„Kamera Foto“** sagen. Alternativ **„Kamera“** sagen und innerhalb von vier Sekunden **„Foto“**. Das löst die erste Fotoaktion aus. Beide Wörter sind in der Plugin-Konfiguration einstellbar.

Die Erkennung läuft lokal. Die frühere frei konfigurierbare Zuordnung zu Druck- und anderen Aktionen ist in dieser Version nicht enthalten.

## Update prüfen

Unter **Systeminformationen → App-Version** auf den grünen Update-Pfeil klicken. Den angezeigten Befehl als Benutzer `pi` im Terminal auf dem Raspberry Pi ausführen. Anschließend das Admin Center mit **Strg + F5** neu laden.

Unter der App-Version steht **Striker62-Fork · Commit** mit der kurzen Kennung der installierten Git-Version. Vergleiche sie mit dem erwarteten Stand auf dem [GitHub-Testzweig](https://github.com/Striker62/photobooth-app/tree/test/v9.0.0-light-meter). Die App-Version kann weiterhin `9.0.0` lauten, auch wenn der Fork aktualisiert wurde.
