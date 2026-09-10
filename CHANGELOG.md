# Math Wizard — Release Notes

Release note cumulative dalla v1.1.8 alla v1.3.51 (rilascio attuale).

## 🚀 Novità

Rendering nativo a 1920x1080 (v1.2.0): rendering con pygame.SCALED, scaling via GPU, ridimensionamento degli elementi UI e rimozione della pipeline di scaling manuale.
Opzioni di gioco nel menu principale (v1.2.3–v1.2.4): la configurazione dell'allenamento è spostata nel flusso del menu principale e le opzioni della storia vengono mostrate prima di avviare la modalità Storia (voce "Storia" rimossa dall'hub Opzioni).
Schermata Progressi (v1.2.5): nuova schermata che mostra l'avanzamento della storia per ogni operazione.
Pool numerici da levels.json (v1.2.7): supporto dei valori min_value/max_value letti da levels.json, mostrati anche nel pannello debug.
Selettore della difficoltà per la storia (v1.3.0–v1.3.2): barra di scorrimento orizzontale al posto dei pulsanti +/- (35 posizioni, finestra di 15 livelli), trascinamento con il mouse ed etichette con le classi scolastiche.
Vita bonus dopo 25 risposte consecutive (v1.3.7): la vita extra viene assegnata dopo 25 risposte esatte consecutive (in precedenza 30).
Musica di sottofondo (v1.3.8): musica in riproduzione con controllo del volume nelle opzioni e fade-in dopo la splash screen.
Musica dei livelli di storia (v1.3.17–v1.3.20): tracce level0–3.mp3 con selezione casuale senza ripetizioni consecutive; la stessa traccia resta attiva per i livelli della stessa storia e avanza automaticamente al termine; nome della traccia corrente e secondi trascorsi mostrati nel debug.
Riporto e Prestito configurabili (v1.3.21): probabilità di carry/borrow per addizione e sottrazione, con filtro degli operandi e controlli percentuali "Riporto" e "Prestito" nella configurazione.
Griglia dei pool di numeri (v1.3.30–v1.3.32): 8 colonne per tutte le operazioni con blocchi per decine e celle compatte; layout definitivo 10x2 con celle da 115px (moltiplicazione 0-19, altre operazioni a decine 0-199).
Progressi indipendenti per difficoltà (v1.3.33): si può giocare a qualunque livello di difficoltà in modo indipendente; il completamento della storia per operazione (100% con restart completo) viene rilevato automaticamente dai progressi esistenti al caricamento del profilo.
Divisione dai primi anni (v1.3.35): la divisione parte dalla 2ª elementare con 51 livelli (min_dp=6, max_dp=36) e curva di difficoltà appiattita; l'ultima posizione della difficoltà viene ricordata per ogni operazione.
Elementi delle operazioni (v1.3.36): pendente e boss elementale associati a ciascuna operazione (acqua, fuoco, terra, vento).
Livello iniziale proposto (v1.3.39): nella configurazione della storia viene proposto come livello iniziale l'ultimo livello raggiunto.
Difficoltà della moltiplicazione (v1.3.40): curva appiattita negli ultimi 15 livelli e pool limitati a 20 elementi.
Risoluzione finestra 1280x720 (v1.3.48): nelle opzioni grafiche la voce "Schermo" cicla tra intero, finestra 1920x1080 e finestra 1280x720; F11 alterna intero e l'ultima risoluzione finestra scelta, con preferenza salvata nel profilo.
Tutorial (v1.3.49): dopo la creazione di un profilo viene proposto un breve tutorial (Sì/No), raggiungibile anche da Opzioni con la voce "Tutorial" o il tasto 4; il livello di tutorial mostra sei dialoghi introduttivi, una domanda forzata 2+1 (solo risposta corretta, senza timeout/retry), dieci dialoghi di chiusura e l'uscita del personaggio a fine livello, per poi tornare al menu.
Dialoghi delle scene di livello (v1.3.49): le entry livello con una sceneggiatura "when: before/after" mostrano i dialoghi con la nuvola sopra il personaggio parlante (il player nei dialoghi del tutorial) prima e dopo le domande.

## 🐛 Fix

Sfondi neri su macOS (v1.1.8): superfici di sfondo opache, ridimensionamento display sicuro, percorsi case-sensitive e riconversione degli sprite al cambio di display.
Posa di colpo persistente (v1.2.1): fix del frame "hit" che restava attivo dopo il cambio di livello.
Crash nelle opzioni di allenamento (v1.2.2): fix del crash quando l'operazione selezionata non era l'addizione.
Progresso dell'ultimo livello (v1.2.6): fix del tracciamento del progresso per l'ultimo livello e layout migliorato delle barre di progresso.
Dissolvenza del background (v1.3.6): schermata di caricamento quando si avvia la storia da un livello > 0 e corretta dissolvenza dello sfondo.
Crossfade musicale (v1.3.9): corretti i riavvii continui che impedivano il ritorno alla musica di sottofondo; il crossfade prosegue anche in assenza di eventi.
ESC e musica in allenamento (v1.3.9): musica anche in allenamento con crossfade da 500ms, schermata di caricamento anche per l'allenamento e fix dello stato dopo il loading (fix ESC).
Timeout in allenamento (v1.3.11): fix del timeout al RIPROVA che ripristinava il valore salvato in config invece di usare quello corrente.
Hold-to-repeat (v1.3.12–v1.3.15): aggiunto e corretto il press-and-hold sui pulsanti +/- del volume, poi esteso a tutti i pulsanti +/- di opzioni, storia e allenamento; fix dell'allineamento verticale della percentuale nella schermata Progressi.
Box di input (v1.3.16): centratura corretta del box di input ed eliminato il jitter del cursore (testo e cursore renderizzati separatamente).
Riporto/prestito (v1.3.23–v1.3.26): corretto l'ordine del controllo needs_borrow (max/min come nella sottrazione post-swap), rispettata l'impostazione differenza_positiva e verificato il prestito con lo scambio degli operandi.
Click e allineamenti della configurazione (v1.3.27–v1.3.29): toggle allineati ai controlli [-/+] (12px) e spaziatura verticale uniforme; aree di click del selettore operazione allineate al disegno; opzioni storia riordinate come in allenamento.
Livello nel riepilogo (v1.3.37): la schermata di livello completato mostra il numero di livello relativo alla storia.
Difficoltà della divisione (v1.3.38): difficoltà massima allineata al lv.36 con 45 livelli e curva appiattita.
Livello iniziale per operazione (v1.3.43): il livello di partenza della storia resta indipendente per ogni operazione.
positive_difference (v1.3.44): inizializzazione corretta in modalità storia/auto ed evitato il crash del pannello debug.
Coda di rinforzo affidabile (v1.3.45): serve priority, nessuna ripetizione dopo un errore e nessun prelievo consecutivo della stessa domanda.
Riepilogo con il mouse (v1.3.46): il click del mouse avanza nella schermata di riepilogo livello e l'INVIO del tastierino numerico conferma il nome del profilo.
Flash del livello successivo (v1.3.47): il background del livello che sta per iniziare non compare più prima della dissolvenza dal buio.
Verifica della build Windows (v1.3.48): il controllo che i dati incorporati nell'exe fossero presenti applicava -notmatch a un array, fallendo sempre con un falso errore su data/story.json; ora l'unione in stringa restituisce un esito corretto.
Dialoghi delle scene senza npc (v1.3.49): se una scena ha dialoghi ma nessun personaggio non giocante (come quelle del tutorial, in cui parla il player), la nuvola di dialogo non veniva disegnata e i dialoghi avanzavano soltanto su INVIO; ora la nuvola viene mostrata sopra il personaggio parlante.
Rettangoli neri su macOS (v1.3.50): sulle build macOS la canvas veniva creata con un canale alpha (RGBA) e i blit con trasparenza (overlay, sprite, testo) ne corrompevano l'alpha, producendo quadrati neri semi-trasparenti sugli elementi dell'interfaccia (cuori, HUD, domanda, personaggio) e schermate completamente trasparenti nella splash; ora la canvas è forzata senza alpha (24bpp, come le build Windows), eliminando il difetto.
Box di input del profilo (v1.3.51): nella schermata di creazione del nuovo profilo il campo del nome non era centrato rispetto allo schermo e si spostava di un pixel per lato ad ogni lampeggio del cursore (testo e cursore renderizzati insieme, con '|' largo 19px e lo spazio 13px); ora testo e cursore sono renderizzati separatamente come nel box di risposta dei livelli, il box resta ancorato al centro dello schermo e la larghezza riservata al cursore è costante, eliminando lo spostamento.

## ✨ Miglioramenti

Grafica e testo (v1.3.5): font ridimensionati, barre di progresso corrette, rimosso il font Fredoka, font dedicato per il debug e pulsanti più larghi.
HUD e debug (v1.3.8): HUD più compatto e numero del livello relativo alla storia mostrato anche nel debug.
Pannello debug (v1.3.19/v1.3.22/v1.3.25): mostra la traccia musicale corrente con i secondi trascorsi, la percentuale di carry/borrow degli operandi correnti e lo stato Fallback (Sì/No) quando la selezione ripiega dopo 50 tentativi.
Progressi per difficoltà (v1.3.33): il progresso della storia traccia solo il livello di storia, indipendente dalla posizione di difficoltà.

## 🛠️ DevOps

Dati e build (v1.3.35): i file data/*.json vengono incorporati nelle build e la versione del bundle macOS è allineata.
Refactor interno (v1.3.41): nomi di storia/stati/operazioni normalizzati in costanti inglesi, con test per gli helper di normalizzazione.
Build macOS onedir-in-bundle (v1.3.50): il bundle passa da onefile-in-bundle a onedir-in-bundle, eliminando l'estrazione temporanea (_MEI*) a ogni avvio e rendendo l'avvio immediato anche su Apple Silicon (prima con ritardo di 10-15s); grafica, data/, fonts/ e music/ restano incorporati nel bundle. La verifica delle risorse nel workflow usa find all'interno del bundle anziché archive_viewer sull'EXE.

## 🎨 Grafica

Elementi elementali (v1.3.36): nuove grafiche per i pendenti (acqua, fuoco, terra, vento) e per i boss elementali associati alle operazioni.
Sprite di mostri e giocatore (v1.3.48): grafiche aggiornate per monster_earth/fire/water/wind e per il player maschile.