import pygame
import random
import sys
from collections import deque

# === CONFIGURAZIONI ===
VITE_MAGO = 3
TEMPO_LIMITE = 12
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
GREEN = (50, 220, 50)
YELLOW = (255, 255, 0)
GOLD = (255, 215, 0)
GRAY = (100, 100, 100)
DARK = (20, 20, 30)
BG_DARK = (30, 30, 50)

LIVELLI = [
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
    esclusi = LIVELLI[livello_idx].get("esclusi", [])
    inclusi = LIVELLI[livello_idx].get("inclusi", [])
    return [n for n in base if n not in esclusi] + inclusi

def genera_operandi(pool, livello_idx, reinforce_queue):
    if reinforce_queue and random.random() < 0.3:
        return reinforce_queue.popleft()
    while True:
        a = random.choice(pool)
        b = random.choice(pool)
        cond = LIVELLI[livello_idx].get("condizione_4")
        if cond:
            if a == 4 and b < cond:
                continue
            if b == 4 and a < cond:
                continue
        return a, b

class Gioco:
    def __init__(self):
        pygame.init()
        self.fullscreen = False
        self.flags = pygame.SCALED
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), self.flags)
        pygame.display.set_caption("Math Wizard - Impara le tabelline!")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "menu"

        self.font_titolo = pygame.font.Font(None, 80)
        self.font_grande = pygame.font.Font(None, 64)
        self.font_medio = pygame.font.Font(None, 42)
        self.font_piccolo = pygame.font.Font(None, 30)
        self.font_input = pygame.font.Font(None, 56)
        self.font_stats = pygame.font.Font(None, 28)

        self.carica_risorse()
        self.azzera_partita()

    def carica_risorse(self):
        bg = pygame.image.load("background.png")
        self.bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

        char_sheet = pygame.image.load("char.png").convert_alpha()
        monster_sheet = pygame.image.load("monster.png").convert_alpha()

        cw, ch = 900, 1330
        mw, mh = 1500, 1619
        self.char_img = pygame.transform.scale(char_sheet, (160, int(160 / cw * ch)))
        self.monster_img = pygame.transform.scale(monster_sheet, (200, int(200 / mw * mh)))

        self.char_h = self.char_img.get_height()
    def azzera_partita(self):
        self.vite = VITE_MAGO
        self.livello = 0
        self.corretto = 0
        self.a = 0
        self.b = 0
        self.risultato_atteso = 0
        self.input_utente = ""
        self.mostro_progresso = 0.0
        self.mostro_x = SCREEN_WIDTH - 150
        self.mostro_colpito = False
        self.domanda_attiva = False
        self.feedback = None
        self.feedback_timer = 0
        self.game_over = False
        self.inizio_domanda = 0
        self.anim_frame = 0
        self.anim_timer = 0
        self.timeout_gestito = False

        self.tempi_risposta = []
        self.blocco_corrente = []
        self.coda_rinforzo = deque()
        self.stats = {}

    def nuova_domanda(self):
        if self.vite <= 0:
            return
        pool = get_pool(self.livello)
        self.a, self.b = genera_operandi(pool, self.livello, self.coda_rinforzo)
        self.risultato_atteso = self.a * self.b
        self.input_utente = ""
        self.mostro_progresso = 0.0
        self.mostro_colpito = False
        self.domanda_attiva = True
        self.feedback = None
        self.feedback_timer = 0
        self.timeout_gestito = False
        self.inizio_domanda = pygame.time.get_ticks()

        richieste = 5 + sum(range(1, self.livello + 1))
        fatte = sum(1 for esito, _ in self.blocco_corrente if esito)
        self.domande_mancanti = max(richieste - fatte, 0)

    def gestisci_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                self.fullscreen = not self.fullscreen
                flags = self.flags
                if self.fullscreen:
                    flags |= pygame.FULLSCREEN
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
                return
            if self.state == "menu":
                if event.key == pygame.K_RETURN:
                    self.state = "gioco"
                    self.azzera_partita()
                    self.nuova_domanda()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
            elif self.state == "gioco":
                if event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                elif self.domanda_attiva:
                    if event.key == pygame.K_RETURN and self.input_utente:
                        self.controlla_risposta()
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_utente = self.input_utente[:-1]
                    elif event.unicode.isdigit() and len(self.input_utente) < 6:
                        self.input_utente += event.unicode
            elif self.state == "gameover":
                if event.key == pygame.K_r:
                    self.state = "gioco"
                    self.azzera_partita()
                    self.nuova_domanda()
                elif event.key == pygame.K_m:
                    self.state = "menu"
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

    def controlla_risposta(self):
        if not self.domanda_attiva:
            return

        tempo = min((pygame.time.get_ticks() - self.inizio_domanda) / 1000.0, TEMPO_LIMITE)
        self.tempi_risposta.append(tempo)

        livello = self.livello
        self.stats.setdefault(livello, {"corrette": 0, "sbagliate": 0, "tempi": []})

        if self.input_utente.strip().isdigit():
            risposta = int(self.input_utente)
            if risposta == self.risultato_atteso:
                self.corretto = True
                self.stats[livello]["corrette"] += 1
                self.mostro_colpito = True
            else:
                self.corretto = False
                self.stats[livello]["sbagliate"] += 1
                self.vite -= 1
                self.blocco_corrente.clear()
                for _ in range(3):
                    self.coda_rinforzo.append((self.a, self.b))
        else:
            self.corretto = False
            self.stats[livello]["sbagliate"] += 1
            self.vite -= 1
            self.blocco_corrente.clear()
            for _ in range(3):
                self.coda_rinforzo.append((self.a, self.b))

        if self.vite <= 0:
            self.game_over = True

        self.blocco_corrente.append((self.corretto, tempo))
        self.stats[livello]["tempi"].append(tempo)
        self.domanda_attiva = False
        self.feedback = self.corretto
        self.feedback_timer = pygame.time.get_ticks()

        if self.corretto:
            richieste = 5 + sum(range(1, self.livello + 1))
            ultimi = self.blocco_corrente[-richieste:]
            corrette_blocco = sum(1 for esito, _ in ultimi if esito)
            tempi_blocco = [t for _, t in ultimi]
            if (
                corrette_blocco == richieste
                and sum(tempi_blocco) / richieste < 5
                and self.livello < len(LIVELLI) - 1
            ):
                self.livello += 1
                self.blocco_corrente.clear()
                self.coda_rinforzo.clear()

    def gestisci_timeout(self):
        if self.timeout_gestito:
            return
        self.timeout_gestito = True
        tempo = TEMPO_LIMITE
        self.tempi_risposta.append(tempo)
        livello = self.livello
        self.stats.setdefault(livello, {"corrette": 0, "sbagliate": 0, "tempi": []})
        self.stats[livello]["sbagliate"] += 1
        self.stats[livello]["tempi"].append(tempo)
        self.vite -= 1
        self.blocco_corrente.clear()
        for _ in range(3):
            self.coda_rinforzo.append((self.a, self.b))
        self.corretto = False
        self.domanda_attiva = False
        self.feedback = False
        self.feedback_timer = pygame.time.get_ticks()
        self.mostro_colpito = True
        if self.vite <= 0:
            self.game_over = True

    def aggiorna(self):
        if self.state == "gameover":
            return
        if self.state != "gioco":
            return

        if self.domanda_attiva:
            elapsed = (pygame.time.get_ticks() - self.inizio_domanda) / 1000.0
            self.mostro_progresso = min(elapsed / TEMPO_LIMITE, 1.0)
            self.mostro_x = (SCREEN_WIDTH - 150) - self.mostro_progresso * (SCREEN_WIDTH - 250)

            if self.mostro_progresso >= 1.0:
                self.gestisci_timeout()
        else:
            if self.feedback is not None and pygame.time.get_ticks() - self.feedback_timer > 1500:
                if self.game_over:
                    self.state = "gameover"
                else:
                    self.nuova_domanda()

    def disegna(self):
        self.screen.blit(self.bg, (0, 0))

        if self.state == "menu":
            self.disegna_menu()
        elif self.state == "gioco":
            if self.game_over:
                self.disegna_gameover()
            else:
                self.disegna_gioco()
        elif self.state == "gameover":
            self.disegna_gameover()

        pygame.display.flip()

    def disegna_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BG_DARK)
        self.screen.blit(overlay, (0, 0))

        titolo = self.font_titolo.render("MATH WIZARD", True, GOLD)
        rect = titolo.get_rect(center=(SCREEN_WIDTH // 2, 160))
        self.screen.blit(titolo, rect)

        sottotitolo = self.font_medio.render("Impara le tabelline divertendoti!", True, WHITE)
        rect = sottotitolo.get_rect(center=(SCREEN_WIDTH // 2, 230))
        self.screen.blit(sottotitolo, rect)

        righe = [
            "Rispondi correttamente alle moltiplicazioni",
            "Il mostro si avvicina mentre pensi!",
            f"Hai {TEMPO_LIMITE} secondi per ogni risposta",
            f"{VITE_MAGO} vite a disposizione per arrivare al livello 10"
        ]
        y = 310
        for riga in righe:
            surf = self.font_piccolo.render(riga, True, (200, 200, 200))
            rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(surf, rect)
            y += 40

        start = self.font_grande.render("Premi INVIO per iniziare", True, GREEN)
        rect = start.get_rect(center=(SCREEN_WIDTH // 2, 520))
        pulse = abs(pygame.time.get_ticks() % 1000 - 500) / 500
        start.set_alpha(int(128 + 127 * pulse))
        self.screen.blit(start, rect)

        esci = self.font_piccolo.render("ESC per uscire", True, GRAY)
        rect = esci.get_rect(center=(SCREEN_WIDTH // 2, 600))
        self.screen.blit(esci, rect)

    def disegna_gioco(self):
        wx = 80
        wy = SCREEN_HEIGHT // 2 - self.char_h // 2 + 120
        self.screen.blit(self.char_img, (wx, wy))
        self.screen.blit(self.monster_img, (self.mostro_x, wy + 20))

        domanda = self.font_grande.render(f"{self.a}  x  {self.b}  =  ?", True, WHITE)
        rect = domanda.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(domanda, rect)

        if self.domanda_attiva:
            testo_input = self.input_utente + ("|" if pygame.time.get_ticks() % 1000 < 500 else " ")
            input_surf = self.font_input.render(testo_input, True, WHITE)
            input_rect = input_surf.get_rect(center=(SCREEN_WIDTH // 2, 155))
            box_rect = input_rect.inflate(40, 16)
            box_rect.width = max(box_rect.width, 120)
            pygame.draw.rect(self.screen, (40, 40, 60), box_rect, border_radius=8)
            pygame.draw.rect(self.screen, (100, 100, 180), box_rect, 2, border_radius=8)
            self.screen.blit(input_surf, input_rect)

            if self.input_utente:
                preview = self.font_piccolo.render(f"INVIO per confermare", True, GRAY)
                rect = preview.get_rect(center=(SCREEN_WIDTH // 2, 200))
                self.screen.blit(preview, rect)

        richieste = 5 + sum(range(1, self.livello + 1))
        corr = sum(1 for esito, _ in self.blocco_corrente if esito)
        stato = self.font_piccolo.render(f"Livello {self.livello + 1}/{len(LIVELLI)} - {corr}/{richieste} corrette", True, WHITE)
        self.screen.blit(stato, (20, 20))

        for i in range(VITE_MAGO):
            colore = RED if i < self.vite else DARK
            pygame.draw.rect(self.screen, colore, (SCREEN_WIDTH - 70 - i * 50, 25, 35, 30), border_radius=4)
            if i < self.vite:
                pygame.draw.rect(self.screen, (255, 100, 100), (SCREEN_WIDTH - 70 - i * 50 + 3, 28, 29, 24), border_radius=3)
            pygame.draw.rect(self.screen, (200, 200, 200) if i < self.vite else (60, 60, 60),
                           (SCREEN_WIDTH - 70 - i * 50, 25, 35, 30), 2, border_radius=4)

        if self.domanda_attiva:
            bar_w = 400
            bar_h = 16
            bar_x = (SCREEN_WIDTH - bar_w) // 2
            bar_y = SCREEN_HEIGHT - 45
            pygame.draw.rect(self.screen, (60, 60, 80), (bar_x, bar_y, bar_w, bar_h), border_radius=8)
            rimanente = 1.0 - self.mostro_progresso
            if rimanente > 0.4:
                col_bar = (0, 200, 80)
            elif rimanente > 0.2:
                col_bar = (220, 200, 0)
            else:
                col_bar = (220, 50, 50)
            if rimanente > 0:
                w = int(bar_w * rimanente)
                if w > 0:
                    pygame.draw.rect(self.screen, col_bar, (bar_x, bar_y, w, bar_h), border_radius=8)

            tempo_testo = self.font_piccolo.render(f"{TEMPO_LIMITE * (1 - self.mostro_progresso):.0f}s", True, WHITE)
            rect = tempo_testo.get_rect(midleft=(bar_x + bar_w + 15, bar_y + bar_h // 2))
            self.screen.blit(tempo_testo, rect)

        if not self.domanda_attiva and self.feedback is not None:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(80)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))

            if self.feedback:
                fb = self.font_grande.render("CORRETTO!", True, GREEN)
            else:
                fb = self.font_grande.render(f"SBAGLIATO! Era {self.risultato_atteso}", True, RED)
            rect = fb.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
            self.screen.blit(fb, rect)

            prossimo = self.font_piccolo.render("Prossima domanda...", True, GRAY)
            rect = prossimo.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            self.screen.blit(prossimo, rect)

    def disegna_gameover(self):
        self.screen.blit(self.bg, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BG_DARK)
        self.screen.blit(overlay, (0, 0))

        if self.vite <= 0:
            titolo = self.font_titolo.render("GAME OVER", True, RED)
        else:
            titolo = self.font_titolo.render("PARTITA TERMINATA", True, GOLD)
        rect = titolo.get_rect(center=(SCREEN_WIDTH // 2, 60))
        self.screen.blit(titolo, rect)

        tot_corrette = sum(v["corrette"] for v in self.stats.values())
        tot_sbagliate = sum(v["sbagliate"] for v in self.stats.values())
        tempo_medio = sum(self.tempi_risposta) / len(self.tempi_risposta) if self.tempi_risposta else 0

        righe = [
            (f"Corrette: {tot_corrette}", GREEN),
            (f"Sbagliate: {tot_sbagliate}", RED),
            (f"Vite rimaste: {self.vite}", YELLOW),
            (f"Livello raggiunto: {self.livello + 1}/{len(LIVELLI)}", WHITE),
            (f"Tempo medio: {tempo_medio:.1f}s", WHITE),
        ]
        y = 130
        for testo, colore in righe:
            surf = self.font_medio.render(testo, True, colore)
            rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(surf, rect)
            y += 50

        if self.stats:
            y += 10
            titolo_stat = self.font_medio.render("Statistiche per livello:", True, GOLD)
            rect = titolo_stat.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(titolo_stat, rect)
            y += 42

            for i in sorted(self.stats.keys()):
                entry = self.stats[i]
                media = sum(entry['tempi']) / len(entry['tempi']) if entry['tempi'] else 0
                testo = f"Livello {i + 1}: {entry['corrette']} corrette / {entry['sbagliate']} sbagliate - Tempo medio: {media:.1f}s"
                surf = self.font_stats.render(testo, True, (200, 200, 200))
                rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y))
                self.screen.blit(surf, rect)
                y += 30

        y = max(y + 30, SCREEN_HEIGHT - 120)
        restart = self.font_medio.render("Premi R per rigiocare  |  M per menu  |  ESC per uscire", True, WHITE)
        rect = restart.get_rect(center=(SCREEN_WIDTH // 2, y))
        self.screen.blit(restart, rect)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.gestisci_input(event)

            self.aggiorna()
            self.disegna()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    g = Gioco()
    g.run()
