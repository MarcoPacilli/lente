# Verifica della consegna — 22 novembre 2026

| Verifica | Esito | Evidenza e limiti |
| --- | --- | --- |
| Analisi ZIP originale | Completata | HTML con 13 notizie incorporate; nessuna pipeline. Grafica e struttura conservate nella UI. |
| Test automatici Python | **15 superati** | `python -m unittest discover -s tests -v`, Python 3.12. Include server HTTP reale locale, parsing, pubblicazione JSON, preservazione dell’edizione, scarti e protocollo Ollama con risposta fittizia dichiarata. |
| Integrazione RSS → pipeline → JSON → HTTP | **Superata in replay locale** | `tests/test_http.py`. Articoli realmente consultati, trasformati in un feed locale per la prova; non una raccolta degli editori. |
| Sintassi JavaScript | **Superata** | `node --check web/app.js`, Node 24. Non certifica rendering o interazioni. |
| Struttura HTML e workflow YAML | Superata | ID HTML univoci, file YAML analizzabili. Non equivale a esecuzione Actions. |
| Tentativo raccolta live | **Bloccato** | `python -m pipeline.update --profile public --hours 168 --output test-results/live/news.json`: quattro risposte HTTP 403. Processo terminato con codice 2. Rapporto originale in `live-attempt.json`; nessuna edizione live generata. |
| Lettura articoli dell’edizione iniziale | Completata via web | Cinque pagine originali consultate; autori, date e collegamenti documentati in `FONTI.md`. Questa è una verifica dei contenuti dello snapshot, non della pipeline RSS. |
| Inferenza Ollama reale | **Non eseguita** | Modello e server non disponibili. Testato solo il protocollo HTTP, la cache e i controlli sugli output. |
| Browser desktop/mobile | **Bloccato prima del rendering** | Chromium termina con `socket() failed: Operation not permitted` all’avvio. Script `tests/e2e.py` consegnato; nessun test visivo/interattivo riuscito è dichiarato. |
| Pubblicazione e scheduler | **Predisposti, non attivati** | Nessun repository o account di destinazione collegato. Workflow da caricare ed eseguire secondo README. |
| 50–100 notizie/giorno e pluralità geografica | **Non raggiunti** | La prima edizione ha cinque approfondimenti e un solo gruppo editoriale; i feed pubblici abilitati appartengono a Global Voices. |

## Accettazione del primo avvio reale

1. Eseguire la suite Python e il test browser su un computer senza le restrizioni indicate.
2. Eseguire il comando di aggiornamento con rete libera, prima senza AI e poi con Ollama.
3. Controllare `origin: rss`, data aggiornata, stati feed, numero di articoli e URL originali apribili. Non basta l’exit code: una sola notizia valida può produrre un’edizione riuscita ma editorialmente incompleta.
4. Confrontare un campione di almeno dieci sintesi/traduzioni con gli originali e le evidenze, incluse negazioni, attribuzioni e incertezze. Gli esiti AI non revisionati restano etichettati.
5. Abilitare ulteriori gruppi editoriali solo dopo verifica tecnica e dei diritti d’uso. Controllare la distribuzione geografica e le lacune dichiarate.
6. Pubblicare, eseguire il workflow manualmente e controllare almeno una successiva esecuzione giornaliera prima di affidarsi allo scheduler.

Non sono state installate o attivate API a pagamento. Non è stato modificato il file ZIP originale allegato; questa consegna è una nuova versione separata.
