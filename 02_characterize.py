"""
Step 2-3: Benchmark suite + static loop characterization.

Each benchmark is characterized WITHOUT running it -- purely from its
known analytical structure (this stands in for what an IR-level pass
would extract: iteration count, FLOP count, memory traffic, arithmetic
intensity, branch/divergence ratio).
"""
import json

# N chosen per-benchmark to keep runtimes in a measurable, comparable range
BENCHMARKS = {
    "vector_add": {
        "description": "c[i] = a[i] + b[i]",
        "N": 5_000_000,
        "iterations": lambda N: N,
        "flops": lambda N: N,                  # 1 add / element
        "bytes": lambda N: 3 * N * 8,           # read a,b write c (float64)
        "branch_ratio": 0.0,
        "reuse_distance": "none (streaming)",
    },
    "dot_product": {
        "description": "sum += a[i]*b[i]",
        "N": 5_000_000,
        "iterations": lambda N: N,
        "flops": lambda N: 2 * N,               # mul + add
        "bytes": lambda N: 2 * N * 8,           # read a,b (accumulator stays in register)
        "branch_ratio": 0.0,
        "reuse_distance": "none (streaming)",
    },
    "stencil_2d": {
        "description": "5-point 2D stencil: out[i,j] = avg of 4 neighbors",
        "N": 2000,  # NxN grid
        "iterations": lambda N: (N - 2) * (N - 2),
        "flops": lambda N: 5 * (N - 2) * (N - 2),   # 4 adds + 1 mul per interior point
        "bytes": lambda N: 5 * (N - 2) * (N - 2) * 8,  # 4 reads + 1 write per interior point
        "branch_ratio": 0.0,
        "reuse_distance": "short (neighbor reuse across rows)",
    },
    "matmul": {
        "description": "C = A @ B (square NxN)",
        "N": 300,
        "iterations": lambda N: N ** 3,
        "flops": lambda N: 2 * N ** 3,          # mul+add per inner product term
        "bytes": lambda N: 3 * N * N * 8,       # A, B, C touched (lower bound, ignores reuse)
        "branch_ratio": 0.0,
        "reuse_distance": "high (rows/cols reused N times)",
    },
    "irregular_branchy_sum": {
        "description": "sum over sparse/conditional predicate: if (a[i] % 7 == 0) sum += a[i]",
        "N": 5_000_000,
        "iterations": lambda N: N,
        "flops": lambda N: N,                   # 1 conditional add (amortized)
        "bytes": lambda N: N * 8,
        "branch_ratio": 1.0,                    # every iteration branches
        "reuse_distance": "none (streaming, unpredictable branch)",
    },
}


def characterize(name, spec):
    N = spec["N"]
    iterations = spec["iterations"](N)
    flops = spec["flops"](N)
    mem_bytes = spec["bytes"](N)
    arithmetic_intensity = flops / mem_bytes  # FLOPs per byte
    return {
        "name": name,
        "description": spec["description"],
        "N": N,
        "iterations": iterations,
        "flops": flops,
        "mem_bytes": mem_bytes,
        "arithmetic_intensity": arithmetic_intensity,
        "branch_ratio": spec["branch_ratio"],
        "reuse_distance": spec["reuse_distance"],
    }


if __name__ == "__main__":
    results = {name: characterize(name, spec) for name, spec in BENCHMARKS.items()}
    with open("characterization.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"{'Benchmark':<22}{'N':>10}{'FLOPs':>14}{'Bytes':>14}{'AI (F/B)':>12}{'Branch%':>10}")
    for r in results.values():
        print(f"{r['name']:<22}{r['N']:>10}{r['flops']:>14,}{r['mem_bytes']:>14,}"
              f"{r['arithmetic_intensity']:>12.3f}{r['branch_ratio']*100:>9.0f}%")
