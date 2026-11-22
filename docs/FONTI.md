# Fonti consultate il 22 novembre 2026

## Condizioni e documentazione primaria

- Global Voices, [linee guida di ripubblicazione](https://globalvoices.org/about/global-voices-attribution-policy/): attribuzione, autore, collegamento e indicazione delle modifiche; i materiali di terzi possono avere condizioni differenti. [Licenza CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). Nessuna immagine viene copiata.
- Global Voices, [catalogo RSS](https://globalvoices.org/feeds/). Gli endpoint configurati devono superare il primo aggiornamento reale prima di essere considerati validati operativamente.
- ANSA, [RSS e condizioni](https://www.ansa.it/sito/static/ansa_rss.html): uso da reader non commerciale, divieto di pubblicazione dei titoli su siti web. Esclusa dal progetto.
- Rai News, [pagina RSS](https://www.rainews.it/rss): usata come riferimento per il lettore personale, non come licenza di ripubblicazione o trasformazione.
- BBC, [catalogo feed](https://support.bbc.co.uk/platform/feeds/NewsFeeds.htm). La lettura del feed World è stata tentata; nessuna traduzione o ripubblicazione pubblica è abilitata.
- GitHub, [billing Actions](https://docs.github.com/en/actions/concepts/billing-and-usage): standard runner gratuiti per repository pubblici; uso privato soggetto a quote e possibile fatturazione. Per questo i workflow sono limitati ai repository pubblici.
- GitHub, [limiti Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits): disponibilità su repository pubblici Free e limiti di traffico/dimensione.
- GitHub, [schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule): ritardi possibili e disattivazione per inattività nei repository pubblici.
- Ollama, [API chat](https://docs.ollama.com/api/chat), [Qwen3](https://ollama.com/library/qwen3), [Qwen3 4B](https://ollama.com/library/qwen3:4b): endpoint, output JSON, modelli multilingue locali e dimensioni.

## Articoli dell’edizione iniziale

Questi URL sono stati aperti e il testo è stato consultato tramite ricerca web. Le sintesi sono rielaborazioni brevi in italiano; la pipeline non dichiara di averli ottenuti via RSS. Le date sono quelle delle traduzioni italiane. Il timestamp normalizzato a mezzanotte nei metadati con `date_precision: day` serve all’ordinamento e **non è l’ora di pubblicazione dell’articolo**; la UI mostra solo il giorno.

| Articolo | Autore e traduzione | Data italiana |
| --- | --- | --- |
| [Cambogia e parchi della libertà](https://it.globalvoices.org/2026/11/cambogia-la-legge-sui-parchi-della-liberta-ha-limitato-il-diritto-di-manifestare-dei-cittadini/) | Mong Palatino; Amanda Mazzinghi | 19 novembre 2026 |
| [Orti scolastici in Camerun](https://it.globalvoices.org/2026/11/gli-orti-scolastici-rigenerativi-possono-rafforzare-la-sicurezza-alimentare-in-camerun/) | Sandra Tuombouh; Viviana | 17 novembre 2026 |
| [Radio e lingua romanì in Kosovo](https://it.globalvoices.org/2026/11/quando-la-radio-trova-una-nuova-voce-digitale-sono-online-la-cultura-e-la-lingua-romani-del-kosovo/) | Global Voices Central & Eastern Europe; Barbara Foggiato, Daniel Mauricio Sánchez Betancourt | 16 novembre 2026 |
| [Pressioni sul matrimonio in Cina](https://it.globalvoices.org/2026/11/le-donne-cinesi-nubili-stanno-riscrivendo-le-regole-del-matrimonio/) | Lina Ma; Sara Scibetta | 14 novembre 2026 |
| [Piattaforma di segnalazioni in Kosovo](https://it.globalvoices.org/2026/11/in-kosovo-una-nuova-app-rende-facile-e-veloce-segnalare-i-problemi-alle-autorita/) | Nurbek Bekmurzaev; Viviana | 11 novembre 2026 |

I contributi sul Kosovo sono ripubblicazioni/interviste dichiarate nel testo originale: le brevi sintesi non riproducono il materiale multimediale o il testo integrale. Sono approfondimenti, non una selezione rappresentativa dell’agenda mondiale. Le citazioni probatorie dell’edizione manuale provengono dal testo consultato; le future edizioni RSS possono usare esclusivamente titolo e anticipazione del feed.

I cinque articoli sono stati convertiti in `tests/replay.xml` per un test ripetibile. Quel file è un **replay costruito**, non un feed storico scaricato né una prova di disponibilità delle testate. Non viene usato automaticamente per sostituire feed irraggiungibili nella produzione.
