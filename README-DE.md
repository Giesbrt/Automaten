# N.E.F.S.' Simulator

## So führen Sie es aus

````shell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\run.ps1
````
### Alternativ: den Installer ausführen und das Programm dem Dialog entsprechend installieren.

## Dateien öffnen
1. Programm starten
2. einen beliebigen Automaten auswählen
3. im Menü unter File > Open eine Datei auswählen

## So wird das Programm Schritt für Schritt ausgeführt

### config.py wird geladen

config.py richtet die Umgebung für unsere App ein.

Dies ändert sich je nach einigen Faktoren, z. B. INDEV, wodurch die App mehr Ausgabe erzeugt.

Bei der Suche nach einer geeigneten Umgebung prüft es das Betriebssystem und die Python-Version.

Es prüft automatisch, ob die App kompiliert ist, und ändert das aktuelle Arbeitsverzeichnis entsprechend.

Dann klonen wir den Ordner default-config nach %LOCALAPPDATA%/nefs_simulator. Dies geschieht, damit die App auf globaler Ebene installiert werden kann.

Zuletzt legen wir das aktuelle Arbeitsverzeichnis auf den Ordner appdata fest, in den wir zuvor alles geklont haben.

### main.py-Setup

Zuerst deklarieren wir in main.py einige globale Variablen, die beim Kompilierungsprozess helfen.

Später im Abschnitt __name__ == "__main__": registrieren wir verschiedene Exit-Codes und erhalten Argumente mithilfe von argparse.

Zuletzt starten wir die MainWindow-Klasse und die App-Klasse in einem Try-Except-Block, um Abstürze ohne eindeutige Fehler zu verhindern.

### App-Klasse

Der Initialisierer der App-Klasse innerhalb eines Try-Except-Blocks:

- Wichtige Speicherorte mit os.path.join festlegen
- IOManager für Protokolle und Popups initialisieren
- AppSettings initialisieren
- Protokollierungsstufe konfigurieren
- ThreadPool starten und Extension Loader übermitteln
- Warten, bis Extension_Loader fertig ist
- Update-Prüfung an Threadpool übermitteln
- Automaton mit der UiAutomaton-Klasse registrieren
- Designs und Stile laden
- MainWindow-GUI einrichten
  - Dadurch werden alle GUI-Komponenten initialisiert, daher wird hier viel Arbeit erledigt
- Eingabepfad prüfen und laden, falls angegeben
- Backend-Thread starten
- Fenstergröße und -position festlegen
- Designs anwenden (vorher iterativ Namen zuweisen)
- Fenstersymbol und -titel aktualisieren und Einstellungen verbinden
- Fenster starten (Fenster anzeigen) und Schriftart danach laden
  - Einige GUI-Komponenten verwenden dies auch, um bestimmte Dinge zu laden
- Timer-Tick starten

Der UiAutomaton wird nur einmal initialisiert und danach für jeden Automaten verwendet.

### Projektstruktur

Standardkonfiguration:
- config ist für alle Einstellungsdateien
- core ist für alle Skriptdateien (.py)
  - libs ist zum Überschreiben enthaltener Bibliotheken wie argparse mit einer anderen Version
  - modules ist für die verschiedenen Module innerhalb der App
    - automaton ist für alles, was mit der Simulation zu tun hat
    - gui ist für GUI
    - abstractions werden verwendet, um abstrakte Klassen zu definieren
    - ...
    - painter analysiert und zeichnet die Designs für Zustände
    - serializer analysiert oder serialisiert Automat (Laden oder Speichern)
    - storage behandelt alles, was mit AppSettings zusammenhängt
- data ist für alle Datendateien wie Symbole, Protokolle oder Stile und Themen
- extensions ist für Erweiterungen

## So kompilieren Sie N.E.F.S

- Führen Sie ./compile.bat aus und deaktivieren Sie Ihren Echtzeitschutz von Antivirus, da dieser bekanntermaßen störend wirkt
- Installieren Sie das Inno Setup Script
- Öffnen Sie ./nefs_install_script.iss
- Klicken Sie auf die Schaltfläche „Kompilieren“
- Fertig! Das Installationsprogramm sollte sich in ./ befinden und etwa so heißen: nefs-v...-win10-11-x64-installer.exe
- Manche Leute haben möglicherweise Probleme bei der Installation von N.E.F.S, da es nicht signiert ist und aus dem Internet heruntergeladen wurde. Der Echtzeit-Antivirusschutz ist oft die Ursache.
