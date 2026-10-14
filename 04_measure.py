"""
Step 5: Actually execute both code variants for each benchmark and
measure real wall-clock time. This is the ground truth we compare
the cost model's predictions against.
"""
import time
import json
import numpy as np

REPS = 3


def timeit(fn, reps=REPS):
    times = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        times.append(t1 - t0)
    return min(times)


# ---------- vector_add ----------
def vector_add_scalar(N):
    a = list(range(N))
    b = list(range(N))
    c = [0] * N
    for i in range(N):
        c[i] = a[i] + b[i]

def vector_add_vector(N):
    a = np.arange(N, dtype=np.float64)
    b = np.arange(N, dtype=np.float64)
    c = a + b

# ---------- dot_product ----------
def dot_product_scalar(N):
    a = list(range(N))
    b = list(range(N))
    s = 0.0
    for i in range(N):
        s += a[i] * b[i]

def dot_product_vector(N):
    a = np.arange(N, dtype=np.float64)
    b = np.arange(N, dtype=np.float64)
    s = np.dot(a, b)

# ---------- stencil_2d ----------
def stencil_2d_scalar(N):
    a = [[1.0] * N for _ in range(N)]
    out = [[0.0] * N for _ in range(N)]
    for i in range(1, N - 1):
        for j in range(1, N - 1):
            out[i][j] = 0.25 * (a[i-1][j] + a[i+1][j] + a[i][j-1] + a[i][j+1])

def stencil_2d_vector(N):
    a = np.ones((N, N), dtype=np.float64)
    out = 0.25 * (a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:])

# ---------- matmul ----------
def matmul_scalar(N):
    A = [[1.0] * N for _ in range(N)]
    B = [[1.0] * N for _ in range(N)]
    C = [[0.0] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            s = 0.0
            for k in range(N):
                s += A[i][k] * B[k][j]
            C[i][j] = s

def matmul_vector(N):
    A = np.ones((N, N), dtype=np.float64)
    B = np.ones((N, N), dtype=np.float64)
    C = A @ B

# ---------- irregular_branchy_sum ----------
def irregular_branchy_sum_scalar(N):
    a = list(range(N))
    s = 0
    for i in range(N):
        if a[i] % 7 == 0:
            s += a[i]

def irregular_branchy_sum_vector(N):
    a = np.arange(N, dtype=np.int64)
    mask = (a % 7 == 0)
    s = a[mask].sum()


BENCH_FUNCS = {
    "vector_add": (vector_add_scalar, vector_add_vector, 5_000_000),
    "dot_product": (dot_product_scalar, dot_product_vector, 5_000_000),
    "stencil_2d": (stencil_2d_scalar, stencil_2d_vector, 2000),
    "matmul": (matmul_scalar, matmul_vector, 300),
    "irregular_branchy_sum": (irregular_branchy_sum_scalar, irregular_branchy_sum_vector, 5_000_000),
}

if __name__ == "__main__":
    results = {}
    print(f"{'Benchmark':<22}{'T_scalar(s)':>14}{'T_vector(s)':>14}{'Speedup':>10}{'Measured winner':>18}")
    for name, (scalar_fn, vector_fn, N) in BENCH_FUNCS.items():
        # matmul_scalar at N=300 is ~27M python-level iterations -- genuinely slow, that's expected and real.
        t_scalar = timeit(lambda: scalar_fn(N), reps=1 if name == "matmul" else REPS)
        t_vector = timeit(lambda: vector_fn(N))
        winner = "vector" if t_vector < t_scalar else "scalar"
        speedup = t_scalar / t_vector
        results[name] = {
            "t_scalar_measured": t_scalar,
            "t_vector_measured": t_vector,
            "speedup": speedup,
            "measured_winner": winner,
        }
        print(f"{name:<22}{t_scalar:>14.6f}{t_vector:>14.6f}{speedup:>9.1f}x{winner:>18}")

    with open("measurements.json", "w") as f:
        json.dump(results, f, indent=2)
