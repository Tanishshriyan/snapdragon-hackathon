"""Optional ONNX Runtime and Qualcomm QNN execution support.

+The package is deliberately imported lazily. The base MVP remains runnable
without ONNX Runtime, while a Windows ARM64 installation of ``onnxruntime-qnn``
can select ``QNNExecutionProvider`` with the HTP backend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    package_available: bool
    package_name: str | None
    version: str | None
    providers: tuple[str, ...]
    qnn_available: bool
    npu_available: bool
    message: str


def detect_runtime() -> RuntimeStatus:
    """Inspect the installed ONNX Runtime package without creating a session."""

    try:
        import onnxruntime as ort  # type: ignore[import-not-found]
    except ImportError:
        return RuntimeStatus(False, None, None, (), False, False, "ONNX Runtime is not installed")
    providers = tuple(ort.get_available_providers())
    qnn = "QNNExecutionProvider" in providers
    return RuntimeStatus(
        True,
        getattr(ort, "__package__", "onnxruntime"),
        getattr(ort, "__version__", None),
        providers,
        qnn,
        qnn,
        "QNN provider available" if qnn else "CPU provider available; QNN provider is not installed",
    )


@dataclass(frozen=True, slots=True)
class InferenceResult:
    outputs: tuple[Any, ...]
    backend: str
    provider: str


class OnnxModelRunner:
    """Run a fixed-shape ONNX model on CPU or QNN when available."""

    def __init__(
        self,
        model_path: str | Path,
        backend: str = "cpu",
        backend_path: str | Path | None = None,
        allow_cpu_fallback: bool = True,
    ) -> None:
        self.model_path = Path(model_path).expanduser().resolve()
        self.backend = backend.lower()
        self.backend_path = str(backend_path) if backend_path else None
        self.allow_cpu_fallback = allow_cpu_fallback
        self._session: Any = None
        self._provider = "CPUExecutionProvider"

    @property
    def provider(self) -> str:
        return self._provider

    def _create_session(self) -> Any:
        if self._session is not None:
            return self._session
        if not self.model_path.exists():
            raise FileNotFoundError(self.model_path)
        try:
            import onnxruntime as ort  # type: ignore[import-not-found]
        except ImportError as error:
            raise RuntimeError("Install onnxruntime or onnxruntime-qnn to run an ONNX model") from error

        options = ort.SessionOptions()
        providers = ["CPUExecutionProvider"]
        provider_options: list[dict[str, str]] = [{}]
        if self.backend in {"qnn", "npu"}:
            available = set(ort.get_available_providers())
            if "QNNExecutionProvider" not in available:
                if not self.allow_cpu_fallback:
                    raise RuntimeError("QNNExecutionProvider is unavailable on this machine")
            else:
                providers = ["QNNExecutionProvider"]
                options.add_session_config_entry("session.disable_cpu_ep_fallback", "1" if not self.allow_cpu_fallback else "0")
                qnn_options = {"backend_path": self.backend_path or ("QnnHtp.dll" if self.backend == "npu" else "QnnCpu.dll")}
                provider_options = [qnn_options]
        self._session = ort.InferenceSession(self.model_path.as_posix(), sess_options=options, providers=providers, provider_options=provider_options)
        actual = tuple(self._session.get_providers())
        self._provider = actual[0] if actual else providers[0]
        return self._session

    def run(self, inputs: Mapping[str, Any], output_names: list[str] | None = None) -> InferenceResult:
        session = self._create_session()
        outputs = tuple(session.run(output_names, dict(inputs)))
        return InferenceResult(outputs, self.backend, self._provider)

    def input_names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self._create_session().get_inputs())
