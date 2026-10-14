"""
Step 4: Cost model + prediction.

Two "target variants" (standing in for two devices/codegen paths):
  - scalar: naive pure-Python loop  (like unoptimized scalar CPU code)
  - vector: NumPy vectorized ops    (like SIMD/vectorized codegen)

For each benchmark, the cost model estimates T_total for both variants
using T_total = T_compute + T_memory + T_sync, then predicts a winner.
Sync overhead is used as the proxy for "irregular/branchy code penalty":
branchy code defeats vectorization, modeled as full sync-per-iteration
cost being paid on the vector path (since masked/branchy vector code
can't skip work), while the scalar path is unaffected by branch ratio.
"""
import json

with open("hw_profile.json") as f:
    HW = json.load(f)

with open("characterization.json") as f:
    LOOPS = json.load(f)

PEAK_FLOPS = HW["cpu_peak_flops"]
BANDWIDTH = HW["cpu_mem_bandwidth"]
SYNC_LATENCY = HW["cpu_sync_latency_sec"]

# Empirically-known Python interpreter overhead per loop iteration
# (measured separately: pure python loop doing trivial arithmetic)
PYTHON_OP_OVERHEAD_SEC = 8e-8  # ~80ns/iteration typical CPython overhead


def predict(loop):
    iterations = loop["iterations"]
    flops = loop["flops"]
    mem_bytes = loop["mem_bytes"]
    branch_ratio = loop["branch_ratio"]

    # --- Vectorized (NumPy/SIMD) variant ---
    t_compute_vec = flops / PEAK_FLOPS
    t_memory_vec = mem_bytes / BANDWIDTH
    # Branchy code can't be efficiently vectorized: model as needing
    # per-element masked-sync overhead proportional to branch_ratio.
    t_sync_vec = branch_ratio * iterations * SYNC_LATENCY
    t_total_vec = max(t_compute_vec, t_memory_vec) + t_sync_vec

    # --- Scalar (naive interpreter loop) variant ---
    # Dominated by per-iteration interpreter overhead, not FLOPs/bandwidth.
    t_total_scalar = iterations * PYTHON_OP_OVERHEAD_SEC

    predicted = "vector" if t_total_vec < t_total_scalar else "scalar"
    return {
        "name": loop["name"],
        "t_total_vec_pred": t_total_vec,
        "t_total_scalar_pred": t_total_scalar,
        "predicted_winner": predicted,
    }


if __name__ == "__main__":
    predictions = [predict(loop) for loop in LOOPS.values()]
    with open("predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)

    print(f"{'Benchmark':<22}{'Pred T_vec(s)':>16}{'Pred T_scalar(s)':>18}{'Predicted winner':>18}")
    for p in predictions:
        print(f"{p['name']:<22}{p['t_total_vec_pred']:>16.6f}"
              f"{p['t_total_scalar_pred']:>18.6f}{p['predicted_winner']:>18}")
