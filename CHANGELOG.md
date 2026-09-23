# Math Wizard — Release Notes

Release note cumulative dalla v1.3.53 alla v1.4.0 (rilascio attuale).

## 🚀 Novità

Opzioni plus (v1.4.0): quando un profilo ha sbloccato le opzioni extra (completando tutte le storie), sia in Storia sia in Allenamento dopo la prima schermata di configurazione compare una seconda schermata "OPZIONI - STORIA +" o "OPZIONI - ALLENAMENTO +". La prima opzione è "OPERANDO MANCANTE" (deselezionata di default, valida per tutte le operazioni): se attiva, in ogni domanda uno dei due operandi viene nascosto a caso e si risponde con l'operando mancante invece che con il risultato. L'impostazione è salvata nel config del profilo (chiave plus_missing_operand) e vale per ogni operazione.

Animazione del completamento (v1.3.53): quando un profilo ha completato tutte e quattro le storie al 100%, all'ingresso nel menu principale (dalla selezione del profilo o al ritorno da una partita) viene riprodotta una breve animazione celebrativa su sfondo delle opzioni: il mago entra da sinistra e si mette in posa da incantesimo, i quattro pendenti elementali compaiono ai quattro angoli, vibrano e convergono lentamente verso il centro fondendosi nel ciondolo magico; a fine sequenza appare il messaggio "Congratulazioni!" e con INVIO il mago esce di scena, lo sfondo sfuma e si torna al menu. Il flag "plus_unlocked" viene salvato nel config del profilo al completamento (ignorato se assente o false, per non rompere i profili esistenti, e i profili "vecchi" con le storie già completate lo ricevono alla prima apertura del menu) e sblocca le opzioni plus (v1.4.0).

## 🐛 Fix

Config dei profili in inglese (v1.3.54): nel config.json di ogni profilo le sezioni dei pool per operazione erano salvate due volte, con la chiave italiana e con quella inglese (es. "moltiplicazione" e "multiplication") e i dict per-operazione usavano chiavi italiane; ora il file usa solo chiavi inglesi (pool, story_progress, story_completed, initial_level_by_op, difficulty_position_by_op, story_operation) e la lettura normalizza entrambe le forme (retrocompatibile con i profili esistenti), preferendo quella inglese se presente. I profili esistenti sono stati migrati rimuovendo i duplicati italiani.

## ✨ Miglioramenti

Allineamento automatico dei profili (v1.3.55): all'avvio, prima della schermata di selezione del profilo, il config.json di ogni profilo viene allineato allo schema corrente: le chiavi legacy (genere, storia_*, difficolta_*, livello_*) vengono rinormalizzate in inglese e le variabili mancanti vengono inserite con i valori predefiniti, senza mai modificare i valori già impostati (scrittura solo quando effettivamente necessario, operazione idempotente).

## 🛠️ DevOps


## 🎨 Grafica

