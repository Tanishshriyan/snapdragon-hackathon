def test_application_startup_and_monitoring_lifecycle(service):
    assert service.engine is not None
    service.start_monitoring()
    service.poll()
    assert service.is_monitoring is True
    service.shutdown()
    assert service.is_monitoring is False

