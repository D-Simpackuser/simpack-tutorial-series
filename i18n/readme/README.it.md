# RailDyn Atlas

**Biblioteca Simpack di dinamica ferroviaria e simulazione di corpi flessibili**

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Español](README.es.md) · [한국어](README.ko.md)

**Interazione veicolo–binario–ponte · Corpi flessibili · Recupero delle tensioni e fatica**

RailDyn Atlas raccoglie sette serie di tutorial sui flussi di lavoro della dinamica ferroviaria con Simpack, Abaqus, Ansys e fe-safe. I temi comprendono i modelli di veicolo, le rotaie e le fondazioni flessibili, l’accoppiamento veicolo–binario–ponte, il recupero di tensioni e deformazioni e l’analisi a fatica dei corpi flessibili.

Il catalogo comprende **194 video**. **193 video** dispongono di sottotitoli cinesi e inglesi nei formati SRT e VTT, per un totale di **772 file di sottotitoli**. Il video introduttivo `0-课程效果` della serie 5 non dispone di sottotitoli associati.

## Catalogo delle serie

| Serie | Argomento | Video | File |
|---|---|---:|---|
| 1 | [Dinamica accoppiata veicolo ferroviario–rotaia flessibile–soletta flottante con Abaqus e Simpack](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/1/README.md) | 18 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-1-v1) |
| 2 | [Analisi delle tensioni, delle deformazioni dinamiche e della fatica dei corpi flessibili con Ansys/Abaqus, Simpack e fe-safe](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/2/README.md) | 13 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-2-v1) |
| 3 | [Dinamica veicolo ferroviario–binario flessibile con Ansys Workbench Mechanical, APDL e Simpack](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/3/README.md) | 16 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-3-v1) |
| 5 | [Dinamica accoppiata veicolo–binario–ponte con Abaqus e Simpack](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/5/README.md) | 42 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-5-v1) |
| 6 | [Introduzione alla dinamica dei veicoli ferroviari con Simpack](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/6/README.md) | 8 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-6-v1) |
| 7 | [Dinamica veicolo–binario–ponte con Ansys e Simpack: modellazione Beam–Solid](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/7/README.md) | 46 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-7-v1) |
| 8 | [Dinamica veicolo–binario–ponte con Ansys e Simpack: modellazione Beam–Beam](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/8/README.md) | 51 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-8-v1) |

Il titolo di ogni serie apre l’indice esistente delle singole lezioni. Le pagine release contengono video e sottotitoli scaricabili. La numerazione originale è conservata; non è presente una serie 4.

## Da dove iniziare

Per il primo modello di veicolo, si consiglia la **serie 6**. Per il binario flessibile, scegliere la **serie 1** con Abaqus o la **serie 3** con Ansys, quindi le **serie 5, 7 o 8** per i modelli veicolo–binario–ponte. La **serie 2** è dedicata al recupero di tensioni e deformazioni e alla fatica. È un percorso suggerito dalla redazione, non una sequenza verificata di prerequisiti.

## Guida agli argomenti

I gruppi seguenti organizzano i titoli delle lezioni disponibili. Non dimostrano una validazione indipendente dei modelli, dei risultati numerici o delle combinazioni di versioni software.

### Serie 1 — Dinamica accoppiata veicolo ferroviario–rotaia flessibile–soletta flottante con Abaqus e Simpack

- Modellazione della rotaia flessibile e della soletta flottante su molle in Abaqus; generazione FBI
- Scrittura dei file FTR e configurazione del binario flessibile in Simpack
- Modelli di sala montata, telaio del carrello e veicolo completo; accoppiamento con la soletta flottante
- Eccitazioni TRE / PSD, animazione dei corpi flessibili e post-elaborazione delle risposte

### Serie 2 — Analisi delle tensioni, delle deformazioni dinamiche e della fatica dei corpi flessibili con Ansys/Abaqus, Simpack e fe-safe

- Preparazione delle interfacce Abaqus / Ansys e generazione dei corpi flessibili FBI
- Configurazione dei corpi flessibili e recupero di tensioni e deformazioni in Simpack
- Visualizzazione di deformate, tensioni e deformazioni in Simpack Post
- Esportazione verso fe-safe, analisi a fatica ed esempio di flusso di lavoro integrato

### Serie 3 — Dinamica veicolo ferroviario–binario flessibile con Ansys Workbench Mechanical, APDL e Simpack

- Modello di rotaia a travi in SpaceClaim; riduzione per sottostrutture in Workbench Mechanical
- Procedure APDL tramite interfaccia grafica e comandi; gestione dell’interfaccia FBI
- Connessioni della fondazione FTR e configurazione in serie degli elementi di forza
- Veicoli semplificati, eccitazioni TRE / PSD, animazioni e parametri di post-elaborazione

### Serie 5 — Dinamica accoppiata veicolo–binario–ponte con Abaqus e Simpack

- Rotaie, lastre di binario CRTS III, strati di calcestruzzo, piastre di base e trave da ponte semplicemente appoggiata
- Materiali, mesh, attacchi, contatti interni e generazione di sottostrutture
- FBI / FTR, veicoli parametrizzati, equilibrio statico e accoppiamento veicolo–binario–ponte
- Precarico, solutore, irregolarità del binario e grandezze di valutazione dinamica trattate nei video

### Serie 6 — Introduzione alla dinamica dei veicoli ferroviari con Simpack

- Modellazione della sala montata e del telaio del carrello
- Assemblaggio del modello del veicolo completo
- File TRE ed eccitazione PSD
- Post-elaborazione e analisi delle risposte

### Serie 7 — Dinamica veicolo–binario–ponte con Ansys e Simpack: modellazione Beam–Solid

- RAIL-EULER, rail-timo, modelli di ponte con elementi solidi e argomenti modali
- File FBI di rotaia e ponte; scrittura e diagnosi dei file FTR
- Veicoli parametrizzati, ordine di accoppiamento, rigidezza e smorzamento delle zone di transizione
- Precarico, solutore, eccitazione, risposte di ponte e rotaia, organizzazione dei modelli

### Serie 8 — Dinamica veicolo–binario–ponte con Ansys e Simpack: modellazione Beam–Beam

- RAIL-EULER, rail-timo, modelli di ponte BEAM188 e argomenti modali
- Configurazione FBI / FTR, veicoli parametrizzati e accoppiamento veicolo–binario–ponte
- Creazione in serie di punti di connessione, collegamenti, appoggi e sensori
- Precarico, solutore, eccitazione, post-elaborazione e organizzazione dei modelli

## Download e utilizzo

Nella serie scelta, scaricare il video MP4 e il relativo file `.zh-CN.srt` o `.en.srt`. Conservare la parte comune del nome e selezionare il sottotitolo nel lettore video locale. È disponibile anche il formato VTT. Il clone del repository o l’archivio Code → Download ZIP non include i video memorizzati in Releases.

L’accesso ai download segue la visibilità del repository. Finché è privato, è necessario un account GitHub autorizzato. I collegamenti ai video consentono il download e non garantiscono un lettore streaming incorporato.

## Lingue

La presentazione e la guida agli argomenti sono disponibili in inglese, cinese semplificato, giapponese, francese, tedesco, italiano, spagnolo e coreano. La localizzazione riguarda i documenti e non aggiunge tracce di sottotitoli o doppiaggi. Le lingue attuali dei sottotitoli sono cinese e inglese. I titoli originali cinesi rimangono disponibili per identificare esattamente le lezioni.

## Ambito e limiti tecnici

Si tratta di una biblioteca di tutorial, non di un benchmark validato né di una distribuzione software. Un modello mostrato in un video non implica che siano inclusi i suoi file, le licenze del solutore o i dati di ingresso. Prima di adattare un procedimento, verificare versioni, unità, condizioni al contorno, smorzamento, impostazioni di riduzione e criteri di valutazione. Le discussioni su norme storiche non costituiscono indicazioni dei requisiti attuali. Beam–Solid e Beam–Beam identificano due percorsi, senza dimostrare una superiorità di precisione.

La presenza dei sottotitoli e la corrispondenza delle somme di controllo non provano la correttezza della traduzione o la sincronizzazione con l’audio. Verificare i termini tecnici nel video originale e nella documentazione del software.

## Correzioni e contributi

Per segnalare una correzione, indicare serie, identificativo stabile della lezione, lingua del sottotitolo ed eventuale riferimento temporale. Non modificare gli identificativi originali quando si migliora un titolo o una traduzione. Non caricare software commerciale, file di licenza, corsi di terzi o modelli senza le autorizzazioni necessarie.

## Fonti e autorizzazioni

La manutenzione del repository, la paternità dei corsi e i diritti sul software sono ruoli distinti. Consultare la dichiarazione di provenienza per le fonti e i diritti registrati. Non si dichiara alcuna affiliazione o approvazione ufficiale dei produttori. L’accesso pubblico non è una licenza generale di riutilizzo o ridistribuzione dei contenuti multimediali.

[Fonti e diritti](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/PROVENANCE.md)
