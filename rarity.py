# ============================================================
# RARITY DETECTOR
# ============================================================
import re

PATTERNS = {
    "R4": [r"(\d)\1{3,}", 5],
    "R3": [r"(\d)\1\1(\d)\2\2", 4],
    "S5": [r"(12345|23456|34567|45678|56789)", 6],
    "S4": [r"(0123|1234|2345|3456|4567|5678|6789|9876|8765|7654|6543|5432|4321|3210)", 5],
    "P6": [r"^(\d)(\d)(\d)\3\2\1$", 7],
    "P4": [r"^(\d)(\d)\2\1$", 5],
    "SPH": [r"(69|420|1337|007)", 6],
    "SPM": [r"(100|200|300|400|500|666|777|888|999)", 4],
    "QD": [r"(1111|2222|3333|4444|5555|6666|7777|8888|9999|0000)", 6],
    "MH": [r"^(\d{2,3})\1$", 5],
    "MM": [r"(\d{2})0\1", 4],
    "GD": [r"1618|0618", 5],
    "PAIR3": [r"(\d)\1(\d)\2(\d)\3", 3],
    "PAIRX": [r"(\d)\1.*(\d)\2.*(\d)\3", 2],
    "ALT": [r"(\d)(\d)\1\2\1\2", 3],
    "ALT8": [r"(\d)(\d)\1\2\1\2\1\2", 4],
    "TAIL0": [r"0{4,}$", 3],
    "HEAD1": [r"^1{2,}", 2],
    "BLOCK": [r"(\d{2,3})\1{1,}", 4],
    "STEP2": [r"(13579|2468|8642|97531)", 4],
    "MIX": [r"(55|66|77|88|99){2,}", 3],
    "ULTRA_R4": [r"(\d)\1{5,}", 10],
    "ULTRA_PAL": [r"^(\d)(\d)(\d)\2\1$", 8],
    "ULTRA_MIRROR": [r"^(\d{3})(\d{3})\1$", 9],
    "ULTRA_SEQ": [r"(012345|123456|234567|345678|456789|987654|876543|765432|654321)", 8],
    "ULTRA_QUAD": [r"(\d{4})\1", 8],
    "ULTRA_BINARY": [r"^[01]+$", 7],
    "ULTRA_REPEAT": [r"(\d{2})\1\1", 7],
}

THRESHOLD = 6


def check_rarity(account_id):
    if not account_id or account_id == "N/A":
        return "NORMAL", [], 0, ""

    score = 0
    patterns_found = []

    for ptype, (pattern, pts) in PATTERNS.items():
        try:
            if re.search(pattern, str(account_id)):
                score += pts
                patterns_found.append(ptype)
        except Exception:
            pass

    aid = str(account_id)
    digits = [int(d) for d in aid if d.isdigit()]
    dc = len(digits)

    if dc > 0 and len(set(digits)) == 1 and dc >= 4:
        b = min(dc * 2, 12)
        score += b
        patterns_found.append(f"UNIFORM(+{b})")

    if dc >= 4:
        diffs = [digits[i+1] - digits[i] for i in range(len(digits)-1)]
        if len(set(diffs)) == 1:
            b = min(abs(diffs[0]) * 2, 10)
            score += b
            patterns_found.append(f"ARITH(+{b})")

    if len(aid) <= 8 and aid.isdigit():
        try:
            iv = int(aid)
            if iv < 1000000:
                score += 8
                patterns_found.append("LOW_ID(<1M)")
            elif iv < 10000000:
                score += 5
                patterns_found.append("LOW_ID(<10M)")
            elif iv < 100000000:
                score += 3
                patterns_found.append("LOW_ID(<100M)")
        except Exception:
            pass

    if aid.isdigit() and len(aid) > 0:
        score += 2
        patterns_found.append("CLEAN_DIGIT")

    if len(aid) >= 3 and aid == aid[::-1]:
        score += 6
        patterns_found.append("PALINDROME")

    if "888" in aid or "999" in aid:
        score += 5
        patterns_found.append("TRIPLE_EIGHT_NINE")

    if "0000" in aid:
        score += 7
        patterns_found.append("QUAD_ZUY")

    if len(aid) >= 4 and dc >= 2:
        try:
            rising = all(digits[i] < digits[i+1] for i in range(len(digits)-1))
            sinking = all(digits[i] > digits[i+1] for i in range(len(digits)-1))
            if rising or sinking:
                b = min(len(digits) * 2, 10)
                score += b
                patterns_found.append(f"RISE_SINK(+{b})")
        except Exception:
            pass

    if score >= THRESHOLD:
        if score >= 20:
            rarity = "LEGENDARY"
        elif score >= 16:
            rarity = "MYTHIC"
        elif score >= 12:
            rarity = "EPIC"
        else:
            rarity = "RARE"
        reason = f"Score:{score} | {','.join(patterns_found[:10])}"
        return rarity, patterns_found, score, reason

    return "NORMAL", patterns_found, score, ""
