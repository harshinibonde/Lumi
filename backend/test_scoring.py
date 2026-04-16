"""PART 8 — Validate the upgraded scoring system."""

import sys
sys.path.insert(0, ".")

from rapidfuzz import fuzz
from screening_router import _auto_score, _fuzzy_match

# Mock session
session_A = {"registration_set": "A", "attention_variant": "serial_7s"}
session_B = {"registration_set": "A", "attention_variant": "world_backwards"}

print("=" * 60)
print("PART 8: SCORING VALIDATION TESTS")
print("=" * 60)

passed = 0
failed = 0

def test(name, actual, expected):
    global passed, failed
    status = "PASS" if actual == expected else "FAIL"
    if status == "FAIL":
        failed += 1
        print(f"  [FAIL] {name} -> got {actual}, expected {expected}")
    else:
        passed += 1
        print(f"  [OK]   {name} -> {actual}")

# --- Task 3: Registration (fuzzy) ---
print("\n--- Task 3: Registration ---")
test("exact words", _auto_score(3, "apple table penny", session_A), 3)
test("typo: appel", _auto_score(3, "appel table penny", session_A), 3)
test("typo: pennie", _auto_score(3, "apple tabel pennie", session_A), 3)
test("only 1 correct", _auto_score(3, "apple banana elephant", session_A), 1)
test("blank", _auto_score(3, "", session_A), 0)
test("random words", _auto_score(3, "dog cat fish", session_A), 0)

# --- Task 4: Attention (serial 7s with tolerance) ---
print("\n--- Task 4: Attention (Serial 7s) ---")
test("exact", _auto_score(4, "93, 86, 79, 72, 65", session_A), 5)
test("off by 1", _auto_score(4, "93, 85, 79, 72, 65", session_A), 5)  # 85 is ±1 from 86
test("two wrong", _auto_score(4, "93, 84, 79, 72, 65", session_A), 4)  # 84 is ±2 from 86
test("blank", _auto_score(4, "", session_A), 0)

# --- Task 4: Attention (WORLD backwards) ---
print("\n--- Task 4: Attention (WORLD backwards) ---")
test("exact DLROW", _auto_score(4, "DLROW", session_B), 5)
test("d l r o w", _auto_score(4, "d l r o w", session_B), 5)
test("dlrow lowercase", _auto_score(4, "dlrow", session_B), 5)
test("partial DLRO", _auto_score(4, "DLRO", session_B), 4)

# --- Task 5: Recall (fuzzy) ---
print("\n--- Task 5: Recall ---")
test("exact", _auto_score(5, "apple table penny", session_A), 3)
test("typo: appel", _auto_score(5, "appel tabl penny", session_A), 3)
test("blank", _auto_score(5, "", session_A), 0)

# --- Task 6: Naming (synonyms + fuzzy) ---
print("\n--- Task 6: Naming ---")
test("exact: pencil watch", _auto_score(6, "pencil, watch", session_A), 2)
test("synonym: pen clock", _auto_score(6, "pen, clock", session_A), 2)
test("synonym: wristwatch", _auto_score(6, "pencil, wristwatch", session_A), 2)
test("typo: pencl", _auto_score(6, "pencl, watch", session_A), 2)
test("only pencil", _auto_score(6, "pencil", session_A), 1)
test("blank", _auto_score(6, "", session_A), 0)
test("wrong objects", _auto_score(6, "chair, table", session_A), 0)

# --- Task 7: Repetition (fuzzy) ---
print("\n--- Task 7: Repetition ---")
test("exact", _auto_score(7, "No ifs, ands, or buts.", session_A), 1)
test("close match", _auto_score(7, "no ifs and or buts", session_A), 1)
test("minor typo", _auto_score(7, "no ifs ands or buds", session_A), 1)
test("blank", _auto_score(7, "", session_A), 0)
test("wrong sentence", _auto_score(7, "hello world foo bar", session_A), 0)

print(f"\n{'=' * 60}")
print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed}")
print(f"{'=' * 60}")
