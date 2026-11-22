# Lente 0.2

La grafica della demo è conservata. Ora la UI legge un’edizione JSON prodotta da una pipeline Python separata: RSS/Atom → normalizzazione → italiano → deduplica → selezione → pubblicazione atomica.

**Stato della consegna:** codice implementato e test automatici della pipeline superati, inclusa integrazione su HTTP locale. La raccolta live degli editori restituisce HTTP 403 in questo ambiente; Ollama non è installato e Chromium è bloccato dalle restrizioni del sistema. Pertanto **non dichiariamo verificato l’end-to-end live**, la qualità del modello o l’aspetto su browser reale. I test browser riproducibili sono inclusi. Nessun sito è stato pubblicato e nessuna schedulazione remota è stata attivata.

La prima apertura mostra **cinque approfondimenti reali di Global Voices**, consultati il 22 novembre 2026, etichettati come fotografia manuale. Non sono notizie raccolte oggi via RSS e non sono il riuso delle 13 notizie della demo. Alcuni sono traduzioni di articoli meno recenti. Le loro date rimangono visibili.

## Prova in due minuti

Richiede Python 3.10 o superiore; nessuna dipendenza per usare la UI e raccogliere i feed. Estrai lo ZIP e apri il terminale nella cartella che contiene questo README.

```bash
python3 scripts/serve.py --open
```

Apri `http://localhost:8000`. Su Mac è disponibile anche `AVVIA.command`; se macOS non permette il doppio clic, usa il comando sopra. Il computer deve restare acceso mentre consulti il sito locale. Il doppio clic su `web/index.html` non basta perché il browser deve caricare il JSON via HTTP.

Per telefono sulla stessa rete Wi-Fi:

```bash
python3 scripts/serve.py --host 0.0.0.0
```

Apri sul telefono `http://IP-LOCALE-DEL-COMPUTER:8000`. Usa una rete fidata; questo server è per sviluppo, senza autenticazione. Per accesso da qualsiasi rete vedi il piano di pubblicazione sotto.

## Aggiornamento vero dai feed

In un terminale separato, dalla cartella del progetto:

```bash
python3 -m pipeline.update --profile personal --limit 30 --hours 48
```

Poi premi **Ricarica edizione** nell’app. Il pulsante rilegge l’edizione; non lancia una raccolta dal browser. Il profilo `personal` usa metadati dei feed abilitati per lettura personale. Il profilo `public` esclude tutte le fonti prive di autorizzazione esplicita alla ripubblicazione nella configurazione.

Senza AI vengono pubblicati solo gli articoli già in italiano. Titolo e anticipazione RSS sono etichettati come estratti, non come nuove sintesi. Il contesto mancante non viene inventato. Le fonti straniere restano nel rapporto di raccolta ma non vengono presentate come tradotte.

Se non esistono articoli validi, l’aggiornamento termina con codice 2, scrive `web/data/status.json` e **mantiene intatto** `web/data/news.json`. La UI segnala il fallimento e l’eventuale età dell’edizione. Con meno di 30 articoli validi, pubblica soltanto quelli disponibili. Per provare una finestra più ampia si può usare `--hours 168`: non significa avere 168 ore di notizie nuove e non cambia le date originali.

## Traduzione e sintesi italiana senza API a pagamento

È implementato un adattatore per **Ollama locale**, che esegue un modello aperto sul computer. Nessuna chiave API, abbonamento o servizio cloud necessario. Servono spazio su disco, RAM, tempo di calcolo ed energia del proprio computer. Un modello piccolo può tradurre male: la qualità va valutata prima dell’uso quotidiano.

1. Installa [Ollama](https://ollama.com/download).
2. Avvia Ollama e scarica il modello:

```bash
ollama pull qwen3:4b
```

3. Esegui:

```bash
python3 -m pipeline.update --profile personal --ai ollama --limit 15
```

Il modello indicato occupa circa 2,5 GB per i pesi; la RAM necessaria in esecuzione è maggiore. È possibile scegliere un modello locale più piccolo, con qualità da verificare:

```bash
ollama pull qwen3:1.7b
OLLAMA_MODEL=qwen3:1.7b python3 -m pipeline.update --profile public --ai ollama --limit 15
```

`OLLAMA_URL` accetta solo loopback HTTP; non sono ammessi endpoint remoti o modelli con suffisso `:cloud`. `.env.example` documenta le variabili; i file `.env` **non vengono caricati automaticamente**. Nessuna credenziale è presente o necessaria. I contenuti RSS vengono inviati solo al servizio locale, senza strumenti, accesso web o esecuzione di istruzioni presenti nei feed.

L’AI opera soltanto sulle fonti con `ai_allowed: true`: nella configurazione iniziale sono le edizioni Global Voices. I titoli BBC non sono tradotti in assenza di un permesso configurato. Gli estratti di Rai restano invariati.

Ogni punto generato deve avere un ID fonte e un’evidenza letterale presente nei metadati originali. Schema, limiti di lunghezza, numeri non presenti, URL inventati e citazioni inesistenti vengono controllati. **Questi controlli non garantiscono equivalenza semantica, lingua o assenza di allucinazioni.** Per questo la UI dichiara “Sintesi automatica · da verificare”. Se la validazione fallisce, usa l’estratto italiano originale oppure esclude la traduzione. Non esiste fallback a pagamento. Sono ammesse al massimo 30 richieste nuove al modello per esecuzione, con timeout di 90 secondi e interruzione delle ulteriori chiamate in caso di indisponibilità; gli esiti validi sono riutilizzati dalla cache.

## Test

```bash
python3 -m unittest discover -s tests -v
node --check web/app.js
```

I test verificano parsing RSS/Atom, URL e date, HTML ostile, deduplica, scarto di traduzioni mancanti, copertura, HTTP 304, fallimenti, preservazione dell’ultima edizione e protocollo HTTP Ollama con server fittizio dichiarato. L’integrazione HTTP usa articoli reali convertiti in un feed di replay, **non un feed scaricato dagli editori**.

Per il test completo in browser:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python3 -m playwright install chromium
CHROMIUM_PATH=playwright python3 tests/e2e.py
```

`tests/e2e.py` esegue replay RSS → pipeline → JSON → HTTP → UI desktop/mobile, controlla apertura schede, fonti, ricerca, filtro geografico, salvati persistenti, errori di caricamento, escaping e focus mobile. Usa un browser vero; non misura la qualità dell’inferenza o la disponibilità live degli editori. Se usi un Chromium di sistema, imposta `CHROMIUM_PATH` al suo eseguibile. Vedi [rapporto di verifica](docs/VERIFICA.md).

## Fonti e copertura: limiti espliciti

Configurazione in `config/sources.json`. I domini articolo e i redirect sono vincolati alle allowlist. Non vengono scaricate pagine articolo, aggirati paywall o copiate immagini. Ogni scheda riporta testata, autore disponibile, data, lingua, titolo originale, collegamento e licenza se prevista.

| Fonte | Profilo personale | Profilo pubblico | Sintesi locale |
| --- | --- | --- | --- |
| Global Voices IT/EN/ES/FR | Abilitata | Abilitata, CC BY 3.0 | Abilitata |
| Rai News Esteri | Abilitata come lettore RSS | Esclusa | Esclusa |
| BBC World | Raccolta metadati, esclusi dalla UI se manca traduzione consentita | Esclusa | Esclusa |
| DW, Al Jazeera, France 24 | Candidate disabilitate | Escluse | Escluse |
| ANSA | Esclusa | Esclusa | Esclusa |

Le diverse lingue di Global Voices sono **un solo gruppo editoriale**. L’edizione iniziale e il profilo pubblico non soddisfano ancora l’obiettivo di pluralità fra grandi testate di aree differenti. Le fonti candidate non sono integrazioni validate; abilitarle richiede verificare endpoint, condizioni d’uso e diritto di trasformazione. La presenza di un feed non autorizza automaticamente a pubblicarne una versione sintetizzata.

La classificazione geografica usa il contenuto e i tag, non la sede dell’editore. L’ordine favorisce freschezza e varietà di aree, categorie e gruppi; non è un giudizio assoluto sull’importanza. Le lacune sono mostrate, non riempite con notizie inventate. La deduplica è conservativa per URL e titoli simili (anche dopo traduzione), con guardie su date e numeri. Può lasciare duplicati e perdere abbinamenti fra lingue. Le coperture correlate non vengono contate come verifiche indipendenti. Le informazioni contrastanti restano attribuite alle rispettive fonti.

## Pubblicazione e aggiornamento giornaliero a costo zero

Il percorso predisposto è GitHub Pages + Actions in un repository pubblico, senza dominio personalizzato né API cloud. È adatto a un sito consultabile da telefono e computer, ma **il sito è pubblico**: l’uso personale non implica accesso privato. I workflow inclusi non eseguono job in repository privati, per evitare minuti a consumo non autorizzati.

1. Crea un repository pubblico gratuito e carica il **contenuto** di questa cartella, compresa `.github` (non la cartella contenitrice).
2. In Settings → Pages scegli **GitHub Actions** come sorgente.
3. Consenti al workflow di scrivere i file dell’edizione nel repository; il job dichiara `contents: write`. Se la policy dell’account lo impedisce, serve modificarla o usare aggiornamento e caricamento manuali. Non servono token personali.
4. Esegui il workflow **Lente · verifiche** e controlla che passino anche i test browser.
5. Esegui **Lente · raccolta e pubblicazione quotidiana** manualmente; verifica un’edizione con `origin: rss`, fonti OK e date corrette prima di considerare operativo il servizio.
6. Per l’AI gratuita sul runner CPU, crea la variabile di repository `LENTE_AI=true`. Il job usa un contenitore Ollama locale e `qwen3:1.7b`, senza GPU o provider a pagamento. **Questa configurazione non è stata eseguita qui**: download, durata, compatibilità e qualità vanno verificati sul primo run. Il job ha limite di 45 minuti. Lascia la variabile assente per il solo RSS italiano.

La raccolta è programmata alle **05:17 UTC**, cioè 06:17 a Roma in inverno e 07:17 in estate. Non è una garanzia di puntualità: GitHub può ritardare o saltare esecuzioni e disattiva le pianificazioni dei repository pubblici senza attività per 60 giorni. Le Actions standard nei repository pubblici sono gratuite; Pages ha limiti di utilizzo. Non attivare runner grandi o opzioni a pagamento. La cache conserva solo metadati ed esiti AI, non i pesi del modello. Gli artefatti temporanei hanno durata di un giorno. Il commit quotidiano conserva la storia delle edizioni: non inserire dati privati e rivaluta la conservazione se aggiungi fonti con limiti specifici.

Il workflow pubblica esclusivamente il profilo `public`. Un errore di raccolta conserva l’edizione precedente, pubblica lo stato del tentativo e fa risultare fallita l’esecuzione. Un errore infrastrutturale precedente alla raccolta può impedire anche l’aggiornamento dello stato: l’età dell’edizione e il log Actions restano gli indicatori.

Alternativa interamente locale: pianifica il comando con cron/Utilità di pianificazione del computer, che deve restare acceso. Esempio cron su un computer con fuso Europe/Rome, sostituendo i percorsi:

```cron
17 7 * * * cd /PERCORSO/lente-v0.2 && /PERCORSO/python3 -m pipeline.update --profile personal --ai ollama --limit 15 >> /PERCORSO/lente-update.log 2>&1
```

Un cron locale non rende da solo l’app raggiungibile da fuori casa. Non aprire porte del router per il server di sviluppo.

## Cosa manca per il target finale

- Un aggiornamento reale completato e verificato su rete libera, da almeno tre gruppi editoriali con condizioni compatibili.
- Verifica editoriale delle traduzioni e delle sintesi con un modello locale reale.
- Test browser eseguito con successo e verifica visiva su dispositivi reali.
- Pubblicazione del sito e prima esecuzione dello scheduler nell’account dell’utente.
- Misura per almeno sette giorni di freschezza, duplicati, distribuzione geografica e tempi prima di portare il limite a 50–100. Il numero si configura con `--limit`, ma **non è già raggiunto né garantito**.

Salvati e letture restano sul dispositivo. Non sono implementati account, sincronizzazione cloud, notifiche o lettura offline. Nessun servizio a pagamento è stato attivato.

## Struttura

- `web/`: interfaccia originale evoluta, senza framework o dipendenze esterne.
- `pipeline/`: raccolta, selezione, validazione e adattatore Ollama.
- `config/sources.json`: registro fonti, domini, lingue e permessi.
- `tests/`: test automatici, replay dichiarato e percorso browser.
- `.github/workflows/`: verifiche, aggiornamento e pubblicazione.
- `docs/`: architettura, fonti consultate, esiti e blocchi di verifica.

Il codice nuovo è disponibile con licenza MIT (vedi `LICENSE`). La grafica fornita dall’utente resta dell’utente; i contenuti delle testate conservano le rispettive licenze, attribuzioni e limitazioni.
