# Architettura e decisioni

Lo ZIP originale conteneva `index.html` (34.702 byte) e un README. Le tredici notizie erano incorporate nello script; nessun backend, fetch, API o schedulazione. L’interfaccia disponeva già di CSS responsive, filtri, ricerca, salvati locali e pannello laterale che diventa scheda mobile.

La v0.2 conserva i componenti e le regole responsive originali, separando HTML, CSS e JavaScript e rimuovendo i tredici esempi. Il browser legge soltanto `web/data/news.json` e `status.json`; non chiama testate o modelli e non contiene credenziali. Un server statico basta per accedere all’ultima edizione.

La pipeline usa la sola standard library Python, così può funzionare anche senza database o piattaforme con limiti di chiamate. Le fasi sono: fetch condizionale RSS/Atom con timeout e dimensione massima; verifica domini, date e metadati; estrazione dei soli titoli e anticipazioni; traduzione/sintesi locale opzionale con evidenze; deduplica conservativa; ordinamento per freschezza e diversità; validazione; scrittura atomica. La pubblicazione avviene solo con almeno un articolo valido. Un rapporto distinto registra anche i fallimenti senza spostare la data dell’ultima edizione.

Il modello locale è una scelta per evitare dipendenza da quote API gratuite variabili e da fatturazione cloud. È anche un limite: installazione, risorse e qualità devono essere verificati. Il sistema non promette fatti certificati da una validazione di schema e non considera automaticamente due URL come conferme indipendenti. Le evidenze sono visibili e le inferenze etichettate.

Il registro fonti distingue abilitazione del feed, lingua, gruppo editoriale, domini ammessi, trasformazione con AI e pubblicazione. Il profilo pubblico iniziale è deliberatamente ristretto ai contenuti Global Voices con attribuzione e licenza CC BY, senza immagini. Le fonti candidate di altre aree non sono presentate come già integrate o licenziate. L’ampliamento del numero di notizie dipende prima di tutto da questa copertura e dalla validazione editoriale, non dal valore numerico di `--limit`.

Per l’automazione vengono consegnati workflow GitHub, non un servizio già attivo. Su computer personale è possibile usare lo scheduler del sistema. Per un sito pubblico, GitHub Pages serve solo la directory `web`; Actions esegue il profilo pubblico e aggiorna l’edizione una volta al giorno. Preferiti e letture sono browser-locali. Non è previsto accesso privato nel percorso Pages gratuito.

Non c’è un archivio pubblico navigabile. Il workflow committa però i JSON: la storia Git contiene edizioni precedenti. Prima di ampliare le fonti, verificare anche la compatibilità di questa conservazione con le loro condizioni. La cache locale non è inclusa nello ZIP né pubblicata da Pages.
