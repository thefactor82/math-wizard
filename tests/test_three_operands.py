import importlib.util
import random
from collections import deque
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "math-wizard.py"
SPEC = importlib.util.spec_from_file_location("mathwizard_main", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_calculate_result3_covers_all_operations():
    assert MODULE.calculate_result3(5, 3, 6, "addizione") == 14
    assert MODULE.calculate_result3(9, 3, 2, "sottrazione") == 4
    assert MODULE.calculate_result3(2, 3, 4, "moltiplicazione") == 24
    assert MODULE.calculate_result3(24, 2, 3, "divisione") == 4
    assert MODULE.calculate_result3(24, 2, 3, "divisione", integer_result=False) == 4.0
    assert MODULE.calculate_result3(10, 0, 3, "divisione") == 0


def test_needs_carry3_and_needs_borrow3():
    assert MODULE.needs_carry3(18, 7, 9) is True
    assert MODULE.needs_carry3(1, 2, 3) is False
    assert MODULE.needs_borrow3(32, 4, 5) is True
    assert MODULE.needs_borrow3(15, 1, 3) is False


def test_select_three_operands_respects_bounds_and_signs():
    random.seed(7)
    pool_a = list(range(0, 11))
    pool_b = list(range(0, 11))
    for _ in range(200):
        # addizione con somma massima e riporto forzato/non
        for need in (False, True):
            prob = 1.0 if need else 0.0
            a, b, c, fb, fq = MODULE.select_three_operands(
                pool_a, pool_b, deque(), "addizione", max_sum=15,
                min_value=0, max_value=199, carry_prob=prob
            )
            assert a + b + c <= 15
            assert MODULE.needs_carry3(a, b, c) == need, (a, b, c)
        # sottrazione: risultato non negativo tramite risultato minimo e prestito rispettato
        for need in (False, True):
            prob = 1.0 if need else 0.0
            a, b, c, fb, fq = MODULE.select_three_operands(
                pool_a, pool_b, deque(), "sottrazione", min_value=0,
                max_value=199, borrow_prob=prob
            )
            assert a - b - c >= 0
            assert MODULE.needs_borrow3(a, b, c) == need, (a, b, c)
        # moltiplicazione: risultato nel range
        a, b, c, fb, fq = MODULE.select_three_operands(
            pool_a, pool_b, deque(), "moltiplicazione", min_value=5,
            max_value=90, max_sum=None
        )
        res = MODULE.calculate_result3(a, b, c, "moltiplicazione")
        assert 5 <= res <= 90
        # divisione: risultato intero quando richiesto
        a, b, c, fb, fq = MODULE.select_three_operands(
            pool_a, pool_b, deque(), "divisione", integer_result=True,
            min_value=0, max_value=199
        )
        if b != 0 and c != 0:
            assert a % (b * c) == 0
            assert MODULE.calculate_result3(a, b, c, "divisione") >= 0


def test_select_three_operands_uses_pool_c_equal_to_pool_b_or_explicit():
    random.seed(3)
    pool_a = list(range(0, 11))
    pool_b = list(range(5, 8))
    for _ in range(100):
        a, b, c, fb, fq = MODULE.select_three_operands(
            pool_a, pool_b, deque(), "addizione", max_sum=30
        )
        assert c in pool_b
        assert a in pool_a
        assert b in pool_b
    random.seed(3)
    pool_c = list(range(11, 19))
    for _ in range(100):
        a, b, c, fb, fq = MODULE.select_three_operands(
            pool_a, pool_b, deque(), "addizione", max_sum=30, pool_c=pool_c
        )
        assert c in pool_c
        assert a in pool_a
        assert b in pool_b


def test_generate_three_division_operands_returns_integer_quotient():
    random.seed(11)
    pool_a = list(range(0, 101))
    pool_b = list(range(1, 6))
    for _ in range(100):
        a, b, c, fq = MODULE.generate_three_division_operands(pool_a, pool_b, deque(), integer_result=True)
        den = b * c
        if den:
            assert a % den == 0


def test_generate_three_division_operands_uses_pool_c_for_third_operand():
    random.seed(41)
    pool_a = list(range(0, 101))
    pool_b = list(range(1, 4))
    pool_c = list(range(4, 9))
    for _ in range(100):
        a, b, c, fq = MODULE.generate_three_division_operands(
            pool_a, pool_b, deque(), integer_result=True, pool_c=pool_c
        )
        den = b * c
        if den:
            assert a % den == 0
        assert c in pool_c or (b == 1 and c == 1)


def test_format_wrong_entry_shows_three_operands():
    segno = MODULE.get_operation_symbol("addizione")
    assert MODULE.format_wrong_entry(5, 3, 6, "addizione", 14) == f"5{segno}3{segno}6=14"
    assert MODULE.format_wrong_entry(5, 3, None, "addizione", 8) == f"5{segno}3=8"
    assert MODULE.format_wrong_entry(5, 3, 6, "addizione", None) == f"5{segno}3{segno}6=(nessuna risposta)"


def test_risultato_minimo_negativo_permette_sottrazioni_negative():
    random.seed(5)
    pool_a = list(range(0, 11))
    pool_b = list(range(0, 11))
    seen_negative = False
    for _ in range(300):
        # due operandi: risultato minimo sotto zero -> risultato anche negativo
        a, b, fb, fq = MODULE.select_operands(
            pool_a, pool_b, deque(), "sottrazione", min_value=-30,
            max_value=199
        )
        res = a - b
        assert -30 <= res
        if res < 0:
            seen_negative = True
    assert seen_negative
    random.seed(5)
    seen_negative3 = False
    for _ in range(300):
        # tre operandi: risultato minimo sotto zero -> risultato anche negativo
        a, b, c, fb, fq = MODULE.select_three_operands(
            pool_a, pool_b, deque(), "sottrazione", min_value=-30,
            max_value=199
        )
        res3 = a - b - c
        assert -30 <= res3
        if res3 < 0:
            seen_negative3 = True
    assert seen_negative3


def test_risultato_minimo_negativo_con_prestito_zero_produce_comunque_negativi():
    # con prestito 0% la selezione evita i prestiti; un risultato negativo
    # richiede comunque un "prestito" e quindi esce solo con prestito attivo
    random.seed(21)
    pool_a = list(range(0, 51))
    pool_b = list(range(0, 51))
    seen_negative = False
    for _ in range(400):
        a, b, fb, fq = MODULE.select_operands(
            pool_a, pool_b, deque(), "sottrazione", min_value=-40,
            max_value=199, borrow_prob=1.0
        )
        res = a - b
        assert -40 <= res
        assert MODULE.needs_borrow(a, b) is True
        if res < 0:
            seen_negative = True
    assert seen_negative


def test_risultato_minimo_zero_mantiene_risultati_non_negativi():
    random.seed(9)
    pool_a = list(range(0, 101))
    pool_b = list(range(0, 101))
    for _ in range(300):
        a, b, fb, fq = MODULE.select_operands(
            pool_a, pool_b, deque(), "sottrazione", min_value=0,
            max_value=199, borrow_prob=0.5
        )
        assert a - b >= 0


MIXED_CFG = {
    "moltiplicazione": {"risultato_minimo": 0, "risultato_massimo": 100,
                        "pool_a": list(range(0, 51)), "pool_b": list(range(1, 26)), "pool_c": list(range(1, 41))},
    "addizione": {"risultato_minimo": 0, "risultato_massimo": 100, "somma_massima": 100, "riporto": 0,
                  "pool_a": list(range(0, 51)), "pool_b": list(range(1, 26)), "pool_c": list(range(1, 41))},
    "sottrazione": {"risultato_minimo": -50, "risultato_massimo": 100, "prestito": 0,
                    "pool_a": list(range(0, 51)), "pool_b": list(range(1, 26)), "pool_c": list(range(1, 41))},
    "divisione": {"risultato_minimo": 0, "risultato_massimo": 100,
                  "pool_a": list(range(2, 51)), "pool_b": list(range(1, 26)), "pool_c": list(range(1, 41))},
}


def test_mixed_result_precedence():
    assert MODULE.mixed_result(2, "moltiplicazione", 4, "addizione", 6) == 14
    assert MODULE.mixed_result(2, "addizione", 4, "moltiplicazione", 6) == 26
    assert MODULE.mixed_result(8, "divisione", 2, "addizione", 3) == 7
    assert MODULE.mixed_result(12, "addizione", 3, "divisione", 3) == 13
    assert MODULE.mixed_result(2, "addizione", 3, "sottrazione", 1) == 4
    assert MODULE.mixed_result(8, "divisione", 2, "moltiplicazione", 4) == 16
    assert MODULE.mixed_result(3, "moltiplicazione", 4, "divisione", 2) == 6


def test_mixed3_steps_order():
    res, steps = MODULE.mixed3_steps(2, "moltiplicazione", 4, "addizione", 6)
    assert res == 14
    assert steps[0][0] == "moltiplicazione" and steps[0][3] == 8
    assert steps[1][0] == "addizione" and steps[1][3] == 14
    res, steps = MODULE.mixed3_steps(2, "addizione", 4, "moltiplicazione", 6)
    assert res == 26
    assert steps[0][0] == "moltiplicazione" and steps[0][3] == 24
    assert steps[1][0] == "addizione" and steps[1][3] == 26


def test_format_wrong_entry_mixed():
    assert MODULE.format_wrong_entry_mixed(2, 4, 6, "moltiplicazione", "addizione", 14) == "2x4+6=14"
    assert MODULE.format_wrong_entry_mixed(2, 4, 6, "addizione", "moltiplicazione", None) == "2+4x6=(nessuna risposta)"


def test_select_mixed_pair_respects_bounds_and_exact_division():
    random.seed(13)
    for _ in range(200):
        a, b, op, fb, fq = MODULE.select_mixed_pair(
            deque(),
            ["moltiplicazione", "addizione", "sottrazione", "divisione"],
            MIXED_CFG,
        )
        res = MODULE.apply_operation(a, b, op)
        lo, hi = MODULE._mixed_bounds(MIXED_CFG, (op,))
        assert lo <= res <= hi, (a, b, op)
        if op == "divisione":
            assert b != 0 and a % b == 0


def test_select_mixed_triple_precedence_and_exact_division():
    random.seed(17)
    for _ in range(300):
        a, b, c, op1, op2, fb, fq = MODULE.select_mixed_triple(
            deque(),
            ["moltiplicazione", "addizione", "sottrazione", "divisione"],
            MIXED_CFG,
        )
        res = MODULE.mixed_result(a, op1, b, op2, c)
        lo, hi = MODULE._mixed_bounds(MIXED_CFG, (op1, op2))
        assert lo <= res <= hi, (a, op1, b, op2, c)
        for step_op, left, right, _sr in MODULE.mixed3_steps(a, op1, b, op2, c)[1]:
            if step_op == "divisione":
                assert right != 0 and left % right == 0


def test_select_mixed_pair_uses_only_selected_ops():
    random.seed(19)
    for _ in range(150):
        a, b, op, fb, fq = MODULE.select_mixed_pair(
            deque(), ["sottrazione", "moltiplicazione"], MIXED_CFG
        )
        assert op in ("sottrazione", "moltiplicazione")


def test_select_mixed_triple_pure_add_respects_somma_massima():
    random.seed(23)
    pool = list(range(0, 10))
    cfg = dict(MIXED_CFG)
    cfg["addizione"] = dict(cfg["addizione"], somma_massima=20,
                            pool_a=pool, pool_b=pool, pool_c=pool)
    for _ in range(200):
        a, b, c, op1, op2, fb, fq = MODULE.select_mixed_triple(
            deque(), ["addizione"], cfg
        )
        assert op1 == op2 == "addizione"
        assert a + b + c <= 20


def test_mixed_pair_uses_op_pools():
    random.seed(37)
    cfg = {
        "moltiplicazione": {"risultato_minimo": 0, "risultato_massimo": 100000,
                            "pool_a": [5], "pool_b": [7]},
        "addizione": {"risultato_minimo": 0, "risultato_massimo": 100000, "somma_massima": 100000,
                      "riporto": 0, "pool_a": [7], "pool_b": [2]},
    }
    seen = set()
    for _ in range(100):
        a, b, op, fb, fq = MODULE.select_mixed_pair(deque(), ["moltiplicazione", "addizione"], cfg)
        assert (a, b, op) in {((5, 7, "moltiplicazione")), ((7, 2, "addizione"))}, (a, b, op)
        seen.add((a, b, op))
    assert seen == {(5, 7, "moltiplicazione"), (7, 2, "addizione")}, seen


def test_mixed_triple_operands_from_per_op_pools():
    random.seed(31)
    cfg = {
        "moltiplicazione": {"risultato_minimo": 0, "risultato_massimo": 100000,
                            "pool_a": [2], "pool_b": [3], "pool_c": [4]},
        "addizione": {"risultato_minimo": 0, "risultato_massimo": 100000, "somma_massima": 100000,
                      "riporto": 0, "pool_a": [10], "pool_b": [6], "pool_c": [1]},
    }
    expected = {
        ("moltiplicazione", "moltiplicazione"): (2, 3, 4),
        ("moltiplicazione", "addizione"): (2, 3, 1),
        ("addizione", "moltiplicazione"): (10, 3, 4),
        ("addizione", "addizione"): (10, 6, 1),
    }
    seen = set()
    for _ in range(300):
        a, b, c, op1, op2, fb, fq = MODULE.select_mixed_triple(
            deque(), ["moltiplicazione", "addizione"], cfg
        )
        assert (a, b, c) == expected[(op1, op2)], (a, op1, b, op2, c)
        seen.add((op1, op2))
    assert seen == set(expected), seen


def test_mixed_triple_b_from_higher_precedence_pool():
    random.seed(41)
    cfg = dict(MIXED_CFG)
    pool_b_by_op = {"moltiplicazione": [22], "divisione": [6], "addizione": [55], "sottrazione": [77]}
    for op, pb in pool_b_by_op.items():
        cfg[op] = dict(cfg[op], pool_b=pb)
    ok = 0
    for _ in range(400):
        a, b, c, op1, op2, fb, fq = MODULE.select_mixed_triple(
            deque(), ["moltiplicazione", "addizione", "sottrazione", "divisione"], cfg
        )
        owner = op1 if MODULE._mixed_weight(op1) <= MODULE._mixed_weight(op2) else op2
        if fb and owner == "divisione":
            continue
        ok += 1
        assert b == pool_b_by_op[owner][0], (a, op1, b, op2, c, owner, fb)
    assert ok > 0


def test_challenge_difficulty_step_depends_on_total():
    assert MODULE.challenge_difficulty_step(50) == 1
    assert MODULE.challenge_difficulty_step(100) == 2


def test_challenge_level_index_ramps_and_clamps():
    assert MODULE.challenge_level_index(0, 50, 50) == 0
    assert MODULE.challenge_level_index(1, 50, 50) == 1
    assert MODULE.challenge_level_index(49, 50, 50) == 49
    assert MODULE.challenge_level_index(0, 100, 50) == 0
    assert MODULE.challenge_level_index(1, 100, 50) == 0
    assert MODULE.challenge_level_index(2, 100, 50) == 1
    assert MODULE.challenge_level_index(98, 100, 50) == 49
    assert MODULE.challenge_level_index(80, 50, 45) == 44
    assert MODULE.challenge_level_index(10, 100, 45) == 5
    assert MODULE.challenge_level_index(0, 50, 0) == 0


def test_challenge_report_payload_fields():
    payload = MODULE.build_challenge_report(
        "Luca", "abc123", "M", "addizione", 50, 45, 5, 3.14159, 157.07963, "1.4.6",
        created_at="2026-01-02T03:04:05",
    )
    assert payload == {
        "created_at": "2026-01-02T03:04:05",
        "name": "Luca",
        "uuid": "abc123",
        "character": "M",
        "operation": "addizione",
        "questions_total": 50,
        "correct": 45,
        "wrong": 5,
        "average_time": 3.14,
        "total_time": 157.08,
        "version": "1.4.6",
    }


def test_post_challenge_report_without_url_is_graceful():
    ok, message = MODULE.post_challenge_report("", {"name": "x"})
    assert ok is False
    assert "non configurata" in message


def test_challenge_constants_match_spec():
    assert MODULE.CHALLENGE_TIMEOUT == 12
    assert MODULE.CHALLENGE_TOTAL_OPTIONS == (50, 100)
    assert MODULE.WIZARD_LIVES == 3


def _challenge_game(operation, total=50):
    game = MODULE.Game()
    game.current_profile = "TestSfida"
    game.plus_unlocked = True
    game.challenge_operation = operation
    game.challenge_total = total
    game.start_challenge()
    game.state = MODULE.GAME_STATE_GAME
    game.start_level()
    game.character_entry = False
    if game.level_scene_before:
        game.start_scene(game.level_scene_before, "question")
        game.finish_scene()
    else:
        game.new_question()
    return game


def test_challenge_fallback_does_not_use_fixed_only_attributes():
    # il fallback per operands ripetuti deve usare i pool del livello Sfida,
    # non gli attributi che esistono solo in modalita' fixed (max_sum, pool_a)
    for operation in ("moltiplicazione", "addizione", "sottrazione", "divisione"):
        game = _challenge_game(operation)
        assert not hasattr(game, "max_sum"), operation
        for _ in range(8):
            if game.lives <= 0:
                break
            game.prev_a, game.prev_b, game.prev_c = game.a, game.b, game.c
            game._from_queue = False
            game._prev_from_queue = False
            game.questions_asked += 1
            game.new_question()
            assert game.a is not None and game.b is not None, operation
            if operation == "sottrazione":
                assert game.a >= game.b, (game.a, game.b)
            assert game.expected_result == MODULE.calculate_result(
                game.a, game.b, operation, game.integer_result
            ), (game.a, game.b, game.expected_result)