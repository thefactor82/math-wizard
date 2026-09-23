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


def test_select_three_operands_uses_pool_c_equal_to_pool_b():
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


def test_generate_three_division_operands_returns_integer_quotient():
    random.seed(11)
    pool_a = list(range(0, 101))
    pool_b = list(range(1, 6))
    for _ in range(100):
        a, b, c, fq = MODULE.generate_three_division_operands(pool_a, pool_b, deque(), integer_result=True)
        den = b * c
        if den:
            assert a % den == 0


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