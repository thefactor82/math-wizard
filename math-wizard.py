import random
import time
from collections import deque, Counter
from inputimeout import inputimeout, TimeoutOccurred

# === CONFIGURAZIONI ===
vite_mago = 3
tempo_limite = 12  # secondi
debug = True  # True per output dettagliato

# === LIVELLI AUTOAPPRENDIMENTO ===
livelli = [
    {"esclusi": []},
    {"esclusi": [1]},
    {"esclusi": [1, 0]},
    {"esclusi": [1, 0, 2]},
    {"esclusi": [1, 0, 2], "inclusi": [11]},
    {"esclusi": [1, 0, 2, 3], "inclusi": [11]},
    {"esclusi": [1, 0, 2, 3], "inclusi": [11], "condizione_4": 6},
    {"esclusi": [1, 0, 2, 3], "inclusi": [11], "condizione_4": 7},
    {"esclusi": [1, 0, 2, 3], "inclusi": [11, 12]},
    {"esclusi": [1, 0, 2, 3, 4], "inclusi": [11, 12]}
]

def get_pool(livello_idx):
    base = list(range(0, 10))
    esclusi = livelli[livello_idx].get("esclusi", [])
    inclusi = livelli[livello_idx].get("inclusi", [])
    return [n for n in base if n not in esclusi] + inclusi

def genera_operandi(pool, livello_idx, reinforce_queue):
    if reinforce_queue and random.random() < 0.3:
        return reinforce_queue.popleft()

    while True:
        a = random.choice(pool)
        b = random.choice(pool)
        cond = livelli[livello_idx].get("condizione_4")
        if cond:
            if a == 4 and b < cond:
                continue
            if b == 4 and a < cond:
                continue
        return a, b

def chiedi_risposta_domanda(a, b):
    if debug:
        print(f"Quanto fa {a} × {b}? (Hai {tempo_limite} secondi)")
    else:
        print(f"Quanto fa {a} × {b}?")

    inizio = time.time()
    risposta = None

    try:
        risposta = inputimeout(prompt="Risposta: ", timeout=tempo_limite)
    except TimeoutOccurred:
        print("⏰ Tempo scaduto!")
    fine = time.time()
    tempo_impiegato = fine - inizio
    return risposta, tempo_impiegato

def gioco_autoapprendimento():
    while True:
        livello = 0
        vite = vite_mago
        tempi_risposta = []
        stats = {}
        reinforce_counter = Counter()
        reinforce_queue = deque()

        print("\n🧠 Modalità autoapprendimento attiva.")
        print("Scrivi '000' per uscire in qualsiasi momento.")
        input("🔀 Premi INVIO per iniziare...")

        blocco_corrente = []
        start_game_time = time.time()

        while vite > 0:
            richieste = 5 + sum(range(1, livello + 1))
            pool = get_pool(livello)
            a, b = genera_operandi(pool, livello, reinforce_queue)
            risultato_atteso = a * b

            if debug:
                print(f"\n⚔️ Livello {livello + 1} — Vite: {vite}")
                print(f"📈 Domande corrette: {sum(1 for esito, _ in blocco_corrente if esito)}/{richieste} — Ne mancano: {max(richieste - sum(1 for esito, _ in blocco_corrente if esito), 0)}")
            else:
                print(f"\nDomanda")

            risposta_raw, tempo = chiedi_risposta_domanda(a, b)
            tempi_risposta.append(min(tempo, tempo_limite))

            stats.setdefault(livello, {"corrette": 0, "sbagliate": 0, "tempi": []})

            if risposta_raw == "000":
                print("🚪 Uscita richiesta.")
                break

            risposta_corretta = False

            if risposta_raw is not None and risposta_raw.strip().isdigit():
                risposta = int(risposta_raw)
                if risposta == risultato_atteso:
                    print("✅ Corretto!")
                    stats[livello]["corrette"] += 1
                    risposta_corretta = True
                else:
                    print("❌ Sbagliato!")
                    print(f"La risposta corretta era: {risultato_atteso}")
                    input("Premi INVIO per continuare...")
                    stats[livello]["sbagliate"] += 1
                    vite -= 1
                    blocco_corrente.clear()
                    for _ in range(3):
                        reinforce_queue.append((a, b))
            else:
                print("⚠️ Risposta non valida o tempo scaduto!")
                print(f"La risposta corretta era: {risultato_atteso}")
                input("Premi INVIO per continuare...")
                stats[livello]["sbagliate"] += 1
                vite -= 1
                blocco_corrente.clear()
                for _ in range(3):
                    reinforce_queue.append((a, b))

            blocco_corrente.append((risposta_corretta, min(tempo, tempo_limite)))
            stats[livello]["tempi"].append(min(tempo, tempo_limite))

            if debug:
                print(f"⏱ Tempo di risposta: {tempo:.2f} secondi")

            if len(blocco_corrente) >= richieste:
                ultimi = blocco_corrente[-richieste:]
                corrette_blocco = sum(1 for esito, _ in ultimi if esito)
                tempi_blocco = [t for _, t in ultimi]
                if (
                    corrette_blocco == richieste
                    and sum(tempi_blocco) / richieste < 5
                    and livello < len(livelli) - 1
                ):
                    print(f"⬆️ Bravo! Passi al livello {livello + 2}")
                    livello += 1
                    blocco_corrente.clear()
                    reinforce_queue.clear()

        total_game_time = time.time() - start_game_time

        print("\n🎮 Fine della modalità autoapprendimento\n")
        tot_corrette = sum(v["corrette"] for v in stats.values())
        tot_sbagliate = sum(v["sbagliate"] for v in stats.values())
        print(f"✔️ Totale corrette: {tot_corrette}")
        print(f"❌ Totale sbagliate: {tot_sbagliate}")
        print(f"❤️ Vite rimaste: {vite}")
        print(f"📊 Tempo medio globale: {sum(tempi_risposta)/len(tempi_risposta):.2f} secondi")
        print(f"⏱ Tempo totale: {total_game_time:.2f} secondi")

        print("\n📋 Statistiche per livello:")
        for i, entry in stats.items():
            media = (sum(entry['tempi']) / len(entry['tempi'])) if entry['tempi'] else 0
            print(f"  Livello {i + 1}: ✔️ {entry['corrette']} / ❌ {entry['sbagliate']} — ⏱ Tempo medio: {media:.2f}s")

        scelta = input("\nVuoi ricominciare? (s/n): ").strip().lower()
        if scelta != 's':
            print("👋 Grazie per aver giocato!")
            break

def main():
    print("Benvenuto nel gioco delle tabelline!\n")
    while True:
        scelta = input("Scegli la modalità (c = classico / a = autoapprendimento): ").strip().lower()
        if scelta == "a":
            gioco_autoapprendimento()
            break
        elif scelta == "c":
            print("Modalità classico non implementata in questa versione.")
            break
        else:
            print("Scelta non valida. Scrivi 'c' o 'a'.")

if __name__ == "__main__":
    main()
