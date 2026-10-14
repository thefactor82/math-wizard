# Math Wizard — Release Notes

Changelog cumulativo dalla v1.5.3 alla v1.5.8.

## v1.5.8

### 🐛 Fix

Animazione del mostro colpito (v1.5.8): corretto un difetto grafico introdotto con l'ottimizzazione per l'hardware datato della v1.5.4. All'avvio dell'animazione di colpo poteva comparire per un istante un riquadro scuro al posto dello sfondo trasparente attorno al mostro, perché la dissolvenza non ripristinava la trasparenza per-pixel della sprite. La dissolvenza ora lavora su una copia dell'immagine; la correzione vale anche per la dissolvenza del boss sconfitto, per il cuore bonus e per l'oggetto mostrato nelle scene della Storia.

## v1.5.7

### 🚀 Novità

Opzione "Disuguaglianze" (v1.5.7): in Allenamento e Storia puoi trasformare le domande in confronti. Al posto di "=" compare un simbolo casuale "<" o ">" e al posto del risultato un valore vicino a quello corretto; si risponde con i pulsanti VERO/FALSO (col mouse) oppure con i tasti V/F e Invio. La nuova opzione è subito dopo "Operando Mancante", con cui è in mutua esclusione (attivandone una l'altra si disattiva e appare in grigio), e funziona anche insieme a "Tre Operandi" e "Operazioni Miste".

## v1.5.6

### 🚀 Novità

Pulsante "RIPROVA TIMEOUT ORIG" (v1.5.6): nella schermata di fine partita della Storia ora puoi ricominciare il livello mantenendo il timeout attuale (RIPROVA) oppure riportandolo al valore iniziale impostato (RIPROVA TIMEOUT ORIG). I tre pulsanti (RIPROVA, RIPROVA TIMEOUT ORIG, MENU PRINCIPALE) si adattano in larghezza alla scritta più lunga e restano sempre interamente visibili.

### 🐛 Fix

Riduzione del timeout in Storia (v1.5.6): il timeout si abbassa di 1 secondo ogni volta che completi un livello con tempo medio delle risposte inferiore alla metà del timeout, anche rigiocando una storia già completata (prima la riduzione era consentita solo sui livelli nuovi, quindi con una storia finita il timeout non scendeva mai). Il timeout non scende comunque mai sotto i 5 secondi.

### 🛠️ DevOps

Build (v1.5.6): la versione dell'applicazione viene ora letta da un'unica fonte (math-wizard.py) da entrambi gli spec PyInstaller. Il bundle macOS la usa nell'Info.plist come prima; l'eseguibile Windows la incorpora come risorsa VERSIONINFO (visibile in Proprietà → Dettagli), che prima era del tutto assente.

## v1.5.5

### 🐛 Fix

Schermata di fine partita in Storia (v1.5.5): i pulsanti RIPROVA e MENU PRINCIPALE non finiscono più sotto il bordo dello schermo quando il personaggio e il messaggio occupano molto spazio verticale. La schermata calcola prima il testo e poi, se serve, sposta verso l'alto personaggio, messaggio e pulsanti (ridimensionando il personaggio solo se rischia di sovrapporsi alle statistiche), così i pulsanti restano sempre interamente visibili. Negli altri casi il layout resta identico a prima.

## v1.5.4

### ✨ Miglioramenti

Prestazioni su hardware datato (v1.5.4): ridotto il carico di rendering per rendere più fluide le animazioni del fulmine e le dissolvenze. La scala a schermo riusa una superficie dedicata (niente più allocazione di ~8 MB per frame), il bagliore della bacchetta è pre-renderizzato e riutilizzato, le dissolvenze non duplicano più l'immagine a ogni frame e le transizioni della Storia (dissolvenza, testo e oggetto) sono ora basate sul tempo reale invece che sul numero di frame.

## v1.5.3

### 🐛 Fix

Timeout minimo in Storia (v1.5.3): nella modalità Storia il timeout non scende più sotto i 5 secondi; quando è già al minimo, le risposte veloci non lo abbassano ulteriormente e la scritta che annuncia l'abbassamento non viene mostrata.
