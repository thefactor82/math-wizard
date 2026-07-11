import pygame
import random
import sys
import os
import json
from datetime import datetime
from collections import deque

PROFILES_DIR = "profiles"

VITE_MAGO = 3
TEMPO_LIMITE_DEFAULT = 12
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
        pygame.display.set_caption("Math Wizard - Impara la matematica")
        self.imposta_cursore()
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "splash"
        self.splash_start = pygame.time.get_ticks()
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
        self.gestione_profili()
        self.azzera_partita()

    def imposta_cursore(self):
        try:
            import struct, io, os
            path = os.path.join("graphics", "misc", "wand.cur")
            if not os.path.exists(path):
                return
            with open(path, "rb") as f:
                data = f.read()
            _, _, count = struct.unpack("<HHH", data[:6])
            # Pick the best entry: prefer 32x32, fallback to largest
            best = None
            for i in range(count):
                w, h, _, _, _, _, sz, off = struct.unpack("<BBBBHHII", data[6 + i * 16 : 22 + i * 16])
                if w == 32:
                    best = (off, sz, w, h)
                    break
                if best is None or w > best[2]:
                    best = (off, sz, w, h)
            if best is None:
                return
            off, sz, w, h = best
            buf = io.BytesIO(data[off : off + sz])
            surf = pygame.image.load(buf)
            if not (surf.get_flags() & pygame.SRCALPHA):
                surf = surf.convert_alpha()
            surf = pygame.transform.scale_by(surf, 3)
            cursor = pygame.cursors.Cursor((0, 0), surf)
            pygame.mouse.set_cursor(cursor)
        except Exception:
            pass

    def aggiorna_char_img(self):
        self.char_img = self.char_imgs.get(self.config_genere, self.char_imgs["F"])
        self.char_h = self.char_img.get_height()

    def carica_risorse(self):
        bg = pygame.image.load("graphics/backgrounds/background.png")
        self.bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

        pw, ph = 900, 1330
        self.char_imgs = {
            "F": pygame.transform.scale(pygame.image.load("graphics/players/playerf.png").convert_alpha(), (160, int(160 / pw * ph))),
            "M": pygame.transform.scale(pygame.image.load("graphics/players/playerm.png").convert_alpha(), (160, int(160 / pw * ph))),
        }
        self.char_img = self.char_imgs["F"]
        self.char_h = self.char_img.get_height()

        mw, mh = 1500, 1619
        self.monster_imgs = []
        for i in range(2, 5):
            img = pygame.image.load(f"graphics/monsters/monster{i}.png").convert_alpha()
            flipped = pygame.transform.flip(img, True, False)
            self.monster_imgs.append(pygame.transform.scale(flipped, (200, int(200 / mw * mh))))
        self.monster_img = self.monster_imgs[0]

        self.heart_red = pygame.transform.scale(pygame.image.load("graphics/misc/lives.png").convert_alpha(), (35, 35))
        self.heart_grey = pygame.transform.scale(pygame.image.load("graphics/misc/lives_lost.png").convert_alpha(), (35, 35))

        self.logo = pygame.transform.scale(pygame.image.load("graphics/misc/logo.png").convert_alpha(), (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.gear_img = pygame.image.load("graphics/misc/gear.png").convert_alpha()

    def gestione_profili(self):
        os.makedirs(PROFILES_DIR, exist_ok=True)
        idx_file = os.path.join(PROFILES_DIR, "profiles.json")
        self.profilo_cursor = 0
        self.profilo_input = ""
        self.profilo_input_mode = False
        self.profilo_genere_mode = False
        self.profilo_nuovo_nome = ""
        self.config_operazione = "moltiplicazione"
        self.config_somma_massima = 10
        self.config_pool_a = [n < 10 for n in range(100)]
        self.config_pool_b = [n < 10 for n in range(100)]
        self.config_domande = 10
        self.config_swap = True
        self.config_differenza_positiva = True
        self.config_timeout = TEMPO_LIMITE_DEFAULT
        self.config_genere = "F"

        self.version = "0.2.004"

        self.profili = []
        self.profilo_corrente = ""
        if os.path.exists(idx_file):
            try:
                with open(idx_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.profili = [p for p in data.get("profiles", [])
                                if os.path.isdir(os.path.join(PROFILES_DIR, p))]
                self.profilo_corrente = data.get("current", "")
                if self.profilo_corrente not in self.profili:
                    self.profilo_corrente = ""
            except (json.JSONDecodeError, Exception):
                self.profili = []
                self.profilo_corrente = ""
        if self.profilo_corrente in self.profili:
            self.carica_config_profilo(self.profilo_corrente)
            self.aggiorna_char_img()

    def salva_profili(self):
        path = os.path.join(PROFILES_DIR, "profiles.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"profiles": self.profili, "current": self.profilo_corrente}, f, indent=2)

    def salva_config_profilo(self, nome=None):
        nome = nome or self.profilo_corrente
        if not nome:
            return
        prof_dir = os.path.join(PROFILES_DIR, nome)
        os.makedirs(prof_dir, exist_ok=True)
        path = os.path.join(prof_dir, "config.json")
        data = {
            "operazione": self.config_operazione,
            "somma_massima": self.config_somma_massima,
            "pool_a": self.config_pool_a,
            "pool_b": self.config_pool_b,
            "domande": self.config_domande,
            "swap": self.config_swap,
            "differenza_positiva": self.config_differenza_positiva,
            "timeout": self.config_timeout,
            "genere": self.config_genere,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def carica_config_profilo(self, nome):
        path = os.path.join(PROFILES_DIR, nome, "config.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.config_operazione = data.get("operazione", self.config_operazione)
            self.config_somma_massima = data.get("somma_massima", self.config_somma_massima)
            self.config_pool_a = data.get("pool_a", self.config_pool_a)
            self.config_pool_b = data.get("pool_b", self.config_pool_b)
            self.config_domande = data.get("domande", self.config_domande)
            self.config_swap = data.get("swap", self.config_swap)
            self.config_differenza_positiva = data.get("differenza_positiva", self.config_differenza_positiva)
            self.config_timeout = data.get("timeout", self.config_timeout)
            self.config_genere = data.get("genere", self.config_genere)

    def percorso_sessioni(self):
        nome = self.profilo_corrente or "_fallback"
        prof_dir = os.path.join(PROFILES_DIR, nome)
        os.makedirs(prof_dir, exist_ok=True)
        return os.path.join(prof_dir, "sessions.txt")

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
        self.mostro_x = SCREEN_WIDTH + 30
        self.mostro_colpito = False
        self.mostro_fade_start = 0
        self.hit_timer = 0
        self.domanda_attiva = False
        self.feedback = None
        self.feedback_timer = 0
        self.zap_timer = 0
        self.game_over = False
        self.inizio_domanda = 0
        self.timeout_gestito = False

        self.menu_cursor = 0
        self.opzioni_cursor = 0

        self.config_operazione = "moltiplicazione"
        self.config_somma_massima = 10
        self.config_cursor_row = 0
        self.config_cursor_col = 0
        self.config_cursor_subrow = 0
        self.config_pool_a = [n < 10 for n in range(100)]
        self.config_pool_b = [n < 10 for n in range(100)]
        self.config_domande = 10
        self.config_swap = True
        self.config_differenza_positiva = True
        self.config_timeout = 12
        self.config_genere = "F"

        self.tempi_risposta = []
        self.blocco_corrente = []
        self.coda_rinforzo = deque()
        self.stats = {}

    def mostra_config(self):
        self.state = "config_fisso"
        self.config_cursor_row = 0
        self.config_cursor_col = 0
        self.config_cursor_subrow = 0

    def avvia_partita(self):
        self.state = "gioco"
        self.game_over = False
        self.vite = VITE_MAGO
        self.timeout_limite = self.config_timeout
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
            self.operazione = self.config_operazione
            self.somma_massima = self.config_somma_massima
            self.differenza_positiva = self.config_differenza_positiva
            pool_range = range(13) if self.config_operazione == "moltiplicazione" else range(100)
            self.pool_a = [n for n in pool_range if self.config_pool_a[n]]
            self.pool_b = [n for n in pool_range if self.config_pool_b[n]]
            if not self.pool_a:
                self.pool_a = [0]
            if not self.pool_b:
                self.pool_b = [0]
            self.domande_totali = self.config_domande
            self.swap_operandi = True if self.operazione == "sottrazione" else self.config_swap
        self.nuova_domanda()

    def nuova_domanda(self):
        if self.vite <= 0:
            return
        if self.modalita == "auto":
            pool = get_pool(self.livello)
            self.a, self.b = genera_operandi(pool, self.livello, self.coda_rinforzo)
        else:
            if self.domande_fatte >= self.domande_totali:
                self.salva_sessione()
                self.state = "gameover"
                return
            if self.coda_rinforzo and random.random() < 0.4:
                self.a, self.b = self.coda_rinforzo.popleft()
            else:
                self.a = random.choice(self.pool_a)
                self.b = random.choice(self.pool_b)
                if self.operazione == "addizione":
                    for _ in range(50):
                        if self.a + self.b <= self.somma_massima:
                            break
                        self.a = random.choice(self.pool_a)
                        self.b = random.choice(self.pool_b)
                    else:
                        self.a = min(self.pool_a, key=lambda x: abs(x - self.somma_massima))
                        self.b = 0
            if self.swap_operandi and random.random() < 0.5:
                self.a, self.b = self.b, self.a
            if self.operazione == "sottrazione" and self.differenza_positiva and self.a < self.b:
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

        if self.modalita == "fisso":
            if self.operazione == "addizione":
                self.risultato_atteso = self.a + self.b
            elif self.operazione == "sottrazione":
                self.risultato_atteso = self.a - self.b
            else:
                self.risultato_atteso = self.a * self.b
        else:
            self.risultato_atteso = self.a * self.b
        self.input_utente = ""
        self.mostro_progresso = 0.0
        self.mostro_x = SCREEN_WIDTH + 30
        self.mostro_colpito = False
        self.monster_img = random.choice(self.monster_imgs)
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
                self.imposta_cursore()
                return
            if event.unicode and event.unicode.isalpha():
                self.debug_buf = (self.debug_buf + event.unicode.lower())[-5:]
                if self.debug_buf == "debug":
                    self.debug = not self.debug
                    self.debug_buf = ""
            if self.state == "profile_select":
                if self.profilo_input_mode:
                    if self.profilo_genere_mode:
                        if event.key == pygame.K_ESCAPE:
                            self.profilo_genere_mode = False
                        elif event.key == pygame.K_f:
                            self.config_genere = "F"
                            nuovo = self.profilo_input.strip()
                            self.profili.append(nuovo)
                            self.salva_config_profilo(nuovo)
                            self.profilo_corrente = nuovo
                            self.aggiorna_char_img()
                            self.salva_profili()
                            self.profilo_input = ""
                            self.profilo_input_mode = False
                            self.profilo_genere_mode = False
                            self.state = "menu"
                        elif event.key == pygame.K_m:
                            self.config_genere = "M"
                            nuovo = self.profilo_input.strip()
                            self.profili.append(nuovo)
                            self.salva_config_profilo(nuovo)
                            self.profilo_corrente = nuovo
                            self.aggiorna_char_img()
                            self.salva_profili()
                            self.profilo_input = ""
                            self.profilo_input_mode = False
                            self.profilo_genere_mode = False
                            self.state = "menu"
                    else:
                        if event.key == pygame.K_ESCAPE:
                            self.profilo_input_mode = False
                            self.profilo_input = ""
                        elif event.key == pygame.K_RETURN and self.profilo_input.strip():
                            self.profilo_genere_mode = True
                        elif event.key == pygame.K_BACKSPACE:
                            self.profilo_input = self.profilo_input[:-1]
                        elif event.unicode and event.unicode.isprintable() and len(self.profilo_input) < 30:
                            self.profilo_input += event.unicode
                    return
                if event.key == pygame.K_UP:
                    self.profilo_cursor = (self.profilo_cursor - 1) % (len(self.profili) + 1)
                elif event.key == pygame.K_DOWN:
                    self.profilo_cursor = (self.profilo_cursor + 1) % (len(self.profili) + 1)
                elif event.key == pygame.K_RETURN:
                    if self.profilo_cursor < len(self.profili):
                        self.profilo_corrente = self.profili[self.profilo_cursor]
                        self.carica_config_profilo(self.profilo_corrente)
                        self.aggiorna_char_img()
                        self.salva_profili()
                        self.state = "menu"
                    else:
                        self.profilo_input_mode = True
                        self.profilo_input = ""
                elif event.key == pygame.K_ESCAPE:
                    if self.profili:
                        self.state = "menu"
                    else:
                        self.running = False
            elif self.state == "menu":
                if event.key == pygame.K_UP:
                    self.menu_cursor = 0
                elif event.key == pygame.K_DOWN:
                    self.menu_cursor = 1
                elif event.key == pygame.K_RETURN:
                    self.modalita = "auto" if self.menu_cursor == 0 else "fisso"
                    self.avvia_partita()
                elif event.key == pygame.K_1:
                    self.modalita = "auto"
                    self.avvia_partita()
                elif event.key == pygame.K_2:
                    self.modalita = "fisso"
                    self.avvia_partita()
                elif event.key == pygame.K_o:
                    self.state = "opzioni"
                elif event.key == pygame.K_p:
                    if self.profilo_corrente in self.profili:
                        self.profilo_cursor = self.profili.index(self.profilo_corrente)
                    else:
                        self.profilo_cursor = 0
                    self.state = "profile_select"
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
            elif self.state == "opzioni":
                if event.key == pygame.K_1:
                    self.state = "opzioni_auto"
                elif event.key == pygame.K_2:
                    self.mostra_config()
                elif event.key == pygame.K_UP:
                    self.opzioni_cursor = max(0, self.opzioni_cursor - 1)
                elif event.key == pygame.K_DOWN:
                    self.opzioni_cursor = min(1, self.opzioni_cursor + 1)
                elif event.key == pygame.K_RETURN:
                    if self.opzioni_cursor == 0:
                        self.state = "opzioni_auto"
                    else:
                        self.mostra_config()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"
            elif self.state == "opzioni_auto":
                if event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    self.config_timeout = min(99, self.config_timeout + 1)
                    self.salva_config_profilo()
                elif event.key == pygame.K_MINUS:
                    self.config_timeout = max(3, self.config_timeout - 1)
                    self.salva_config_profilo()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "opzioni"
            elif self.state == "config_fisso":
                self.gestisci_config(event)
            elif self.state == "gioco":
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.avvia_partita()
                        return
                    elif event.key == pygame.K_m:
                        self.salva_sessione()
                        self.state = "menu"
                        return
                    elif event.key == pygame.K_ESCAPE:
                        self.salva_sessione()
                        self.state = "menu"
                        return
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
                    elif event.unicode == "-" and not self.input_utente:
                        self.input_utente += event.unicode
            elif self.state == "gameover":
                if event.key == pygame.K_r:
                    self.avvia_partita()
                elif event.key == pygame.K_m:
                    self.state = "menu"
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if self.state == "menu":
                # Opzione 1: Autoapprendimento (midleft 340, 280)
                if 340 - 10 <= mx <= 340 + 580 and 280 - 10 <= my <= 280 + 74:
                    self.modalita = "auto"
                    self.avvia_partita()
                # Opzione 2: Livello Fisso (midleft 340, 380)
                elif 340 - 10 <= mx <= 340 + 580 and 380 - 10 <= my <= 380 + 74:
                    self.modalita = "fisso"
                    self.avvia_partita()
                # Gear icon (centro 1235, 45, raggio 22)
                elif (mx - 1235) ** 2 + (my - 45) ** 2 <= (22 + 10) ** 2:
                    self.state = "opzioni"
                # Profilo (midleft 340, 550)
                elif 340 - 10 <= mx <= 340 + 400 and 550 - 10 <= my <= 550 + 34:
                    if self.profilo_corrente in self.profili:
                        self.profilo_cursor = self.profili.index(self.profilo_corrente)
                    else:
                        self.profilo_cursor = 0
                    self.state = "profile_select"
            elif self.state == "profile_select":
                if not self.profilo_input_mode:
                    # Lista profili
                    for i, nome in enumerate(self.profili):
                        y = 170 + i * 60
                        if 340 - 10 <= mx <= 340 + 400 and y - 10 <= my <= y + 64:
                            self.profilo_corrente = nome
                            self.carica_config_profilo(nome)
                            self.aggiorna_char_img()
                            self.salva_profili()
                            self.state = "menu"
                            break
                    else:
                        # "+ Nuovo profilo" (ultima entry)
                        y = 170 + len(self.profili) * 60
                        if 340 - 10 <= mx <= 340 + 400 and y - 10 <= my <= y + 64:
                            self.profilo_input_mode = True
                            self.profilo_input = ""
                elif self.profilo_genere_mode:
                    # Scelta genere
                    if 330 <= mx <= 610 and 370 - 10 <= my <= 370 + 130:
                        self.config_genere = "F"
                        nuovo = self.profilo_input.strip()
                        self.profili.append(nuovo)
                        self.salva_config_profilo(nuovo)
                        self.profilo_corrente = nuovo
                        self.aggiorna_char_img()
                        self.salva_profili()
                        self.profilo_input = ""
                        self.profilo_input_mode = False
                        self.profilo_genere_mode = False
                        self.state = "menu"
                    elif 670 <= mx <= 950 and 370 - 10 <= my <= 370 + 130:
                        self.config_genere = "M"
                        nuovo = self.profilo_input.strip()
                        self.profili.append(nuovo)
                        self.salva_config_profilo(nuovo)
                        self.profilo_corrente = nuovo
                        self.aggiorna_char_img()
                        self.salva_profili()
                        self.profilo_input = ""
                        self.profilo_input_mode = False
                        self.profilo_genere_mode = False
                        self.state = "menu"
            elif self.state == "opzioni":
                if SCREEN_WIDTH // 2 - 320 <= mx <= SCREEN_WIDTH // 2 + 320:
                    if 209 <= my <= 273:
                        self.state = "opzioni_auto"
                    elif 289 <= my <= 353:
                        self.mostra_config()
            elif self.state == "opzioni_auto":
                tx = SCREEN_WIDTH // 2 + 20
                lw = 30
                if tx - 2 <= mx <= tx + 100 + 2 and 218 <= my <= 256:
                    if mx < tx + lw:
                        self.config_timeout = max(3, self.config_timeout - 1)
                    elif mx >= tx + lw + 40:
                        self.config_timeout = min(99, self.config_timeout + 1)
                    self.salva_config_profilo()
            elif self.state == "config_fisso":
                try:
                    self.gestisci_config(event)
                except Exception as e:
                    print(f"config mouse error: {e}")
                    import traceback
                    traceback.print_exc()

    def gestisci_config(self, event):
        ops = ["moltiplicazione", "addizione", "sottrazione"]
        op_idx = ops.index(self.config_operazione)
        addizione = self.config_operazione == "addizione"
        sottrazione = self.config_operazione == "sottrazione"
        pools_mode = addizione or sottrazione
        cols_u = 5
        items_pool = 10 if pools_mode else 13

        def row_y(r):
            base = [150, 210, 290, 370, 420, 470, 520, 550]
            cell_h, gap = 30, 6
            subrows_pool = (items_pool + 4) // 5
            pool_extra = max(0, (subrows_pool - 2)) * (cell_h + gap)
            offset = 0
            if r >= 2:
                offset += pool_extra
            if r >= 3:
                offset += pool_extra
            return base[r] + offset

        def pool_ncols():
            if pools_mode:
                return (10, 5)
            return (13, 5)

        def pool_rows():
            items, cols = pool_ncols()
            return (items + cols - 1) // cols

        def pool_index(subrow, col):
            items, cols = pool_ncols()
            idx = subrow * cols + col
            return idx if idx < items else -1

        def max_col_for_row(r):
            if r in (1, 2):
                return 4
            return 0

        def skip_somma(r, step):
            if not addizione and not sottrazione:
                if step == 1 and r == 2:
                    return 4
                if step == -1 and r == 4:
                    return 2
            return r

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Row 7: CONFERMA
            y7 = row_y(7)
            if SCREEN_WIDTH // 2 - 110 <= mx <= SCREEN_WIDTH // 2 + 110 and y7 <= my <= y7 + 46:
                self.salva_config_profilo()
                self.state = "menu"
                return

            # Row 0: operation selector
            y0 = row_y(0)
            if y0 - 2 <= my <= y0 + 36:
                for i in range(3):
                    sx = 360 + i * 220
                    if sx <= mx <= sx + 206:
                        self.config_operazione = ops[i]
                        self.config_cursor_row = 0
                        self.config_cursor_col = 0
                        self.config_cursor_subrow = 0
                        return

            # Row 1 and 2: pool grid
            for ri in range(2):
                r = 1 + ri
                y_base = row_y(r)
                subrows = (items_pool + cols_u - 1) // cols_u
                cell_w, cell_h = 100, 30
                gap = 6
                grid_x = 360
                for sr in range(subrows):
                    sy = y_base + sr * (cell_h + gap)
                    for c in range(cols_u):
                        idx = sr * cols_u + c
                        if idx >= items_pool:
                            break
                        sx = grid_x + c * (cell_w + gap)
                        if sx - 2 <= mx <= sx + cell_w + 2 and sy - 2 <= my <= sy + cell_h + 2:
                            self.config_cursor_row = r
                            self.config_cursor_col = c
                            self.config_cursor_subrow = sr
                            pool = self.config_pool_a if r == 1 else self.config_pool_b
                            if pools_mode:
                                start = idx * 10
                                for i in range(start, start + 10):
                                    pool[i] = not pool[i]
                                if not any(pool):
                                    pool[start] = True
                            else:
                                pool[idx] = not pool[idx]
                                if not any(pool):
                                    pool[idx] = True
                            return

            # Row 3: somma massima (addizione) / differenza positiva (sottrazione)
            y3 = row_y(3)
            if y3 - 2 <= my <= y3 + 36:
                if addizione:
                    lw = 30
                    if 360 - 2 <= mx <= 360 + 100 + 2:
                        self.config_cursor_row = 3
                        self.config_cursor_col = 0
                        if mx < 360 + lw:
                            self.config_somma_massima = max(1, self.config_somma_massima - 1)
                        elif mx >= 360 + lw + 40:
                            self.config_somma_massima = min(199, self.config_somma_massima + 1)
                        return
                elif sottrazione:
                    if 350 <= mx <= 540 and y3 - 4 <= my <= y3 + 40:
                        self.config_cursor_row = 3
                        self.config_cursor_col = 0
                        self.config_differenza_positiva = not self.config_differenza_positiva
                        return

            # Row 4: domande
            y4 = row_y(4)
            if y4 - 2 <= my <= y4 + 36:
                lw = 30
                if 360 - 2 <= mx <= 360 + 100 + 2:
                    self.config_cursor_row = 4
                    self.config_cursor_col = 0
                    if mx < 360 + lw:
                        self.config_domande = max(1, self.config_domande - 1)
                    elif mx >= 360 + lw + 40:
                        self.config_domande = min(99, self.config_domande + 1)
                    return

            # Row 5: swap
            y5 = row_y(5)
            if y5 - 4 <= my <= y5 + 40:
                if 350 <= mx <= 540 and not sottrazione:
                    self.config_cursor_row = 5
                    self.config_cursor_col = 0
                    self.config_swap = not self.config_swap
                    return

            # Row 6: timeout
            y6 = row_y(6)
            if y6 - 2 <= my <= y6 + 36:
                lw = 30
                if 360 - 2 <= mx <= 360 + 100 + 2:
                    self.config_cursor_row = 6
                    self.config_cursor_col = 0
                    if mx < 360 + lw:
                        self.config_timeout = max(3, self.config_timeout - 1)
                    elif mx >= 360 + lw + 40:
                        self.config_timeout = min(99, self.config_timeout + 1)
                    return

            return

        if event.key == pygame.K_ESCAPE:
            self.state = "opzioni"
            return
        if event.key == pygame.K_RETURN:
            self.salva_config_profilo()
            self.state = "menu"
            return

        row = self.config_cursor_row
        col = self.config_cursor_col
        sub = self.config_cursor_subrow

        if event.key == pygame.K_UP:
            if row in (1, 2):
                if sub > 0:
                    sub -= 1
                else:
                    row = skip_somma(max(0, row - 1), -1)
            else:
                row = skip_somma(max(0, row - 1), -1)
            self.config_cursor_col = min(col, max_col_for_row(row))
        elif event.key == pygame.K_DOWN:
            if row in (1, 2):
                if sub < pool_rows() - 1:
                    idx = pool_index(sub + 1, col)
                    if idx >= 0:
                        sub += 1
                    else:
                        row = skip_somma(min(7, row + 1), 1)
                else:
                    row = skip_somma(min(7, row + 1), 1)
            else:
                row = skip_somma(min(7, row + 1), 1)
            self.config_cursor_col = min(col, max_col_for_row(row))
        elif event.key == pygame.K_LEFT:
            if row == 0:
                self.config_operazione = ops[(op_idx - 1) % 3]
            elif row in (1, 2):
                if col > 0:
                    col -= 1
                else:
                    col = max_col_for_row(row)
            else:
                self.config_cursor_col = max(0, col - 1)
        elif event.key == pygame.K_RIGHT:
            if row == 0:
                self.config_operazione = ops[(op_idx + 1) % 3]
            elif row in (1, 2):
                if col < 4:
                    idx = pool_index(sub, col + 1)
                    if idx >= 0:
                        col += 1
            else:
                self.config_cursor_col = min(max_col_for_row(row), col + 1)
        elif event.key == pygame.K_SPACE:
            if row == 0:
                self.config_operazione = ops[(op_idx + 1) % 3]
            elif row in (1, 2):
                pool = self.config_pool_a if row == 1 else self.config_pool_b
                idx = pool_index(sub, col)
                if idx >= 0:
                    if pools_mode:
                        start = idx * 10
                        for i in range(start, start + 10):
                            pool[i] = not pool[i]
                        if not any(pool):
                            pool[start] = True
                    else:
                        pool[idx] = not pool[idx]
                        if not any(pool):
                            pool[idx] = True
            elif row == 3 and sottrazione:
                self.config_differenza_positiva = not self.config_differenza_positiva
            elif row == 5 and not sottrazione:
                self.config_swap = not self.config_swap
        elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
            if row == 3 and addizione:
                self.config_somma_massima = min(199, self.config_somma_massima + 1)
            elif row == 4:
                self.config_domande = min(99, self.config_domande + 1)
            elif row == 6:
                self.config_timeout = min(99, self.config_timeout + 1)
        elif event.key == pygame.K_MINUS:
            if row == 3 and addizione:
                self.config_somma_massima = max(1, self.config_somma_massima - 1)
            elif row == 4:
                self.config_domande = max(1, self.config_domande - 1)
            elif row == 6:
                self.config_timeout = max(3, self.config_timeout - 1)

        self.config_cursor_row = row
        self.config_cursor_col = col
        self.config_cursor_subrow = sub

    def controlla_risposta(self):
        if not self.domanda_attiva:
            return

        tempo = min((pygame.time.get_ticks() - self.inizio_domanda) / 1000.0, self.timeout_limite)
        self.tempi_risposta.append(tempo)

        livello = 0 if self.modalita == "fisso" else self.livello
        self.stats.setdefault(livello, {"corrette": 0, "sbagliate": 0, "tempi": []})

        testo = self.input_utente.strip()
        if testo.startswith("-") and testo[1:].isdigit():
            risposta = int(testo)
        elif testo.isdigit():
            risposta = int(testo)
            if risposta == self.risultato_atteso:
                self.corretto = True
                self.stats[livello]["corrette"] += 1
                self.mostro_colpito = True
                self.mostro_fade_start = pygame.time.get_ticks()
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
        tempo = self.timeout_limite
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
        self.mostro_fade_start = pygame.time.get_ticks()
        self.hit_timer = 12
        if self.vite <= 0:
            self.game_over = True

    def aggiorna(self):
        if self.zap_timer > 0:
            self.zap_timer -= 1
        if self.hit_timer > 0:
            self.hit_timer -= 1
        if self.state == "splash":
            if pygame.time.get_ticks() - self.splash_start >= 5000:
                self.state = "profile_select"
            return
        if self.state == "gameover":
            return
        if self.state not in ("gioco",):
            return

        if self.domanda_attiva:
            elapsed = (pygame.time.get_ticks() - self.inizio_domanda) / 1000.0
            self.mostro_progresso = min(elapsed / self.timeout_limite, 1.0)
            start_x = SCREEN_WIDTH + 30
            end_x = 210
            self.mostro_x = start_x - self.mostro_progresso * (start_x - end_x)

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
        if self.state == "splash":
            self.disegna_splash()
        elif self.state == "profile_select":
            self.disegna_profilo()
        elif self.state == "gioco" and not self.game_over:
            self.disegna_gioco()
        else:
            self.screen.blit(self.bg, (0, 0))
            if self.state == "menu":
                self.disegna_menu()
            elif self.state == "opzioni":
                self.disegna_opzioni()
            elif self.state == "opzioni_auto":
                self.disegna_opzioni_auto()
            elif self.state == "config_fisso":
                self.disegna_config()
            elif self.state in ("gioco", "gameover"):
                self.disegna_gameover()

        pygame.display.flip()

    def disegna_splash(self):
        elapsed = pygame.time.get_ticks() - self.splash_start
        logo_rect = self.logo.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(self.logo, logo_rect)

        if elapsed < 1000:
            alpha = 255 - int(255 * elapsed / 1000)
        elif elapsed > 4000:
            alpha = int(255 * (elapsed - 4000) / 1000)
        else:
            alpha = 0
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(alpha)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

    def disegna_profilo(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BG_DARK)
        self.screen.blit(overlay, (0, 0))

        if self.profilo_input_mode:
            if self.profilo_genere_mode:
                titolo = self.font_titolo.render("NUOVO PROFILO", True, GOLD)
                rect = titolo.get_rect(center=(SCREEN_WIDTH // 2, 100))
                self.screen.blit(titolo, rect)

                nome_label = self.font_medio.render(f"Profilo: {self.profilo_input}", True, WHITE)
                rect = nome_label.get_rect(center=(SCREEN_WIDTH // 2, 200))
                self.screen.blit(nome_label, rect)

                prompt = self.font_grande.render("Seleziona il sesso:", True, WHITE)
                rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, 300))
                self.screen.blit(prompt, rect)

                for i, (key, label) in enumerate([("F", "Femmina"), ("M", "Maschio")]):
                    sx = SCREEN_WIDTH // 2 - 310 + i * 340
                    y = 370
                    img_h = int(80 / 900 * 1330)
                    box_h = max(90, img_h + 20)
                    pygame.draw.rect(self.screen, (60, 60, 70), (sx, y, 280, box_h), border_radius=8)
                    if self.char_imgs[key]:
                        img = pygame.transform.scale(self.char_imgs[key], (80, img_h))
                        self.screen.blit(img, (sx + 20, y + 10))
                    txt = self.font_medio.render(label, True, WHITE)
                    rect = txt.get_rect(midleft=(sx + 120, y + box_h // 2))
                    self.screen.blit(txt, rect)

                tip = self.font_piccolo.render("Premi F o M per scegliere  |  ESC: annulla", True, GRAY)
                rect = tip.get_rect(center=(SCREEN_WIDTH // 2, 590))
                self.screen.blit(tip, rect)
            else:
                titolo = self.font_titolo.render("NUOVO PROFILO", True, GOLD)
                rect = titolo.get_rect(center=(SCREEN_WIDTH // 2, 120))
                self.screen.blit(titolo, rect)

                lbl = self.font_medio.render("Inserisci il nome:", True, WHITE)
                rect = lbl.get_rect(center=(SCREEN_WIDTH // 2, 260))
                self.screen.blit(lbl, rect)

                txt = self.profilo_input + ("|" if pygame.time.get_ticks() % 1000 < 500 else " ")
                surf = self.font_input.render(txt, True, WHITE)
                box = surf.get_rect(center=(SCREEN_WIDTH // 2, 330))
                bg = box.inflate(40, 16)
                bg.width = max(bg.width, 200)
                pygame.draw.rect(self.screen, (40, 40, 60), bg, border_radius=8)
                pygame.draw.rect(self.screen, (100, 100, 180), bg, 2, border_radius=8)
                self.screen.blit(surf, box)

                if self.profilo_input:
                    hint = self.font_piccolo.render("INVIO per confermare", True, GRAY)
                    rect = hint.get_rect(center=(SCREEN_WIDTH // 2, 380))
                    self.screen.blit(hint, rect)
                back = self.font_piccolo.render("ESC: annulla", True, GRAY)
                rect = back.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
                self.screen.blit(back, rect)
            return

        titolo = self.font_titolo.render("SELEZIONA PROFILO", True, GOLD)
        rect = titolo.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(titolo, rect)

        voci = self.profili + ["+ Nuovo profilo"]
        nuovo_idx = len(self.profili)
        for i, voce in enumerate(voci):
            y = 170 + i * 60
            col = GOLD if i == self.profilo_cursor else WHITE
            txt = self.font_grande.render(voce, True, col)
            rect = txt.get_rect(midleft=(SCREEN_WIDTH // 2 - 200, y))
            self.screen.blit(txt, rect)
            if i < nuovo_idx and voce == self.profilo_corrente:
                ok = self.font_piccolo.render("(attivo)", True, GRAY)
                rect = ok.get_rect(midleft=(SCREEN_WIDTH // 2 + 150, y + 20))
                self.screen.blit(ok, rect)

        info = self.font_piccolo.render("Freccette: naviga  |  INVIO: seleziona  |  ESC: esci", True, GRAY)
        rect = info.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        self.screen.blit(info, rect)

    def disegna_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BG_DARK)
        self.screen.blit(overlay, (0, 0))

        titolo = self.font_titolo.render("MATH WIZARD", True, GOLD)
        rect = titolo.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(titolo, rect)

        sottotitolo = self.font_medio.render("Impara divertendoti!", True, WHITE)
        rect = sottotitolo.get_rect(center=(SCREEN_WIDTH // 2, 160))
        self.screen.blit(sottotitolo, rect)

        opzioni = [
            ("1  Autoapprendimento", "Livelli progressivi automatici, operandi 0-12, level-up basato su precisione e velocita"),
            ("2  Livello Fisso", "Scegli operandi, numero domande e sfida a difficolta costante"),
        ]
        for i, (tit, desc) in enumerate(opzioni):
            y = 280 + i * 100
            col = GOLD if i == self.menu_cursor else WHITE
            opt = self.font_grande.render(tit, True, col)
            rect = opt.get_rect(midleft=(SCREEN_WIDTH // 2 - 300, y))
            self.screen.blit(opt, rect)
            desc_surf = self.font_piccolo.render(desc, True, GRAY)
            rect = desc_surf.get_rect(midleft=(SCREEN_WIDTH // 2 - 300, y + 40))
            self.screen.blit(desc_surf, rect)

        # gear icon
        cx, cy = SCREEN_WIDTH - 45, 45
        gear_size = 44
        gear_scaled = pygame.transform.scale(self.gear_img, (gear_size, gear_size))
        rect = gear_scaled.get_rect(center=(cx, cy))
        self.screen.blit(gear_scaled, rect)

        profilo_lbl = self.font_piccolo.render(f"Profilo: {self.profilo_corrente}", True, GRAY)
        rect = profilo_lbl.get_rect(midleft=(SCREEN_WIDTH // 2 - 300, 550))
        self.screen.blit(profilo_lbl, rect)
        cambia_lbl = self.font_piccolo.render("P: Cambia profilo", True, GRAY)
        rect = cambia_lbl.get_rect(midleft=(SCREEN_WIDTH // 2 - 300, 575))
        self.screen.blit(cambia_lbl, rect)

        info = self.font_piccolo.render("Freccette: seleziona  |  INVIO: conferma  |  O: Opzioni  |  ESC: Esci", True, WHITE)
        rect = info.get_rect(center=(SCREEN_WIDTH // 2, 620))
        self.screen.blit(info, rect)

        version_surf = self.font_tiny.render(f"v{self.version}", True, GRAY)
        rect = version_surf.get_rect(bottomright=(SCREEN_WIDTH - 8, SCREEN_HEIGHT - 8))
        self.screen.blit(version_surf, rect)

    def disegna_opzioni(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BG_DARK)
        self.screen.blit(overlay, (0, 0))

        titolo = self.font_titolo.render("OPZIONI", True, GOLD)
        rect = titolo.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(titolo, rect)

        voci = [("1", "Autoapprendimento"), ("2", "Livello Fisso")]
        for i, (num, voce) in enumerate(voci):
            y = 220 + i * 80
            col = GOLD if i == self.opzioni_cursor else WHITE
            txt = self.font_grande.render(f"{num}  {voce}", True, col)
            rect = txt.get_rect(center=(SCREEN_WIDTH // 2, y + 21))
            self.screen.blit(txt, rect)

        info = self.font_piccolo.render("1/2 o Freccette: naviga  |  INVIO: seleziona  |  ESC: indietro", True, GRAY)
        rect = info.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        self.screen.blit(info, rect)

    def disegna_opzioni_auto(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BG_DARK)
        self.screen.blit(overlay, (0, 0))

        titolo = self.font_titolo.render("OPZIONI - AUTOAPPRENDIMENTO", True, GOLD)
        rect = titolo.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(titolo, rect)

        # Timeout
        y = 220
        label_t = self.font_medio.render("Timeout (secondi)", True, WHITE)
        rect = label_t.get_rect(midleft=(SCREEN_WIDTH // 2 - 200, y + 17))
        self.screen.blit(label_t, rect)
        focused = self.opzioni_cursor == 0
        tx = SCREEN_WIDTH // 2 + 20
        lw, vw, rw = 30, 40, 30
        total = lw + vw + rw
        if focused:
            pygame.draw.rect(self.screen, (255, 255, 100), (tx - 2, y - 2, total + 4, 38), 3, border_radius=4)
        pygame.draw.rect(self.screen, (70, 70, 80), (tx, y, lw, 34), border_radius=4)
        pygame.draw.rect(self.screen, (40, 40, 50), (tx + lw, y, vw, 34))
        pygame.draw.rect(self.screen, (70, 70, 80), (tx + lw + vw, y, rw, 34), border_radius=4)
        minus = self.font_medio.render("-", True, WHITE)
        plus = self.font_medio.render("+", True, WHITE)
        self.screen.blit(minus, minus.get_rect(center=(tx + lw // 2, y + 17)))
        self.screen.blit(plus, plus.get_rect(center=(tx + lw + vw + rw // 2, y + 17)))
        t_surf = self.font_grande.render(str(self.config_timeout), True, WHITE)
        self.screen.blit(t_surf, t_surf.get_rect(center=(tx + lw + vw // 2, y + 17)))

        back = self.font_piccolo.render("ESC: torna indietro", True, GRAY)
        rect = back.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        self.screen.blit(back, rect)

    def disegna_config(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BG_DARK)
        self.screen.blit(overlay, (0, 0))

        titolo = self.font_titolo.render("OPZIONI - LIVELLO FISSO", True, GOLD)
        rect = titolo.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(titolo, rect)

        ops = ["moltiplicazione", "addizione", "sottrazione"]
        op_idx = ops.index(self.config_operazione)
        addizione = self.config_operazione == "addizione"
        sottrazione = self.config_operazione == "sottrazione"

        def row_y(r):
            base = [150, 210, 290, 370, 420, 470, 520, 550]
            pools_mode = addizione or sottrazione
            cell_h, gap = 30, 6
            items_pool = 10 if pools_mode else 13
            subrows_pool = (items_pool + 4) // 5
            pool_extra = max(0, (subrows_pool - 2)) * (cell_h + gap)
            offset = 0
            if r >= 2:
                offset += pool_extra
            if r >= 3:
                offset += pool_extra
            return base[r] + offset

        # Row 0: Operazione
        row = 0
        y = row_y(row)
        label_op = self.font_tiny.render("Operazione", True, WHITE)
        rect = label_op.get_rect(midleft=(80, y + 17))
        self.screen.blit(label_op, rect)
        focused = self.config_cursor_row == row
        opzioni_op = ["Moltiplicazione", "Addizione", "Sottrazione"]
        for i, nome in enumerate(opzioni_op):
            sx = 360 + i * 220
            sel = i == op_idx
            bg_col = (60, 130, 60) if sel else (60, 60, 70)
            if focused:
                col_b = (255, 255, 100) if sel else (80, 80, 90)
                pygame.draw.rect(self.screen, col_b, (sx - 2, y - 2, 210, 38), 3, border_radius=4)
            pygame.draw.rect(self.screen, bg_col, (sx, y, 206, 34), border_radius=4)
            txt = self.font_tiny.render(nome, True, WHITE)
            rect_t = txt.get_rect(center=(sx + 103, y + 17))
            self.screen.blit(txt, rect_t)

        # Row 1-2: Pool A / Pool B (unified 5-col grid)
        labels = ["Operando A", "Operando B"]
        pools = [self.config_pool_a, self.config_pool_b]
        cols_u = 5
        pools_mode = addizione or sottrazione
        for ri in range(2):
            row = 1 + ri
            y_base = row_y(row)
            label = self.font_tiny.render(labels[ri], True, WHITE)
            rect = label.get_rect(midleft=(80, y_base + 17))
            self.screen.blit(label, rect)

            items = 10 if pools_mode else 13
            subrows = (items + cols_u - 1) // cols_u
            cell_w, cell_h = 100, 30
            gap = 6
            grid_x = 360
            for sr in range(subrows):
                sy = y_base + sr * (cell_h + gap)
                for c in range(cols_u):
                    idx = sr * cols_u + c
                    if idx >= items:
                        break
                    sx = grid_x + c * (cell_w + gap)
                    if pools_mode:
                        start = idx * 10
                        end = min(start + 9, 99)
                        selected = any(pools[ri][start:start+10])
                        txt = f"{start}-{end}"
                    else:
                        selected = pools[ri][idx]
                        txt = str(idx)
                    focus = self.config_cursor_row == row and self.config_cursor_col == c and self.config_cursor_subrow == sr
                    bg_col = (60, 130, 60) if selected else (60, 60, 70)
                    if focus:
                        pygame.draw.rect(self.screen, (255, 255, 100), (sx - 2, sy - 2, cell_w + 4, cell_h + 4), 3, border_radius=4)
                    pygame.draw.rect(self.screen, bg_col, (sx, sy, cell_w, cell_h), border_radius=4)
                    t = self.font_tiny.render(txt, True, WHITE)
                    rt = t.get_rect(center=(sx + cell_w // 2, sy + cell_h // 2))
                    self.screen.blit(t, rt)

        # Row 3: Somma massima / Differenza positiva
        row = 3
        y = row_y(row)
        if addizione:
            label_s = self.font_tiny.render("Somma massima", True, WHITE)
            rect = label_s.get_rect(midleft=(80, y + 17))
            self.screen.blit(label_s, rect)
            focused = self.config_cursor_row == row
            sx = 360
            lw, vw, rw = 30, 40, 30
            total = lw + vw + rw
            if focused:
                pygame.draw.rect(self.screen, (255, 255, 100), (sx - 2, y - 2, total + 4, 38), 3, border_radius=4)
            pygame.draw.rect(self.screen, (70, 70, 80), (sx, y, lw, 34), border_radius=4)
            pygame.draw.rect(self.screen, (40, 40, 50), (sx + lw, y, vw, 34))
            pygame.draw.rect(self.screen, (70, 70, 80), (sx + lw + vw, y, rw, 34), border_radius=4)
            minus = self.font_tiny.render("-", True, WHITE)
            plus = self.font_tiny.render("+", True, WHITE)
            self.screen.blit(minus, minus.get_rect(center=(sx + lw // 2, y + 17)))
            self.screen.blit(plus, plus.get_rect(center=(sx + lw + vw + rw // 2, y + 17)))
            s_surf = self.font_tiny.render(str(self.config_somma_massima), True, WHITE)
            self.screen.blit(s_surf, s_surf.get_rect(center=(sx + lw + vw // 2, y + 17)))
        elif sottrazione:
            focused = self.config_cursor_row == row
            label_d = self.font_tiny.render("Differenza positiva", True, WHITE)
            rect = label_d.get_rect(midleft=(80, y + 17))
            self.screen.blit(label_d, rect)
            if focused:
                pygame.draw.rect(self.screen, (255, 255, 100), (350, y - 4, 190, 44), 3, border_radius=6)
            bg_d = (60, 130, 60) if self.config_differenza_positiva else (60, 60, 70)
            pygame.draw.rect(self.screen, bg_d, (352, y, 186, 36), border_radius=6)
            dp_txt = "ON" if self.config_differenza_positiva else "OFF"
            dp_val = self.font_tiny.render(dp_txt, True, WHITE)
            rect_dv = dp_val.get_rect(center=(445, y + 18))
            self.screen.blit(dp_val, rect_dv)

        # Row 4: Domande
        row = 4
        y = row_y(row)
        label_q = self.font_tiny.render("Domande", True, WHITE)
        rect = label_q.get_rect(midleft=(80, y + 17))
        self.screen.blit(label_q, rect)
        focused = self.config_cursor_row == row
        qx = 360
        lw, vw, rw = 30, 40, 30
        total = lw + vw + rw
        if focused:
            pygame.draw.rect(self.screen, (255, 255, 100), (qx - 2, y - 2, total + 4, 38), 3, border_radius=4)
        pygame.draw.rect(self.screen, (70, 70, 80), (qx, y, lw, 34), border_radius=4)
        pygame.draw.rect(self.screen, (40, 40, 50), (qx + lw, y, vw, 34))
        pygame.draw.rect(self.screen, (70, 70, 80), (qx + lw + vw, y, rw, 34), border_radius=4)
        minus = self.font_tiny.render("-", True, WHITE)
        plus = self.font_tiny.render("+", True, WHITE)
        self.screen.blit(minus, minus.get_rect(center=(qx + lw // 2, y + 17)))
        self.screen.blit(plus, plus.get_rect(center=(qx + lw + vw + rw // 2, y + 17)))
        q_surf = self.font_tiny.render(str(self.config_domande), True, WHITE)
        self.screen.blit(q_surf, q_surf.get_rect(center=(qx + lw + vw // 2, y + 17)))

        # Row 5: Commutazione
        row = 5
        y = row_y(row)
        swap_locked = sottrazione
        swap_sel = self.config_cursor_row == row and not swap_locked
        if swap_sel:
            pygame.draw.rect(self.screen, (255, 255, 100), (350, y - 4, 190, 44), 3, border_radius=6)
        bg_swap = (60, 130, 60) if (self.config_swap or swap_locked) else (60, 60, 70)
        pygame.draw.rect(self.screen, bg_swap, (352, y, 186, 36), border_radius=6)
        sw_txt = "ON" if (self.config_swap or swap_locked) else "OFF"
        swap_label = self.font_tiny.render("Commuta A/B", True, WHITE)
        rect_sl = swap_label.get_rect(midleft=(80, y + 18))
        self.screen.blit(swap_label, rect_sl)
        swap_val = self.font_tiny.render(sw_txt, True, WHITE)
        rect_sv = swap_val.get_rect(center=(445, y + 18))
        self.screen.blit(swap_val, rect_sv)

        # Row 6: Timeout
        row = 6
        y = row_y(row)
        label_t = self.font_tiny.render("Timeout (secondi)", True, WHITE)
        rect = label_t.get_rect(midleft=(80, y + 17))
        self.screen.blit(label_t, rect)
        focused = self.config_cursor_row == row
        tx = 360
        lw, vw, rw = 30, 40, 30
        total = lw + vw + rw
        if focused:
            pygame.draw.rect(self.screen, (255, 255, 100), (tx - 2, y - 2, total + 4, 38), 3, border_radius=4)
        pygame.draw.rect(self.screen, (70, 70, 80), (tx, y, lw, 34), border_radius=4)
        pygame.draw.rect(self.screen, (40, 40, 50), (tx + lw, y, vw, 34))
        pygame.draw.rect(self.screen, (70, 70, 80), (tx + lw + vw, y, rw, 34), border_radius=4)
        minus = self.font_tiny.render("-", True, WHITE)
        plus = self.font_tiny.render("+", True, WHITE)
        self.screen.blit(minus, minus.get_rect(center=(tx + lw // 2, y + 17)))
        self.screen.blit(plus, plus.get_rect(center=(tx + lw + vw + rw // 2, y + 17)))
        t_surf = self.font_tiny.render(str(self.config_timeout), True, WHITE)
        self.screen.blit(t_surf, t_surf.get_rect(center=(tx + lw + vw // 2, y + 17)))

        # Row 7: CONFERMA
        row = 7
        y = row_y(row)
        start_sel = self.config_cursor_row == row
        if start_sel:
            pygame.draw.rect(self.screen, (255, 255, 100), (SCREEN_WIDTH // 2 - 112, y - 4, 224, 54), 3, border_radius=8)
        pygame.draw.rect(self.screen, (40, 120, 40), (SCREEN_WIDTH // 2 - 110, y, 220, 46), border_radius=8)
        start_txt = self.font_tiny.render("CONFERMA", True, WHITE)
        rect_s = start_txt.get_rect(center=(SCREEN_WIDTH // 2, y + 23))
        self.screen.blit(start_txt, rect_s)

        help = self.font_piccolo.render("Freccette: naviga  |  SPACE: attiva/disattiva  |  INVIO: conferma  |  ESC: indietro", True, GRAY)
        rect_h2 = help.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 15))
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
        wy_monster = wy + 50
        self.screen.blit(self.char_img, (wx, wy_monster))

        if self.mostro_colpito:
            elapsed = pygame.time.get_ticks() - self.mostro_fade_start
            alpha = max(0, 255 - int(elapsed / 500 * 255))
            if alpha > 0:
                faded = self.monster_img.copy()
                faded.set_alpha(alpha)
                self.screen.blit(faded, (self.mostro_x + shake[0], wy_monster))
        else:
            self.screen.blit(self.monster_img, (self.mostro_x + shake[0], wy_monster))

        if self.zap_timer > 0:
            start_x, start_y = wx + 25, wy_monster + 20
            end_x, end_y = self.mostro_x + 100, wy_monster + self.char_h // 2
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

        if hasattr(self, 'operazione') and self.operazione == "sottrazione":
            segno = "-"
        elif hasattr(self, 'operazione') and self.operazione == "addizione":
            segno = "+"
        else:
            segno = "x"
        domanda = self.font_grande.render(f"{self.a}  {segno}  {self.b}  =  ?", True, WHITE)
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
            cx = SCREEN_WIDTH - 70 - i * 50
            img = self.heart_red if i < self.vite else self.heart_grey
            self.screen.blit(img, (cx - 17, 30))

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

            tempo_testo = self.font_piccolo.render(f"{self.timeout_limite * (1 - self.mostro_progresso):.0f}s", True, WHITE)
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

        if self.mostro_colpito:
            elapsed = pygame.time.get_ticks() - self.mostro_fade_start
            white_alpha = max(0, 150 - int(elapsed / 200 * 150))
            if white_alpha > 0:
                flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                flash.set_alpha(white_alpha)
                flash.fill(WHITE)
                self.screen.blit(flash, (0, 0))

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
            op_txt = self.operazione.capitalize() if hasattr(self, 'operazione') else "Moltiplicazione"
            pool_a_txt = ",".join(str(n) for n in self.pool_a)
            pool_b_txt = ",".join(str(n) for n in self.pool_b)
            extra = ""
            if self.operazione == "sottrazione" and getattr(self, 'differenza_positiva', False):
                extra = " | Diff. positiva: ON"
            riga = f"{now} | Livello Fisso | {op_txt} | Corrette: {tot_corrette} | Sbagliate: {tot_sbagliate} | Pool A: [{pool_a_txt}] | Pool B: [{pool_b_txt}] | Domande: {self.domande_fatte}/{self.domande_totali} | Tempo medio: {tempo_medio:.1f}s{extra}"
        path = self.percorso_sessioni()
        with open(path, "a", encoding="utf-8") as f:
            f.write(riga + "\n")

    def carica_sessioni(self):
        path = self.percorso_sessioni()
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
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
