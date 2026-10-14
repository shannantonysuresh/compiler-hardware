"""
Step 6: Compare predicted winner vs measured winner -- the core validation metric.
"""
import json

with open("predictions.json") as f:
    preds = {p["name"]: p for p in json.load(f)}

with open("measurements.json") as f:
    meas = json.load(f)

with open("characterization.json") as f:
    charac = json.load(f)

rows = []
correct = 0
for name in preds:
    p = preds[name]
    m = meas[name]
    match = p["predicted_winner"] == m["measured_winner"]
    correct += match
    rows.append({
        "name": name,
        "arithmetic_intensity": charac[name]["arithmetic_intensity"],
        "branch_ratio": charac[name]["branch_ratio"],
        "predicted_winner": p["predicted_winner"],
        "measured_winner": m["measured_winner"],
        "match": match,
        "measured_speedup": m["speedup"],
        "t_scalar_measured": m["t_scalar_measured"],
        "t_vector_measured": m["t_vector_measured"],
    })

accuracy = correct / len(rows)

print(f"{'Benchmark':<22}{'AI':>8}{'Branch%':>9}{'Predicted':>12}{'Measured':>12}{'Match':>8}")
for r in rows:
    print(f"{r['name']:<22}{r['arithmetic_intensity']:>8.3f}{r['branch_ratio']*100:>8.0f}%"
          f"{r['predicted_winner']:>12}{r['measured_winner']:>12}{'YES' if r['match'] else 'NO':>8}")

print(f"\nSelection accuracy: {correct}/{len(rows)} = {accuracy*100:.0f}%")

with open("comparison.json", "w") as f:
    json.dump({"rows": rows, "accuracy": accuracy}, f, indent=2)
