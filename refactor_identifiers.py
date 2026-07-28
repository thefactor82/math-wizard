import tokenize
import token
import io
import ast

mapping = {
    'Gioco':'Game',
    'imposta_cursore':'setup_cursor',
    'aggiorna_char_img':'update_char_image',
    'carica_risorse':'load_resources',
    'carica_spritesheet':'load_spritesheet',
    'gestione_profili':'setup_profiles',
    'salva_profili':'save_profiles',
    'salva_config_profilo':'save_profile_config',
    'carica_config_profilo':'load_profile_config',
    'percorso_sessioni':'sessions_path',
    'azzera_partita':'reset_game_state',
    'mostra_config':'show_config',
    'avvia_partita':'start_game',
    'livello_effettivo':'effective_level',
    'e_ultimo_livello_storia':'is_last_story_level',
    'avvia_livello':'start_level',
    'mostra_storia':'show_story',
    'nuova_domanda':'new_question',
    'gestisci_input':'handle_input',
    'gestisci_timeout':'handle_timeout',
    'aggiorna':'update',
    'disegna_level_complete':'draw_level_complete',
    'disegna_storia':'draw_story',
    'disegna_player_exit':'draw_player_exit',
    'disegna_gameover':'draw_gameover',
    'disegna_gameover_storia':'draw_gameover_story',
    'disegna_gameover_fisso':'draw_gameover_fixed',
    'disegna':'draw',
    'genera_operandi_addizione':'generate_addition_operands',
    'seleziona_operandi':'select_operands',
    'genera_operandi':'generate_operands',
    'genera_operandi_divisione':'generate_division_operands',
    'calcola_risultato':'calculate_result',
    'VITE_MAGO':'WIZARD_LIVES',
    'TEMPO_LIMITE_DEFAULT':'DEFAULT_TIMEOUT',
    'LIVELLI':'LEVELS',
    'mostro_tipo':'monster_type',
    'mostro_y_offset':'monster_y_offset',
    'gioco_bg':'game_bg',
    'mostri':'monsters',
    'mostro_hit_delay':'monster_hit_delay',
    'mostro_precedente':'previous_monster',
    'storia_entries':'story_entries',
    'storia_idx':'story_idx',
    'num_livelli_storia':'num_story_levels',
    'storia_is_livello':'story_is_level',
    'storia_monsters':'story_monsters',
    'storia_flying_monsters':'story_flying_monsters',
    'storia_fade_speed':'story_fade_speed',
    'storia_prossimo_bg':'story_next_bg',
    'storia_fade_alpha':'story_fade_alpha',
    'storia_fase':'story_phase',
    'storia_fade_color':'story_fade_color',
    'storia_primo_step':'story_first_step',
    'storia_testo_completo':'story_text_full',
    'storia_caratteri_mostrati':'story_characters_shown',
    'storia_tipografia_frame':'story_typing_frame',
    'storia_progresso':'story_progress',
    'config_genere':'config_gender',
    'config_storia_operazione':'config_story_operation',
    'config_per_op':'config_by_operation',
    'cfg':'config',
    'livello_iniziale':'initial_level',
    'modalita':'mode',
    'operazione':'operation',
    'somma_massima':'max_sum',
    'differenza_positiva':'positive_difference',
    'risultato_intero':'integer_result',
    'domande_totali':'total_questions',
    'domande_fatte':'questions_asked',
    'domande_livello':'questions_per_level',
    'domanda_attiva':'question_active',
    'inizio_domanda':'question_start',
    'timeout_limite':'timeout_limit',
    'tempo_limite_iniziale':'initial_timeout_limit',
    'tempi_risposta':'answer_times',
    'tempi_mostri':'monster_times',
    'tempi_boss':'boss_times',
    'blocco_corrente':'current_block',
    'coda_rinforzo':'reinforcement_queue',
    'mostro_progresso':'monster_progress',
    'mostro_x':'monster_x',
    'mostro_start_x':'monster_start_x',
    'mostro_end_x':'monster_end_x',
    'mostro_colpito':'monster_hit',
    'mostro_fade_start':'monster_fade_start',
    'boss_fase':'boss_phase',
    'boss_progresso':'boss_progress',
    'boss_domande_fatte':'boss_questions_asked',
    'boss_domande_totali':'boss_total_questions',
    'boss_colpito':'boss_hit',
    'profilo_corrente':'current_profile',
    'profili':'profiles',
    'profilo_input':'profile_input',
    'profilo_input_mode':'profile_input_mode',
    'profilo_genere_mode':'profile_gender_mode',
    'profilo_nuovo_nome':'new_profile_name',
    'config_operazione':'config_operation',
    'ritorno_gioco':'return_to_game',
    'entrata_personaggio':'character_entry',
    'entrata_personaggio_start':'character_entry_start',
    'entrata_personaggio_x':'character_entry_x',
}
string_mapping = {
    'storia':'story',
    'gioco':'game',
    'opzioni':'options',
    'opzioni_auto':'options_auto',
    'config_fisso':'config_fixed',
    'fisso':'fixed',
}

src_path = 'math-wizard.py'
out_path = 'math_wizard.py'
with tokenize.open(src_path) as f:
    source = f.read()

result_tokens = []
for tok in tokenize.generate_tokens(io.StringIO(source).readline):
    toktype, tokstr, start, end, line = tok
    if toktype == token.NAME and tokstr in mapping:
        tokstr = mapping[tokstr]
    elif toktype == token.STRING:
        try:
            value = ast.literal_eval(tokstr)
        except Exception:
            value = None
        if isinstance(value, str) and value in string_mapping:
            quote = tokstr[0]
            prefix = ''
            if tokstr[0] in 'rubfRUBF':
                prefix = tokstr[:1]
                quote = tokstr[1]
            new_value = string_mapping[value]
            tokstr = prefix + quote + new_value + quote
    result_tokens.append((toktype, tokstr))
new_source = tokenize.untokenize(result_tokens)
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(new_source)
print('Wrote', out_path)
