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

Hörer abheben, Begrüßung abwarten und **1** wählen. Nach dem Signalton sprechen und zum Speichern auflegen. Eine Nachricht kann bis zu fünf Minuten lang sein.

Unter **Admin Center → Übersichtsseite → Audiogästebuch** siehst du den Dienststatus. Mit **Aktualisieren** holst du neue Aufnahmen in die Liste. Wähle **Anhören**, **Download** oder **Löschen**. Löschen ist endgültig.

Wenn du die Box ohne Telefon nutzt, wähle **Telefon deaktivieren** und bestätige. Das stoppt den Dienst und schaltet seinen Autostart aus. Gespeicherte Aufnahmen kannst du weiterhin verwalten. **Telefon aktivieren** startet den Dienst wieder und schaltet den Autostart ein. Für die erstmalige Einrichtung auf dem Pi und den Import alter Aufnahmen siehe [Audiogästebuch einrichten](deployment/guestbook/README.md).

## Update prüfen

Unter **Systeminformationen → App-Version** auf den grünen Update-Pfeil klicken. Den angezeigten Befehl als Benutzer `pi` im Terminal auf dem Raspberry Pi ausführen. Anschließend das Admin Center mit **Strg + F5** neu laden.

Unter der App-Version steht **Striker62-Fork · Commit** mit der kurzen Kennung der installierten Git-Version. Vergleiche sie mit dem erwarteten Stand auf dem [GitHub-Testzweig](https://github.com/Striker62/photobooth-app/tree/test/v9.0.0-light-meter). Die App-Version kann weiterhin `9.0.0` lauten, auch wenn der Fork aktualisiert wurde.
