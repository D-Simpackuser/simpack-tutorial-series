# RailDyn Atlas

**Simpack-Bibliothek für Schienenfahrzeugdynamik und Simulation flexibler Körper**

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Español](README.es.md) · [한국어](README.ko.md)

> Das Repository ist derzeit privat. Für Video- und Untertiteldownloads ist ein GitHub-Konto mit Zugriffsberechtigung erforderlich.

**Fahrzeug–Fahrweg–Brücken-Interaktion · Flexible Körper · Spannungsrückgewinnung und Ermüdung**

RailDyn Atlas bündelt sieben Tutorial-Reihen zu Arbeitsabläufen der Eisenbahndynamik mit Simpack, Abaqus, Ansys und fe-safe. Die Themen reichen von Fahrzeugmodellen über elastische Schienen und Gleisfundamente bis zur Fahrzeug–Fahrweg–Brücken-Kopplung sowie zur Spannungs-, Dehnungs- und Ermüdungsanalyse flexibler Körper.

194 Videos · 772 Untertiteldateien · 193 Videos mit allen vier Untertiteldateien. Lektionen ohne Untertiteldateien: `s05-e001` — 0-课程效果.

## Übersicht der Reihen

| Reihe | Thema | Videos | Dateien |
|---|---|---:|---|
| 1 | [Gekoppelte Dynamik von Schienenfahrzeug, elastischer Schiene und schwimmend gelagerter Fahrbahnplatte mit Abaqus und Simpack](series/1/README.de.md) | 18 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-1-v1) |
| 2 | [Dynamische Spannungs-, Dehnungs- und Ermüdungsanalyse flexibler Körper mit Ansys/Abaqus, Simpack und fe-safe](series/2/README.de.md) | 13 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-2-v1) |
| 3 | [Schienenfahrzeug–Fahrweg-Dynamik mit elastischem Gleis in Ansys Workbench Mechanical, APDL und Simpack](series/3/README.de.md) | 16 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-3-v1) |
| 5 | [Gekoppelte Fahrzeug–Fahrweg–Brücken-Dynamik mit Abaqus und Simpack](series/5/README.de.md) | 42 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-5-v1) |
| 6 | [Einstieg in die Schienenfahrzeugdynamik mit Simpack](series/6/README.de.md) | 8 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-6-v1) |
| 7 | [Fahrzeug–Fahrweg–Brücken-Dynamik mit Ansys und Simpack: Beam–Solid-Modellierung](series/7/README.de.md) | 46 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-7-v1) |
| 8 | [Fahrzeug–Fahrweg–Brücken-Dynamik mit Ansys und Simpack: Beam–Beam-Modellierung](series/8/README.de.md) | 51 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-8-v1) |

Der Titel einer Reihe führt zum vorhandenen Einzelverzeichnis. Auf den Release-Seiten stehen Videos und Untertitel zum Download. Die ursprüngliche Nummerierung bleibt erhalten; eine Reihe 4 gibt es nicht.

## Empfohlener Einstieg

Für ein erstes Fahrzeugmodell empfiehlt sich **Reihe 6**. Für elastische Gleise wählen Sie **Reihe 1** mit Abaqus oder **Reihe 3** mit Ansys; anschließend bieten sich **Reihe 5, 7 oder 8** für Fahrzeug–Fahrweg–Brücken-Modelle an. **Reihe 2** behandelt insbesondere Spannungs- und Dehnungsrückgewinnung sowie Ermüdung. Dies ist eine redaktionelle Lernempfehlung, keine geprüfte Abfolge verbindlicher Voraussetzungen.

## Themenüberblick

Die folgenden Gruppen ordnen die vorliegenden Videotitel. Sie belegen keine unabhängige Validierung von Modellen, numerischen Ergebnissen oder Softwareversionskombinationen.

### Reihe 1 — Gekoppelte Dynamik von Schienenfahrzeug, elastischer Schiene und schwimmend gelagerter Fahrbahnplatte mit Abaqus und Simpack

- Elastische Schienen und federgelagerte Fahrbahnplatten in Abaqus; FBI-Erzeugung
- FTR-Dateien und Einrichtung elastischer Gleise in Simpack
- Radsatz-, Drehgestellrahmen- und Gesamtfahrzeugmodelle; Kopplung mit der Fahrbahnplatte
- TRE-/PSD-Anregung, Animation flexibler Körper und Auswertung der Antworten

### Reihe 2 — Dynamische Spannungs-, Dehnungs- und Ermüdungsanalyse flexibler Körper mit Ansys/Abaqus, Simpack und fe-safe

- Vorbereitung der Abaqus-/Ansys-Schnittstellen und Erzeugung von FBI-Dateien
- Einrichtung flexibler Körper sowie Spannungs- und Dehnungsrückgewinnung in Simpack
- Darstellung von Verformungen, Spannungen und Dehnungen in Simpack Post
- Export nach fe-safe, Ermüdungsanalyse und durchgängiges Ablaufbeispiel

### Reihe 3 — Schienenfahrzeug–Fahrweg-Dynamik mit elastischem Gleis in Ansys Workbench Mechanical, APDL und Simpack

- Schienen-Balkenmodell in SpaceClaim; Substrukturreduktion in Workbench Mechanical
- APDL mit grafischer Oberfläche und Befehlen; FBI-Schnittstelle
- FTR-Fundamentverbindungen und stapelweise Einrichtung von Kraftelementen
- Einfache Fahrzeugmodelle, TRE-/PSD-Anregung, Animationen und Auswerteparameter

### Reihe 5 — Gekoppelte Fahrzeug–Fahrweg–Brücken-Dynamik mit Abaqus und Simpack

- Schienen, CRTS-III-Gleisplatten, Betonschichten, Grundplatten und einfach gelagerte Brückenträger
- Materialien, Vernetzung, Schienenbefestigungen, interne Kontakte und Substrukturen
- FBI / FTR, parametrisierte Fahrzeuge, statisches Gleichgewicht und Fahrzeug–Fahrweg–Brücken-Kopplung
- Vorlast, Solver, Gleisunregelmäßigkeiten und die in den Videos behandelten dynamischen Bewertungsgrößen

### Reihe 6 — Einstieg in die Schienenfahrzeugdynamik mit Simpack

- Radsatz- und Drehgestellrahmenmodellierung
- Zusammenbau des Gesamtfahrzeugmodells
- TRE-Dateien und PSD-Anregung
- Nachverarbeitung und Analyse der Antworten

### Reihe 7 — Fahrzeug–Fahrweg–Brücken-Dynamik mit Ansys und Simpack: Beam–Solid-Modellierung

- RAIL-EULER, rail-timo, Brückenmodelle mit Volumenelementen und modale Themen
- FBI-Dateien für Schienen und Brücken; FTR-Erstellung und Fehlersuche
- Parametrisierte Fahrzeuge, Kopplungsreihenfolge sowie Steifigkeit und Dämpfung im Übergangsbereich
- Vorlast, Solver, Anregung, Brücken- und Schienenantworten, Modellorganisation

### Reihe 8 — Fahrzeug–Fahrweg–Brücken-Dynamik mit Ansys und Simpack: Beam–Beam-Modellierung

- RAIL-EULER, rail-timo, BEAM188-Brückenmodelle und modale Themen
- FBI-/FTR-Einstellungen, parametrisierte Fahrzeuge und Fahrzeug–Fahrweg–Brücken-Kopplung
- Stapelweise Erstellung von Verbindungspunkten, Verbindungen, Lagern und Sensoren
- Vorlast, Solver, Anregung, Nachverarbeitung und Modellorganisation

## Download und Nutzung

Laden Sie innerhalb der gewünschten Reihe die MP4-Datei und die passende `.zh-CN.srt`- oder `.en.srt`-Datei herunter. Behalten Sie den gemeinsamen Dateinamensstamm bei und wählen Sie die Untertiteldatei im lokalen Videoplayer aus. VTT steht ebenfalls zur Verfügung. Ein Repository-Clone oder Code → Download ZIP enthält nicht die in Releases gespeicherten Videos.

Die Downloadberechtigung richtet sich nach der Sichtbarkeit des Repositorys. Solange es privat ist, benötigen Sie ein berechtigtes GitHub-Konto. Videolinks sind Downloadlinks; ein eingebetteter Streamingplayer wird damit nicht zugesichert.

## Sprachen

Einführung und Themenüberblick liegen auf Englisch, vereinfachtem Chinesisch, Japanisch, Französisch, Deutsch, Italienisch, Spanisch und Koreanisch vor. Diese Lokalisierung betrifft die Dokumentation, nicht zusätzliche Untertitelspuren oder Synchronfassungen. Die vorhandenen Untertitelsprachen sind Chinesisch und Englisch. Die chinesischen Originaltitel bleiben zur eindeutigen Zuordnung erhalten.

## Umfang und technische Grenzen

Dies ist eine Tutorial-Bibliothek, kein validierter Benchmark und keine Softwaredistribution. Ein im Video gezeigtes Modell bedeutet nicht, dass Modelldateien, Solverlizenzen oder Eingabedaten mitgeliefert werden. Prüfen Sie vor einer Übertragung den Softwarestand, Einheiten, Randbedingungen, Dämpfung, Reduktionseinstellungen und Bewertungskriterien. Historische Normendiskussionen in Videos sind kein Nachweis aktueller Anforderungen. Beam–Solid und Beam–Beam bezeichnen zwei Lernpfade und belegen keinen Genauigkeitsvorteil.

Vorhandene Untertitel und übereinstimmende Prüfsummen bestätigen weder die Übersetzungsqualität noch die Synchronität mit dem Ton. Fachbegriffe sollten anhand der Originalaufnahme und der zugehörigen Softwaredokumentation geprüft werden.

## Korrekturen und Mitarbeit

Nennen Sie bei Korrekturen die Reihe, die stabile Video-ID, die Untertitelsprache und gegebenenfalls den Zeitstempel. Originalkennungen bleiben auch bei verbesserten Titeln oder Übersetzungen unverändert. Laden Sie keine kommerzielle Software, Lizenzdateien, fremden Kurse oder Modelle ohne die erforderliche Erlaubnis hoch.

## Quellen und Nutzungsrechte

Repository-Pflege, Urheberschaft der Kurse und Rechte an der Software sind getrennte Rollen. Den dokumentierten Quellen- und Rechtestatus finden Sie in der Herkunftserklärung. Eine offizielle Zugehörigkeit zu den Herstellern oder deren Unterstützung wird nicht behauptet. Öffentliche Zugänglichkeit ist keine pauschale Erlaubnis zur Weiterverwendung oder Weiterverbreitung der Medien.

[Quellen- und Rechtehinweise](PROVENANCE.md)

[Downloadhinweise](docs/using-the-library.md) · [Lernempfehlungen](docs/learning-paths.md) · [Qualität und Versionen](docs/quality-and-versions.md) · [Terminologie](docs/terminology.md) · [Mitarbeit](CONTRIBUTING.md) · [Quellen und Rechte](PROVENANCE.md)
