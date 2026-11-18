def calc_aeiou(s) -> list[str]:
    return [e for e in s if e in 'aeiouAEIOU']


print(calc_aeiou('Hellow Python!'))# ['e', 'o', 'o']


def calc_score(scores: list[float]) -> float:
    return round(sum(scores) / len(scores), 1)


avg_score = calc_score([66, 77, 88.5, 99])
print(f"avg_score: {avg_score}")  # avg_score: 82.6
