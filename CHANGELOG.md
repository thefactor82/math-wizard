# Math Wizard — Release Notes

Release note cumulative dalla v1.3.53 alla v1.4.3 (rilascio attuale).

## 🚀 Novità

Tempo totale in sessione e fine livello (v1.4.3): oltre al "Tempo medio di risposta", nei file di sessione e nelle schermate di fine livello (livello completato, game over e partita terminata) viene ora riportato anche il "Tempo totale" (es. 2m 34s), calcolato come somma dei tempi di risposta della sessione.

Opzione plus "Tre Operandi" (v1.4.2): nella seconda schermata "OPZIONI - STORIA +" o "OPZIONI - ALLENAMENTO +" è disponibile un nuovo interruttore "Tre Operandi" (O)FF di default, ricordato nel config del profilo con la chiave plus_three_operands): se attivo, in ogni domanda vengono proposti 3 operandi invece di 2 (es. "5 + 3 + 6 = ?"), usando due valori dal pool A/B e un terzo operando c scelto dagli stessi valori del pool B. Tutti gli altri parametri sono rispettati: risultati interi (divisione esatta a/(b·c)), somma massima, percentuale di riporto e di prestito calcolate su 3 operandi e limiti minimo/massimo del risultato (per la sottrazione il risultato a - b - c rispetta l'intervallo scelto, quindi può essere negativo se il risultato minimo scende sotto lo zero). Con l'opzione "Operando Mancante" attiva contemporaneamente viene nascosto a caso uno dei 3 operandi ("..." al posto dell'operando); nelle moltiplicazioni con un qualsiasi operando pari a 0 (prodotto 0) viene accettata qualsiasi risposta. I log di sessione riportano gli errori con la forma "a op b op c = risposta".

Sottrazione con risultati negativi (v1.4.2): rimossa l'opzione "Differenza positiva" dalla schermata delle opzioni: non serve più, perché la positività è già garantita dal "Risultato Minimo" (con minimo 0 o superiore i risultati non possono essere negativi). Il valore "Risultato Minimo" ora può scendere anche sotto lo zero: impostandolo a un valore negativo si permettono operazioni di sottrazione con risultato negativo (il valore massimo resta limitato a 0 come minimo). I valori memorizzati nelle opzioni dei profili esistenti sono ignorati.

Opzioni plus (v1.4.0): quando un profilo ha sbloccato le opzioni extra (completando tutte le storie), sia in Storia sia in Allenamento dopo la prima schermata di configurazione compare una seconda schermata "OPZIONI - STORIA +" o "OPZIONI - ALLENAMENTO +". La prima opzione è "OPERANDO MANCANTE" (deselezionata di default, valida per tutte le operazioni): se attiva, in ogni domanda uno dei due operandi viene nascosto a caso e si risponde con l'operando mancante invece che con il risultato. L'impostazione è salvata nel config del profilo (chiave plus_missing_operand) e vale per ogni operazione.

Animazione del completamento (v1.3.53): quando un profilo ha completato tutte e quattro le storie al 100%, all'ingresso nel menu principale (dalla selezione del profilo o al ritorno da una partita) viene riprodotta una breve animazione celebrativa su sfondo delle opzioni: il mago entra da sinistra e si mette in posa da incantesimo, i quattro pendenti elementali compaiono ai quattro angoli, vibrano e convergono lentamente verso il centro fondendosi nel ciondolo magico; a fine sequenza appare il messaggio "Congratulazioni!" e con INVIO il mago esce di scena, lo sfondo sfuma e si torna al menu. Il flag "plus_unlocked" viene salvato nel config del profilo al completamento (ignorato se assente o false, per non rompere i profili esistenti, e i profili "vecchi" con le storie già completate lo ricevono alla prima apertura del menu) e sblocca le opzioni plus (v1.4.0).

## 🐛 Fix

Config dei profili in inglese (v1.3.54): nel config.json di ogni profilo le sezioni dei pool per operazione erano salvate due volte, con la chiave italiana e con quella inglese (es. "moltiplicazione" e "multiplication") e i dict per-operazione usavano chiavi italiane; ora il file usa solo chiavi inglesi (pool, story_progress, story_completed, initial_level_by_op, difficulty_position_by_op, story_operation) e la lettura normalizza entrambe le forme (retrocompatibile con i profili esistenti), preferendo quella inglese se presente. I profili esistenti sono stati migrati rimuovendo i duplicati italiani.

## ✨ Miglioramenti

Raffinamento delle opzioni plus (v1.4.1): schermata "OPZIONI +" riallineata allo stile delle opzioni normali (etichetta "Operando Mancante", toggle ON/OFF senza checkbox, rimosse le scritte di spiegazione e il pulsante "Indietro ESC", resta solo CONFERMA); l'opzione resta di default OFF e ricorda l'ultima scelta nel profilo. Nelle domande l'operando nascosto è indicato con "..." invece che con "?"; nelle moltiplicazioni con 0 (0 x ... o ... x 0) viene accettata qualsiasi risposta. Font dell'elenco "Ultime sessioni" nella schermata finale ridotto a 20px per mostrare più righe.

Allineamento automatico dei profili (v1.3.55): all'avvio, prima della schermata di selezione del profilo, il config.json di ogni profilo viene allineato allo schema corrente: le chiavi legacy (genere, storia_*, difficolta_*, livello_*) vengono rinormalizzate in inglese e le variabili mancanti vengono inserite con i valori predefiniti, senza mai modificare i valori già impostati (scrittura solo quando effettivamente necessario, operazione idempotente).

## 🛠️ DevOps


## 🎨 Grafica

