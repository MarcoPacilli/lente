# Diagnosi e verifiche della versione 0.3

## Evidenze effettive

Snapshot analizzato: ZIP `lente-main.zip`, commit `988bed06b8b93485da07deea0c92b255f6ab6f3b`, rapporto del 22 novembre 2026 alle 14:36:25 UTC. I due JSON di produzione sono conservati come fixture di regressione in `tests/fixtures/production-*.json`, senza usarli come edizione pubblicata.

- Sei articoli raccolti: quattro Global Voices EN, due ES, zero IT/FR nella finestra.
- Cinque scarti con identico errore `Evidenza non riscontrata`.
- El Salto risponde HTTP 406; non è un problema di GitHub Pages.
- Un solo testo supera i controlli, ma contiene errori linguistici osservabili (“all'Corte Internazionale di Criminalità”, “abstracti”). La validazione di schema non è una valutazione editoriale.
- L'exit code di successo dipendeva soltanto dall'esistenza di almeno un articolo.
- La cache salvava solo gli elementi della finestra corrente. Un feed invariato con HTTP 304 non poteva recuperare articoli precedentemente esclusi ampliando la finestra.

## Correzioni

1. Separazione tra raccolta delle anticipazioni italiane e produzione di bozze AI. Il modello non riscrive l'italiano già disponibile e non blocca la raccolta principale.
2. Evidenze collegate programmaticamente tramite enum `t` e `d`, invece di chiedere al modello di ricopiare letteralmente la fonte. Gli ID sconosciuti sono rifiutati.
3. Nessuna pubblicazione automatica dei testi generati non revisionati. Il vecchio articolo mal tradotto, se ancora presente in un JSON legacy, viene nascosto dalla lista della UI.
4. Soglia predefinita di dieci notizie valide dopo la deduplica, con conservazione dell'ultima edizione se il candidato è insufficiente.
5. Cache di sette giorni, fingerprint della politica della fonte e ricontrollo della finestra dopo HTTP 304.
6. Nessun commit dei dati delle testate nella storia Git. Il workflow usa cache temporanea e artefatto Pages con retention di un giorno.
7. Test browser inserito prima della raccolta e pubblicazione nel workflow. Resta separato dalla verifica live delle fonti.

## Fonti e condizioni

Euronews offre widget e feed RSS per l'integrazione nelle pagine web:

- https://it.euronews.com/follow-us
- https://it.euronews.com/widgets
- https://it.euronews.com/terms-and-conditions

Gli endpoint sono quelli collegati dalla pagina ufficiale widgets (Mondo, Notizie UE, Business, Next, Terra, Salute, Cultura). Il feed Europa verticale `my-europe` ha risposto 404 nel controllo via web e non è stato inserito.

L'uso configurato è ristretto a un lettore personale non commerciale che mostra **titolo e anticipazione RSS originali, attribuzione e collegamento**. Non viene attribuita una licenza Creative Commons a Euronews, non si trasformano i suoi testi con AI e non si scaricano foto, video o pagine articolo. Le condizioni generali non autorizzano il riuso indiscriminato degli articoli: l'integrazione si basa sul servizio specifico RSS offerto per le pagine web e resta limitata ai suoi metadati. Per un prodotto commerciale o per ampliare il riuso serve una verifica separata dei diritti.

Global Voices conserva attribuzioni e licenza CC BY 3.0. Le sue versioni linguistiche sono un solo gruppo editoriale. El Salto è disabilitato dopo il 406 di produzione. Valigia Blu è registrata ma disabilitata perché il feed non è stato verificato; il sito dichiara CC BY-SA 4.0 nel footer. Nessuna fonte disabilitata è contata come copertura disponibile.

Il volume principale può quindi dipendere da un solo gruppo. La UI lo segnala esplicitamente, anche se sono presenti sette sezioni. Una raccolta ampia da una testata non equivale a pluralità o neutralità.

## Risultati verificati localmente

- 30 test Python superati.
- Test di integrazione con feed di replay servito da HTTP locale, invocazione della CLI con data congelata, soglia dichiarata di tre per il solo fixture e quattro articoli originali restituiti via HTTP.
- Regressioni sui cinque scarti reali, quarantena della vecchia traduzione, associazione delle evidenze senza generazione di citazioni, nessuna chiamata al modello per l'italiano, mancata sovrascrittura con un solo articolo e ampliamento della finestra di cache dopo HTTP 304.
- `node --check web/app.js` e test dell'indicatore temporale superati.
- YAML dei workflow analizzabile; artefatto Pages preparato prima del deploy, nomi coerenti e permessi di lettura.

## Verifiche ancora non completate

Le richieste dirette ai publisher restituiscono HTTP 403 dall'ambiente di sviluppo. Il lettore web conferma la presenza di più feed Euronews restituendo un tipo XML che non supporta, ma non fornisce i byte del feed alla pipeline. Non si dichiara quindi una raccolta live riuscita dei nuovi endpoint.

Chromium termina all'avvio con `socket() failed: Operation not permitted`; il test browser desktop/mobile non è passato qui. Il workflow lo esegue su GitHub. Non è stata eseguita inferenza reale di Ollama e non viene rivendicata la qualità del suo italiano.

Per l'accettazione operativa serve una nuova esecuzione GitHub completa, con test browser riuscito, almeno dieci articoli italiani validi, controllo di un campione contro le fonti e lettura delle lacune di copertura. Il target 50–100 e la pluralità geografica/editoriale restano obiettivi da misurare, non risultati conseguiti.
