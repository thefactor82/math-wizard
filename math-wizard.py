import pygame
import random
import sys
import os
from datetime import datetime
from collections import deque

SESSIONS_FILE = "sessions.txt"

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
    if reinforce_queue and random.random() < 0.4:
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
        self.debug = False
        self.debug_buf = ""

        self.font_titolo = pygame.font.Font(None, 80)
        self.font_grande = pygame.font.Font(None, 64)
        self.font_medio = pygame.font.Font(None, 42)
        self.font_piccolo = pygame.font.Font(None, 30)
        self.font_input = pygame.font.Font(None, 56)
        self.font_stats = pygame.font.Font(None, 28)
        self.font_num = pygame.font.Font(None, 36)
        self.font_tiny = pygame.font.Font(None, 22)

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
        self.modalita = "auto"
        self.pool_a = list(range(0, 10))
        self.pool_b = list(range(0, 10))
        self.domande_totali = 10
        self.domande_fatte = 0
        self.vite = VITE_MAGO
        self.livello = 0
        self.corretto = 0
        self.a = 0
        self.b = 0
        self.prev_a = -1
        self.prev_b = -1
        self.risultato_atteso = 0
        self.input_utente = ""
        self.mostro_progresso = 0.0
        self.mostro_x = SCREEN_WIDTH - 150
        self.mostro_colpito = False
        self.hit_timer = 0
        self.domanda_attiva = False
        self.feedback = None
        self.feedback_timer = 0
        self.attendi_invio = False
        self.zap_timer = 0
        self.game_over = False
        self.inizio_domanda = 0
        self.timeout_gestito = False

        self.config_cursor_row = 0
        self.config_cursor_col = 0
        self.config_pool_a = [n in self.pool_a for n in range(13)]
        self.config_pool_b = [n in self.pool_b for n in range(13)]
        self.config_domande = 10
        self.config_swap = True

        self.tempi_risposta = []
        self.blocco_corrente = []
        self.coda_rinforzo = deque()
        self.stats = {}

    def mostra_config(self):
        self.state = "config_fisso"

    def avvia_partita(self):
        self.state = "gioco"
        self.game_over = False
        self.vite = VITE_MAGO
        self.livello = 0
        self.tempi_risposta = []
        self.blocco_corrente = []
        self.coda_rinforzo = deque()
        self.stats = {}
        self.domande_fatte = 0
        self.domanda_attiva = False
        self.feedback = None
        self.attendi_invio = False
        self.prev_a = -1
        self.prev_b = -1
        self.game_over = False
        if self.modalita == "fisso":
            self.pool_a = [n for n in range(13) if self.config_pool_a[n]]
            self.pool_b = [n for n in range(13) if self.config_pool_b[n]]
            if not self.pool_a:
                self.pool_a = [0]
            if not self.pool_b:
                self.pool_b = [0]
            self.domande_totali = self.config_domande
            self.swap_operandi = self.config_swap
        self.nuova_domanda()

    def nuova_domanda(self):
        if self.vite <= 0:
            return
        if self.modalita == "auto":
            pool = get_pool(self.livello)
            self.a, self.b = genera_operandi(pool, self.livello, self.coda_rinforzo)
        else:
            if self.domande_fatte >= self.domande_totali:
                self.game_over = True
                return
            if self.coda_rinforzo and random.random() < 0.4:
                self.a, self.b = self.coda_rinforzo.popleft()
            else:
                self.a = random.choice(self.pool_a)
                self.b = random.choice(self.pool_b)
            if self.swap_operandi and random.random() < 0.5:
                self.a, self.b = self.b, self.a
            self.domande_fatte += 1

        if (self.a, self.b) == (self.prev_a, self.prev_b):
            if self.a == self.b:
                pool = get_pool(self.livello) if self.modalita == "auto" else self.pool_a
                candidates = [n for n in pool if n != self.a]
                if candidates:
                    self.a = random.choice(candidates)
                    self.b = random.choice(pool)
            else:
                self.a, self.b = self.b, self.a
        self.prev_a, self.prev_b = self.a, self.b

        self.risultato_atteso = self.a * self.b
        self.input_utente = ""
        self.mostro_progresso = 0.0
        self.mostro_colpito = False
        self.domanda_attiva = True
        self.feedback = None
        self.feedback_timer = 0
        self.zap_timer = 0
        self.attendi_invio = False
        self.timeout_gestito = False
        self.inizio_domanda = pygame.time.get_ticks()

        if self.modalita == "auto":
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
            if event.unicode and event.unicode.isalpha():
                self.debug_buf = (self.debug_buf + event.unicode.lower())[-5:]
                if self.debug_buf == "debug":
                    self.debug = not self.debug
                    self.debug_buf = ""
            if self.state == "menu":
                if event.key == pygame.K_1:
                    self.modalita = "auto"
                    self.avvia_partita()
                elif event.key == pygame.K_2:
                    self.modalita = "fisso"
                    self.mostra_config()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
            elif self.state == "config_fisso":
                self.gestisci_config(event)
            elif self.state == "gioco":
                if event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                elif self.attendi_invio and event.key == pygame.K_RETURN:
                    if self.game_over:
                        self.salva_sessione()
                        self.state = "gameover"
                    else:
                        self.nuova_domanda()
                elif self.domanda_attiva:
                    if event.key == pygame.K_RETURN and self.input_utente:
                        self.controlla_risposta()
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_utente = self.input_utente[:-1]
                    elif event.unicode.isdigit() and len(self.input_utente) < 6:
                        self.input_utente += event.unicode
            elif self.state == "gameover":
                if event.key == pygame.K_r:
                    self.avvia_partita()
                elif event.key == pygame.K_m:
                    self.state = "menu"
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

    def gestisci_config(self, event):
        if event.key == pygame.K_ESCAPE:
            self.state = "menu"
            return
        if event.key == pygame.K_RETURN:
            self.avvia_partita()
            return

        max_col = 12 if self.config_cursor_row in (0, 1) else 0
        if event.key == pygame.K_UP:
            self.config_cursor_row = max(0, self.config_cursor_row - 1)
            self.config_cursor_col = min(self.config_cursor_col, 12 if self.config_cursor_row in (0, 1) else 0)
        elif event.key == pygame.K_DOWN:
            self.config_cursor_row = min(4, self.config_cursor_row + 1)
            self.config_cursor_col = min(self.config_cursor_col, 12 if self.config_cursor_row in (0, 1) else 0)
        elif event.key == pygame.K_LEFT:
            self.config_cursor_col = max(0, self.config_cursor_col - 1)
        elif event.key == pygame.K_RIGHT:
            self.config_cursor_col = min(max_col, self.config_cursor_col + 1)
        elif event.key == pygame.K_SPACE:
            if self.config_cursor_row == 0:
                self.config_pool_a[self.config_cursor_col] = not self.config_pool_a[self.config_cursor_col]
                if not any(self.config_pool_a):
                    self.config_pool_a[self.config_cursor_col] = True
            elif self.config_cursor_row == 1:
                self.config_pool_b[self.config_cursor_col] = not self.config_pool_b[self.config_cursor_col]
                if not any(self.config_pool_b):
                    self.config_pool_b[self.config_cursor_col] = True
            elif self.config_cursor_row == 3:
                self.config_swap = not self.config_swap
        elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
            if self.config_cursor_row == 2:
                self.config_domande = min(99, self.config_domande + 1)
        elif event.key == pygame.K_MINUS:
            if self.config_cursor_row == 2:
                self.config_domande = max(1, self.config_domande - 1)

    def controlla_risposta(self):
        if not self.domanda_attiva:
            return

        tempo = min((pygame.time.get_ticks() - self.inizio_domanda) / 1000.0, TEMPO_LIMITE)
        self.tempi_risposta.append(tempo)

        livello = 0 if self.modalita == "fisso" else self.livello
        self.stats.setdefault(livello, {"corrette": 0, "sbagliate": 0, "tempi": []})

        if self.input_utente.strip().isdigit():
            risposta = int(self.input_utente)
            if risposta == self.risultato_atteso:
                self.corretto = True
                self.stats[livello]["corrette"] += 1
                self.mostro_colpito = True
                self.zap_timer = 12
            else:
                self.corretto = False
                self.stats[livello]["sbagliate"] += 1
                self.vite -= 1
                self.blocco_corrente.clear()
                for _ in range(3):
                    self.coda_rinforzo.append((self.a, self.b))
                self.hit_timer = 12
        else:
            self.corretto = False
            self.stats[livello]["sbagliate"] += 1
            self.vite -= 1
            self.blocco_corrente.clear()
            for _ in range(3):
                self.coda_rinforzo.append((self.a, self.b))
            self.hit_timer = 12

        if self.vite <= 0:
            self.game_over = True

        self.blocco_corrente.append((self.corretto, tempo))
        self.stats[livello]["tempi"].append(tempo)
        self.domanda_attiva = False
        self.feedback = self.corretto
        self.feedback_timer = pygame.time.get_ticks()
        if not self.corretto:
            self.attendi_invio = True

        if self.modalita == "auto" and self.corretto:
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
        livello = 0 if self.modalita == "fisso" else self.livello
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
        self.attendi_invio = True
        self.mostro_colpito = True
        self.hit_timer = 12
        if self.vite <= 0:
            self.game_over = True

    def aggiorna(self):
        if self.zap_timer > 0:
            self.zap_timer -= 1
        if self.hit_timer > 0:
            self.hit_timer -= 1
        if self.state == "gameover":
            return
        if self.state not in ("gioco",):
            return

        if self.domanda_attiva:
            elapsed = (pygame.time.get_ticks() - self.inizio_domanda) / 1000.0
            self.mostro_progresso = min(elapsed / TEMPO_LIMITE, 1.0)
            self.mostro_x = (SCREEN_WIDTH - 150) - self.mostro_progresso * (SCREEN_WIDTH - 250)

            if self.mostro_progresso >= 1.0:
                self.gestisci_timeout()
        else:
            if self.attendi_invio:
                return
            if self.feedback is not None and pygame.time.get_ticks() - self.feedback_timer > 1500:
                if self.game_over:
                    self.salva_sessione()
                    self.state = "gameover"
                else:
                    self.nuova_domanda()

    def disegna(self):
        if self.state == "gioco" and not self.game_over:
            self.disegna_gioco()
        else:
            self.screen.blit(self.bg, (0, 0))
            if self.state == "menu":
                self.disegna_menu()
            elif self.state == "config_fisso":
                self.disegna_config()
            elif self.state in ("gioco", "gameover"):
                self.disegna_gameover()

        pygame.display.flip()

    def disegna_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BG_DARK)
        self.screen.blit(overlay, (0, 0))

        titolo = self.font_titolo.render("MATH WIZARD", True, GOLD)
        rect = titolo.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(titolo, rect)

        sottotitolo = self.font_medio.render("Impara le tabelline divertendoti!", True, WHITE)
        rect = sottotitolo.get_rect(center=(SCREEN_WIDTH // 2, 160))
        self.screen.blit(sottotitolo, rect)

        y = 280
        opt1 = self.font_grande.render("1  Autoapprendimento", True, WHITE)
        rect = opt1.get_rect(midleft=(SCREEN_WIDTH // 2 - 300, y))
        self.screen.blit(opt1, rect)
        desc1 = self.font_piccolo.render("Livelli progressivi automatici, operandi 0-12, level-up basato su precisione e velocita", True, GRAY)
        rect = desc1.get_rect(midleft=(SCREEN_WIDTH // 2 - 300, y + 40))
        self.screen.blit(desc1, rect)

        y = 380
        opt2 = self.font_grande.render("2  Livello Fisso", True, WHITE)
        rect = opt2.get_rect(midleft=(SCREEN_WIDTH // 2 - 300, y))
        self.screen.blit(opt2, rect)
        desc2 = self.font_piccolo.render("Scegli operandi, numero domande e sfida a difficolta costante", True, GRAY)
        rect = desc2.get_rect(midleft=(SCREEN_WIDTH // 2 - 300, y + 40))
        self.screen.blit(desc2, rect)

        info = self.font_piccolo.render("Premi 1 o 2 per selezionare  |  ESC per uscire", True, WHITE)
        rect = info.get_rect(center=(SCREEN_WIDTH // 2, 550))
        self.screen.blit(info, rect)

    def disegna_config(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BG_DARK)
        self.screen.blit(overlay, (0, 0))

        titolo = self.font_titolo.render("LIVELLO FISSO", True, GOLD)
        rect = titolo.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(titolo, rect)

        labels = ["Operando A", "Operando B"]
        pools = [self.config_pool_a, self.config_pool_b]

        for row in range(2):
            y = 140 + row * 100
            label = self.font_medio.render(labels[row], True, WHITE)
            rect = label.get_rect(midleft=(80, y + 20))
            self.screen.blit(label, rect)

            for col in range(13):
                sx = 280 + col * 68
                selected = pools[row][col]
                focused = self.config_cursor_row == row and self.config_cursor_col == col
                bg_col = (60, 130, 60) if selected else (60, 60, 70)
                if focused:
                    pygame.draw.rect(self.screen, (255, 255, 100), (sx - 2, y - 2, 58, 38), 3, border_radius=4)
                pygame.draw.rect(self.screen, bg_col, (sx, y, 54, 34), border_radius=4)
                num = self.font_num.render(str(col), True, WHITE)
                rect_n = num.get_rect(center=(sx + 27, y + 17))
                self.screen.blit(num, rect_n)

        y = 360
        label_q = self.font_medio.render("Domande", True, WHITE)
        rect = label_q.get_rect(midleft=(80, y + 20))
        self.screen.blit(label_q, rect)

        focused = self.config_cursor_row == 2
        qx = 280
        if focused:
            pygame.draw.rect(self.screen, (255, 255, 100), (qx - 2, y - 2, 90, 38), 3, border_radius=4)
        pygame.draw.rect(self.screen, (60, 60, 70), (qx, y, 86, 34), border_radius=4)
        q_surf = self.font_grande.render(str(self.config_domande), True, WHITE)
        rect_q = q_surf.get_rect(center=(qx + 43, y + 17))
        self.screen.blit(q_surf, rect_q)
        hint = self.font_piccolo.render("+ / -", True, GRAY)
        rect_h = hint.get_rect(midleft=(qx + 100, y + 17))
        self.screen.blit(hint, rect_h)

        y = 450
        swap_sel = self.config_cursor_row == 3
        if swap_sel:
            pygame.draw.rect(self.screen, (255, 255, 100), (270, y - 4, 190, 44), 3, border_radius=6)
        bg_swap = (60, 130, 60) if self.config_swap else (60, 60, 70)
        pygame.draw.rect(self.screen, bg_swap, (272, y, 186, 36), border_radius=6)
        sw_txt = "ON" if self.config_swap else "OFF"
        swap_label = self.font_medio.render("Commuta A/B", True, WHITE)
        rect_sl = swap_label.get_rect(midleft=(80, y + 18))
        self.screen.blit(swap_label, rect_sl)
        swap_val = self.font_medio.render(sw_txt, True, WHITE)
        rect_sv = swap_val.get_rect(center=(365, y + 18))
        self.screen.blit(swap_val, rect_sv)

        y = 510
        start_sel = self.config_cursor_row == 4
        if start_sel:
            pygame.draw.rect(self.screen, (255, 255, 100), (SCREEN_WIDTH // 2 - 112, y - 4, 224, 54), 3, border_radius=8)
        pygame.draw.rect(self.screen, (40, 120, 40), (SCREEN_WIDTH // 2 - 110, y, 220, 46), border_radius=8)
        start_txt = self.font_medio.render("INIZIA", True, WHITE)
        rect_s = start_txt.get_rect(center=(SCREEN_WIDTH // 2, y + 23))
        self.screen.blit(start_txt, rect_s)

        help = self.font_piccolo.render("Freccette: naviga  |  SPACE: attiva/disattiva  |  INVIO: conferma  |  ESC: indietro", True, GRAY)
        rect_h2 = help.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        self.screen.blit(help, rect_h2)

    def disegna_gioco(self):
        shake = (0, 0)
        if self.hit_timer > 0:
            shake = (random.randint(-4, 4), random.randint(-3, 3))
            self.screen.blit(self.bg, shake)
        else:
            self.screen.blit(self.bg, (0, 0))

        wx = 80 + shake[0]
        wy = SCREEN_HEIGHT // 2 - self.char_h // 2 + 120 + shake[1]
        self.screen.blit(self.char_img, (wx, wy))
        self.screen.blit(self.monster_img, (self.mostro_x + shake[0], wy + 50))

        if self.zap_timer > 0:
            start_x, start_y = 80 + 80, wy + self.char_h // 2
            end_x, end_y = self.mostro_x + 100, wy + 50 + self.char_h // 2
            mid_x = (start_x + end_x) // 2
            segments = 8
            for offset in range(-4, 5, 2):
                points = [(start_x, start_y)]
                for i in range(1, segments):
                    t = i / segments
                    x = start_x + (end_x - start_x) * t + random.randint(-30, 30)
                    y = start_y + (end_y - start_y) * t + random.randint(-40, 40) + offset * 3
                    points.append((x, y))
                points.append((end_x, end_y))
                width = 3 if abs(offset) <= 2 else 1
                alpha = max(100, 255 - abs(offset) * 40)
                col = (255, 255, int(255 * self.zap_timer / 12)) if abs(offset) <= 2 else (100, 100, 255)
                pygame.draw.lines(self.screen, col, False, points, width)

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

        if self.modalita == "auto":
            richieste = 5 + sum(range(1, self.livello + 1))
            corr = sum(1 for esito, _ in self.blocco_corrente if esito)
            stato = self.font_piccolo.render(f"Livello {self.livello + 1}/{len(LIVELLI)} - {corr}/{richieste} corrette", True, WHITE)
            self.screen.blit(stato, (20, 20))
            mode_txt = "Autoapprendimento"
        else:
            stato = self.font_piccolo.render(f"Domanda {self.domande_fatte}/{self.domande_totali}", True, WHITE)
            self.screen.blit(stato, (20, 20))
            mode_txt = "Livello Fisso"
        mode = self.font_piccolo.render(mode_txt, True, GRAY)
        rect_m = mode.get_rect(midright=(SCREEN_WIDTH - 20, 20))
        self.screen.blit(mode, rect_m)

        for i in range(VITE_MAGO):
            colore = RED if i < self.vite else DARK
            pygame.draw.rect(self.screen, colore, (SCREEN_WIDTH - 70 - i * 50, 30, 35, 30), border_radius=4)
            if i < self.vite:
                pygame.draw.rect(self.screen, (255, 100, 100), (SCREEN_WIDTH - 70 - i * 50 + 3, 33, 29, 24), border_radius=3)
            pygame.draw.rect(self.screen, (200, 200, 200) if i < self.vite else (60, 60, 60),
                           (SCREEN_WIDTH - 70 - i * 50, 30, 35, 30), 2, border_radius=4)

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
                prossimo = self.font_piccolo.render("Prossima domanda...", True, GRAY)
            else:
                fb = self.font_grande.render(f"SBAGLIATO! Era {self.risultato_atteso}", True, RED)
                prossimo = self.font_piccolo.render("Premi INVIO per continuare", True, GRAY)
            rect = fb.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
            self.screen.blit(fb, rect)
            rect = prossimo.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            self.screen.blit(prossimo, rect)

        if self.hit_timer > 0:
            alpha = int(120 * self.hit_timer / 12)
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash.set_alpha(alpha)
            flash.fill(RED)
            self.screen.blit(flash, (0, 0))

        if self.debug:
            label = self.font_stats.render("DEBUG ON", True, (0, 255, 255))
            rect = label.get_rect(bottomright=(SCREEN_WIDTH - 15, SCREEN_HEIGHT - 15))
            bg_l = rect.inflate(8, 4)
            pygame.draw.rect(self.screen, (10, 10, 20), bg_l)
            pygame.draw.rect(self.screen, (0, 255, 255), bg_l, 1)
            self.screen.blit(label, rect)
            dx, dy = 20, 80
            lines = [
                "DEBUG",
                f"Stato: {self.state}",
                f"Modalita: {self.modalita}",
                f"Domanda attiva: {self.domanda_attiva}",
                f"Feedback: {self.feedback}",
                f"Attendi invio: {self.attendi_invio}",
                f"Game over: {self.game_over}",
                f"Lives: {self.vite}",
                f"Livello: {self.livello + 1 if self.modalita == 'auto' else '-'}",
                f"Operandi: {self.a} x {self.b}",
                f"Prev: {self.prev_a} x {self.prev_b}",
                f"Risultato: {self.risultato_atteso}",
                f"Pool A: {get_pool(self.livello) if self.modalita == 'auto' else self.pool_a}",
                f"Pool B: {get_pool(self.livello) if self.modalita == 'auto' else self.pool_b}",
                f"Coda rinforzo: {list(self.coda_rinforzo)}",
                f"Progresso mostro: {self.mostro_progresso:.2f}" + (f"  Tempo: {(pygame.time.get_ticks() - self.inizio_domanda)/1000:.1f}s" if self.domanda_attiva else ""),
            ]
            bg = pygame.Surface((380, len(lines) * 22 + 10))
            bg.set_alpha(200)
            bg.fill((10, 10, 20))
            self.screen.blit(bg, (dx - 5, dy - 5))
            for line in lines:
                surf = self.font_stats.render(line, True, (0, 255, 255))
                rect = surf.get_rect(topleft=(dx, dy))
                self.screen.blit(surf, rect)
                dy += 22

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
        rect = titolo.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(titolo, rect)

        tot_corrette = sum(v["corrette"] for v in self.stats.values())
        tot_sbagliate = sum(v["sbagliate"] for v in self.stats.values())
        tempo_medio = sum(self.tempi_risposta) / len(self.tempi_risposta) if self.tempi_risposta else 0

        righe = [
            (f"Corrette: {tot_corrette}", GREEN),
            (f"Sbagliate: {tot_sbagliate}", RED),
            (f"Vite rimaste: {self.vite}", YELLOW),
            (f"Tempo medio: {tempo_medio:.1f}s", WHITE),
        ]
        if self.modalita == "auto":
            righe.insert(2, (f"Livello raggiunto: {self.livello + 1}/{len(LIVELLI)}", WHITE))
        y = 110
        for testo, colore in righe:
            surf = self.font_medio.render(testo, True, colore)
            rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(surf, rect)
            y += 46

        sessioni = self.carica_sessioni()
        if sessioni:
            y += 14
            titolo_sess = self.font_medio.render("Ultime sessioni:", True, GOLD)
            rect = titolo_sess.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(titolo_sess, rect)
            y += 34
            for s in sessioni:
                surf = self.font_tiny.render(s, True, (180, 180, 180))
                rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y))
                self.screen.blit(surf, rect)
                y += 24

        y = max(y + 20, SCREEN_HEIGHT - 100)
        restart = self.font_medio.render("Premi R per rigiocare  |  M per menu  |  ESC per uscire", True, WHITE)
        rect = restart.get_rect(center=(SCREEN_WIDTH // 2, y))
        self.screen.blit(restart, rect)

    def salva_sessione(self):
        tot_corrette = sum(v["corrette"] for v in self.stats.values())
        tot_sbagliate = sum(v["sbagliate"] for v in self.stats.values())
        tempo_medio = sum(self.tempi_risposta) / len(self.tempi_risposta) if self.tempi_risposta else 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        if self.modalita == "auto":
            riga = f"{now} | Autoapprendimento | Corrette: {tot_corrette} | Sbagliate: {tot_sbagliate} | Livello: {self.livello + 1}/{len(LIVELLI)} | Tempo medio: {tempo_medio:.1f}s"
        else:
            pool_a_txt = ",".join(str(n) for n in self.pool_a)
            pool_b_txt = ",".join(str(n) for n in self.pool_b)
            riga = f"{now} | Livello Fisso | Corrette: {tot_corrette} | Sbagliate: {tot_sbagliate} | Pool A: [{pool_a_txt}] | Pool B: [{pool_b_txt}] | Domande: {self.domande_fatte}/{self.domande_totali} | Tempo medio: {tempo_medio:.1f}s"
        with open(SESSIONS_FILE, "a", encoding="utf-8") as f:
            f.write(riga + "\n")

    def carica_sessioni(self):
        if not os.path.exists(SESSIONS_FILE):
            return []
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            righe = f.readlines()
        ultime = [r.strip() for r in righe if r.strip()]
        return list(reversed(ultime[-6:]))

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
