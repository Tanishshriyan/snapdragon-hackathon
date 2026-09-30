from app.ai.onnx_runtime import detect_runtime
from app.benchmark.runner import BenchmarkRunner
from app.resume.launcher import LaunchTarget, WorkspaceLauncher


def test_semantic_memory_and_local_reasoning_are_wired(service):
    service.remember_memory("The API integration needs a small retry test", memory_type="work_note")
    hits = service.search_memory("retry test for API integration")

    assert hits
    assert "retry" in hits[0].memory.text
    explanation = service.explain_current_context()
    assert explanation.text
    assert explanation.provider in {"local-demo-reasoner", "llama-cpp-local"}


def test_allowlisted_resume_launcher_supports_dry_run():
    launcher = WorkspaceLauncher([LaunchTarget("Editor", "editor.exe", ("project",))])
    results = launcher.launch_names(["Editor"], dry_run=True)

    assert results[0].started is True
    assert "editor.exe project" in results[0].message


def test_benchmark_reports_latency_and_explicit_power_boundary():
    result = BenchmarkRunner().run("small-operation", lambda: sum(range(20)), iterations=3, warmups=1)

    assert result.latency_ms_median >= 0
    assert result.iterations == 3
    assert "not available" in result.power_measurement


def test_onnx_runtime_detection_is_safe_without_optional_package():
    status = detect_runtime()

    assert isinstance(status.providers, tuple)
    assert status.npu_available == status.qnn_available
