"""Run a small local Doppel benchmark without requiring an AI service.

Examples:
    python scripts/benchmark.py
    python scripts/benchmark.py --model models/encoder.onnx --backend cpu,qnn
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from app.ai.onnx_runtime import OnnxModelRunner, detect_runtime
from app.benchmark.runner import BenchmarkRunner, results_to_json
from app.memory.embeddings import LocalTextEmbedder


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark local Doppel inference paths")
    parser.add_argument("--model", type=Path, help="Optional fixed-shape ONNX model")
    parser.add_argument("--backend", default="cpu", help="Comma-separated backends: cpu,qnn,npu")
    parser.add_argument("--iterations", type=int, default=20)
    args = parser.parse_args()
    runner = BenchmarkRunner()
    if not args.model:
        embedder = LocalTextEmbedder()
        results = runner.compare({"local-embedding-cpu": lambda: embedder.embed("resume the API integration task")}, args.iterations)
        print(results_to_json(results))
        return 0
    status = detect_runtime()
    print(f"Runtime: {status.message}; providers={','.join(status.providers) or 'none'}")
    operations = {}
    for backend in [item.strip().lower() for item in args.backend.split(",") if item.strip()]:
        if backend in {"qnn", "npu"} and not status.qnn_available:
            print(f"Skipping {backend}: QNNExecutionProvider is unavailable")
            continue
        model = OnnxModelRunner(args.model, backend=backend, allow_cpu_fallback=False)
        input_name = model.input_names()[0]
        try:
            import numpy as np  # type: ignore[import-not-found]
        except ImportError as error:
            raise SystemExit("Install numpy to benchmark an ONNX model") from error
        operations[backend] = lambda model=model, input_name=input_name: model.run({input_name: np.zeros((1, 1), dtype=np.float32)})
    if operations:
        print(results_to_json(runner.compare(operations, args.iterations)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
