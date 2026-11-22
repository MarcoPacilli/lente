# Correzioni 0.2.1 — 22 novembre 2026

L'edizione online osservata dall'utente contiene due notizie ottenute dalla pipeline. La pubblicazione è riuscita, ma il volume e la pluralità restano insufficienti. Questa patch non rappresenta il raggiungimento di 50–100 notizie al giorno.

## Modifiche

- Corretto un errore di unità: la soglia di 36 ore era confrontata con un intervallo in millisecondi usando un numero espresso in secondi, facendo scattare l'avviso dopo circa 2 minuti e 10 secondi. Ora la soglia è corretta. L'età viene calcolata usando la data HTTP del server, l'età della cache e il tempo monotono della sessione. Non usa l'orologio del dispositivo. Se manca una data server valida non dichiara un'età non verificabile. La data di pubblicazione delle notizie non cambia.
- Il modello non sovrascrive più categoria e area geografica determinate dai metadati originali. Nepal è riconosciuto come Asia. La classificazione rimane euristica e può sbagliare; non è una geolocalizzazione verificata articolo per articolo.
- Output Ollama vincolato da JSON Schema; un tentativo aggiuntivo per output non valido, mantenendo i controlli su citazioni, numeri, fonti e URL. Dopo due output non validi l'articolo straniero resta escluso. Limite complessivo di 30 richieste nuove per esecuzione, compresi i tentativi aggiuntivi. Non c'è fallback a pagamento.
- Gli errori di sintesi, con titolo e motivo dello scarto, sono visibili nella finestra “Metodo e stato delle fonti”.
- El Salto (spagnolo) aggiunto al profilo pubblico. Endpoint ufficiale: https://www.elsaltodiario.com/general/feed . Politica RSS: https://www.elsaltodiario.com/comunidad/no-te-pierdas-ningun-articulo-rss . Licenza testi: https://www.elsaltodiario.com/comunidad/licencia ; CC BY-SA 3.0 ES: https://creativecommons.org/licenses/by-sa/3.0/es/ . Autore obbligatorio, nessuna immagine, licenza e attribuzioni conservate, rielaborazioni distribuite sotto la stessa licenza. La configurazione conta El Salto come secondo gruppo editoriale, non come copertura equilibrata già raggiunta. Il feed non è stato acquisito dalla pipeline in questo ambiente: deve essere verificato nella prossima esecuzione su GitHub.
- Il briefing mostra il numero effettivo di storie disponibili (fino a cinque), evitando di annunciarne cinque quando sono meno.

Documentazione primaria Ollama sul formato vincolato: https://docs.ollama.com/capabilities/structured-outputs . Lo schema riduce gli errori di formato, non certifica l'accuratezza semantica o la qualità della traduzione. Tutte le sintesi restano etichettate come automatiche non revisionate.

## Installazione su GitHub

Estrarre lo ZIP della patch. Nella pagina principale del repository usare Add file → Upload files e trascinare le cartelle `config`, `pipeline`, `web`, `tests` e `docs` contenute nella patch. Non trascinare la cartella contenitrice. I file omonimi saranno aggiornati. Premere Commit changes sul ramo main, poi avviare una nuova esecuzione del workflow quotidiano.

La patch non contiene `.github`, non sostituisce il workflow già corretto, non cambia l'orario o il limite di pubblicazione, non sovrascrive i JSON dell'edizione online e non contiene credenziali. La variabile LENTE_AI=true rimane necessaria.

## Verifiche locali

- 20 test Python superati, compresi replay HTTP e nuove regressioni su retry, scarto di output invalidi e metadati geografici.
- Sintassi `web/app.js` verificata con Node.
- `node tests/test_clock.js` superato: clock del dispositivo errato, avanzamento monotono, Age HTTP, scadenza reale e intestazione Date assente.
- Inferenza reale del modello, nuovo feed ed esecuzione GitHub da verificare dopo il caricamento. Test browser ancora non eseguibile qui per le restrizioni di sistema già documentate.

## Controllo dopo il primo aggiornamento

Aprire Lente, aggiornare la pagina e premere Ricarica edizione. Controllare quantità, data e una sintesi contro la fonte originale. Aprire Metodo e stato delle fonti per vedere lo stato del nuovo feed e gli articoli esclusi. Un workflow verde dimostra che almeno un articolo valido è stato pubblicato, non che tutte le traduzioni siano riuscite o che la copertura sia sufficiente. Il limite del workflow resta 15 notizie: il passo successivo richiede ampliare e bilanciare le fonti prima di aumentarlo.
