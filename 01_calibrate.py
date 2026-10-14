"""
Step 1: Hardware calibration.
Measures this CPU's real achievable peak FLOPS and memory bandwidth,
so the cost model uses real numbers instead of datasheet guesses.
"""
import time
import numpy as np
import json

def calibrate_flops(size=2_000_000, inner_reps=50, reps=10):
    # Small enough to stay in L2/L3 cache so we measure compute, not memory bandwidth.
    a = np.random.rand(size).astype(np.float64)
    b = np.random.rand(size).astype(np.float64)
    c = np.empty_like(a)
    # warmup
    for _ in range(3):
        np.multiply(a, b, out=c)
        np.add(c, a, out=c)
    times = []
    for _ in range(reps):
        t0 = time.perf_counter()
        for _ in range(inner_reps):
            np.multiply(a, b, out=c)   # 1 FLOP/elem
            np.add(c, a, out=c)        # 1 FLOP/elem
        t1 = time.perf_counter()
        times.append((t1 - t0) / inner_reps)
    best = min(times)
    flops = 2 * size / best
    return flops

def calibrate_bandwidth(size=20_000_000, reps=20):
    a = np.random.rand(size).astype(np.float64)
    b = np.empty_like(a)
    for _ in range(3):
        b[:] = a
    times = []
    for _ in range(reps):
        t0 = time.perf_counter()
        b[:] = a  # read size*8 bytes, write size*8 bytes
        t1 = time.perf_counter()
        times.append(t1 - t0)
    best = min(times)
    bytes_moved = 2 * size * 8
    bandwidth = bytes_moved / best
    return bandwidth

def calibrate_sync_overhead(reps=100000):
    # Proxy for python-level function-call / lock overhead
    import threading
    lock = threading.Lock()
    t0 = time.perf_counter()
    for _ in range(reps):
        with lock:
            pass
    t1 = time.perf_counter()
    return (t1 - t0) / reps  # seconds per sync op

if __name__ == "__main__":
    print("Calibrating CPU peak FLOPS (vectorized elementwise ops)...")
    flops = calibrate_flops()
    print(f"  Measured: {flops/1e9:.2f} GFLOPS")

    print("Calibrating memory bandwidth (contiguous copy)...")
    bw = calibrate_bandwidth()
    print(f"  Measured: {bw/1e9:.2f} GB/s")

    print("Calibrating sync/lock overhead...")
    sync = calibrate_sync_overhead()
    print(f"  Measured: {sync*1e9:.1f} ns/op")

    profile = {
        "cpu_peak_flops": flops,
        "cpu_mem_bandwidth": bw,
        "cpu_sync_latency_sec": sync,
        "cores_logical": 10,
        "cores_physical": 8,
    }
    with open("hw_profile.json", "w") as f:
        json.dump(profile, f, indent=2)
    print("\nSaved hw_profile.json:")
    print(json.dumps(profile, indent=2))
