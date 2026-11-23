# Lente 0.3 — ripristino della raccolta

Questa versione parte dallo ZIP del repository online fornito dall'utente. Mantiene l'interfaccia e corregge i guasti misurati nel rapporto di produzione: sei articoli raccolti, cinque scartati per evidenze riscritte dall'AI, un solo articolo pubblicato con una cattiva traduzione, più un feed El Salto in errore HTTP 406.

## Comportamento della versione corretta

- Il notiziario usa titoli e anticipazioni RSS **già in italiano**, senza farli riscrivere dal modello. L'anteprima è attribuita alla fonte, non presentata come sintesi neutrale creata da Lente.
- Aggiunti sette feed ufficiali Euronews: mondo, Unione europea, economia, tecnologia, ambiente, salute e cultura. Sono sezioni di **un solo gruppo editoriale**, non sette fonti indipendenti. Si usano solo i metadati offerti dal servizio RSS, con attribuzione e link, senza immagini, video o articoli completi.
- Global Voices italiano resta attivo. Le altre lingue sono raccolte ma non diventano automaticamente notizie italiane. El Salto e le fonti non validate restano disabilitati.
- La soglia predefinita è **dieci notizie valide dopo la deduplica**. Un'edizione con una o due notizie viene rifiutata e non sovrascrive l'ultima valida.
- Il limite giornaliero del workflow è 50, entro una finestra di 48 ore. **Non significa che 50 articoli al giorno siano già stati ottenuti.** La UI mostra la finestra e le date delle singole notizie.
- Le traduzioni sperimentali diventano bozze separate, mai contenuti approvati automaticamente. Le evidenze vengono selezionate tramite ID e collegate dal codice al testo originale: non vengono più ricopiate dal modello.
- La cache conserva i metadati di sette giorni e viene invalidata se cambia la configurazione di una fonte. Una risposta HTTP 304 non impedisce più di ampliare la finestra di selezione.
- Il workflow non committa più i JSON delle notizie nel repository. Usa una cache temporanea per l'ultima edizione e un artefatto Pages di un giorno, evitando un archivio Git permanente dei metadati dei publisher.
- Gli avvisi di copertura insufficiente restano visibili. Un conteggio sufficiente non dimostra che la selezione sia completa, equilibrata o verificata da più testate.

## Installazione nel repository esistente

Il pacchetto di consegna ha due cartelle visibili, per evitare il problema del caricamento di `.github`:

1. Nella pagina principale `MarcoPacilli/lente`, scegliere **Add file → Upload files**. Aprire `PROGETTO` nel pacchetto estratto e trascinare **il suo contenuto** nel riquadro. Salvare con **Commit changes** sul ramo `main`.
2. Aprire la cartella `.github/workflows` già presente su GitHub. Usare **Add file → Upload files** e caricare **daily.yml e test.yml** contenuti nella cartella `WORKFLOWS` del pacchetto. Salvare con **Commit changes**.
3. Aprire Actions → **Lente · raccolta e pubblicazione quotidiana** → **Run workflow** su `main`.
4. Il workflow verifica codice e browser desktop/mobile prima di raccogliere e pubblicare. Se un controllo fallisce, il suo log è la fonte del risultato; non è necessario modificare il piano GitHub.

La vecchia variabile `LENTE_AI=true` non è più usata dal nuovo workflow: non serve cancellarla. Non sono richiesti nuovi account, token, API o servizi a pagamento. Non usare “Re-run jobs” per provare un file aggiornato: avviare una nuova esecuzione su `main`.

Il pacchetto contiene un JSON iniziale esplicitamente vuoto, in attesa della prima raccolta valida. Non include un notiziario artificiale e non ripropone l'articolo tradotto male come risultato aggiornato.

## Controllo del risultato

Aprire il sito pubblicato, aggiornare la pagina e premere **Ricarica edizione**. Controllare numero, data, finestra e attribuzioni. In fondo alla pagina, **Metodo e stato delle fonti → Scarica diagnostica** genera un solo JSON con edizione e rapporto della raccolta, senza preferiti o dati personali del browser.

Un aggiornamento sotto soglia termina con codice 2, conserva il precedente `news.json` e scrive il motivo in `status.json`. Il workflow pubblica il rapporto insieme all'ultima edizione disponibile, poi segnala l'esito fallito. Per un primo avvio senza precedente edizione valida, la UI resta in attesa: non inventa notizie.

La pubblicazione avviene su GitHub Pages, quindi il sito è pubblico. Il workflow è limitato ai repository pubblici su runner standard per evitare minuti a consumo in repository privati. La pianificazione resta alle 05:17 UTC, cioè 06:17 a Roma in inverno. GitHub può ritardare le esecuzioni e disattivare la pianificazione dei repository inattivi per 60 giorni. Il computer personale non deve rimanere acceso.

## Avvio locale

Richiede Python 3.10 o superiore:

```bash
python3 scripts/serve.py --open
```

Raccolta reale, senza AI:

```bash
python3 -m pipeline.update --profile public --limit 50 --min-stories 10 --hours 48
```

Profilo `personal`: può includere feed abilitati solo per lettura personale. Il suo risultato non deve essere caricato sul sito pubblico. Il workflow usa sempre `public`.

## Test e limiti della verifica

```bash
python3 -m unittest discover -s tests -v
node --check web/app.js
node tests/test_clock.js
```

Nell'ambiente di sviluppo sono passati **30 test Python**, la verifica sintattica JavaScript e i test dell'indicatore temporale. È stato verificato il percorso HTTP locale → RSS → CLI → soglia di pubblicazione → JSON su HTTP, con il replay dichiarato di articoli reali e data congelata. Questo non è una raccolta live dei nuovi feed.

Per il test browser:

```bash
pip install -r requirements-dev.txt
python3 -m playwright install chromium
CHROMIUM_PATH=playwright python3 tests/e2e.py
```

Chromium non si avvia in questo ambiente a causa di una restrizione di sistema sui socket; il test non viene dichiarato superato. Il workflow lo esegue sul runner GitHub prima della pubblicazione. Il replay verifica interazioni, filtri, salvataggi, fonti, escaping e vista mobile, non la disponibilità degli editori o la qualità di un modello.

Le richieste dirette ai publisher sono bloccate in questo ambiente. Le pagine ufficiali di Euronews elencano gli endpoint configurati, ma **il primo aggiornamento riuscito su GitHub è ancora necessario** per validarli operativamente. Non è stato verificato un notiziario live con 10, 30 o 50 articoli. Non è stata dimostrata una selezione equilibrata fra più testate.

## AI sperimentale

L'AI non serve al notiziario principale. Per sperimentare sul proprio computer, installare Ollama e scaricare un modello locale:

```bash
ollama pull qwen3:4b
python3 -m pipeline.update --ai ollama --limit 50
```

Le bozze sono scritte in `web/data/drafts.json` e hanno stato `unreviewed`. Non entrano nell'elenco delle notizie. Gli ID delle evidenze sono limitati a titolo e anticipazione; il codice collega la citazione esatta e l'ID fonte. Rimangono i controlli su schema, numeri e URL, ma non certificano correttezza semantica o buon italiano. Il modello reale non è stato eseguito in questo ambiente.

Nel workflow, l'eventuale variabile `LENTE_EXPERIMENTAL_AI=true` attiva il modello locale sul runner, sempre solo per bozze. Il modello piccolo usato nelle versioni precedenti non viene più scaricato automaticamente.

## Copertura ancora da completare

L'obiettivo originale di 50–100 notizie al giorno da fonti di aree e lingue diverse, con sintesi editorialmente affidabili, **non è ancora raggiunto**. Questa versione ripristina prima una raccolta verificabile di anticipazioni italiane. Il contesto aggiuntivo non disponibile nel feed non viene inventato. La pluralità, la selezione per importanza, la deduplica semantica fra lingue e le sintesi automatiche di qualità richiedono ancora validazione.

Per dettagli sulle cause, sulle fonti e sulle prove, vedere `docs/RIPRISTINO_0.3.md`. Il codice resta separato dalla UI. Preferiti e letture restano sul dispositivo; account privati, sincronizzazione e notifiche non sono implementati.
