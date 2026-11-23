# Architettura corrente

UI statica originale → `web/data/news.json` e `status.json`.

Pipeline indipendente: feed RSS/Atom → metadati originali → controllo di date e domini → filtro lingua italiana → deduplica conservativa → selezione per freschezza e varietà → soglia minima di pubblicazione → JSON atomico.

Il ramo AI è separato e produce soltanto `drafts.json`, con stato non revisionato. Le evidenze sono ID risolti dal programma. Lo schema non è usato come certificazione di accuratezza linguistica o fattuale.

Il workflow giornaliero esegue prima test Python, JavaScript e browser. Poi raccoglie e prepara l'artefatto GitHub Pages nel job update; il job deploy pubblica quell'artefatto. Non committa contenuti giornalistici nel repository. La cache temporanea conserva l'ultima edizione valida per gestire fallimenti successivi. Un aggiornamento sotto soglia viene segnalato anche se il sito con l'edizione precedente è ancora disponibile.

La configurazione distingue editore, lingua, endpoint ufficiale, domini, uso pubblico, possibilità di elaborazione AI e metadati da preservare. La sede dell'editore non determina la geografia della notizia. Le diverse sezioni e lingue dello stesso gruppo non diventano fonti indipendenti.

La finestra predefinita è di 48 ore; la soglia minima è di dieci notizie e il limite del workflow è 50. Questi sono parametri, non un volume live già verificato. Le limitazioni e le prove sono in RIPRISTINO_0.3.md; i documenti delle versioni precedenti conservano valore storico, non descrivono il comportamento corrente.
