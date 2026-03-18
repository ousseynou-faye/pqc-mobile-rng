from software.entropy import (
    CPUJitterSource,
    EntropyPool,
    HealthEstimator,
    SensorEntropySource,
    SensorFrame,
)


def test_cpu_jitter_collect_returns_expected_shape():
    src = CPUJitterSource(sample_count=64, inner_loops=64, lsb_count=2)
    chunk = src.collect()

    assert chunk.source_name == "cpu_jitter"
    assert chunk.sample_count == 64
    assert chunk.symbol_bits == 2
    assert len(chunk.raw_bytes) > 0
    assert all(0 <= value < 4 for value in chunk.symbols)


def test_sensor_collect_from_frames_is_stable():
    frames = [
        SensorFrame(ax=10, ay=11, az=12, gx=13, gy=14, gz=15, timestamp_ns=1),
        SensorFrame(ax=20, ay=21, az=22, gx=23, gy=24, gz=25, timestamp_ns=2),
    ]

    src = SensorEntropySource(frame_count=2, lsb_count=2)
    chunk = src.collect_from_frames(frames)

    assert chunk.source_name == "inertial_sensors"
    assert chunk.sample_count == 12
    assert chunk.symbol_bits == 2
    assert chunk.metadata["frame_count"] == 2


def test_health_estimator_rejects_frozen_sequence():
    estimator = HealthEstimator(repetition_limit=8, adaptive_window_size=16, adaptive_max_proportion=0.75)

    symbols = [0] * 64
    report = estimator.evaluate_symbols(symbols, symbol_bits=2, source_name="frozen")

    assert report.accepted is False
    assert report.repetition_count_ok is False


def test_entropy_pool_can_become_ready_with_small_thresholds():
    cpu = CPUJitterSource(sample_count=64, inner_loops=32, lsb_count=2)
    sensor = SensorEntropySource(frame_count=16, lsb_count=2)

    pool = EntropyPool(
        target_min_entropy_bits=8.0,
        target_min_symbols=32,
    )

    pool.add_chunk(cpu.collect())
    pool.add_chunk(sensor.collect())

    snapshot = pool.snapshot()

    assert snapshot.total_symbols >= 32
    assert snapshot.total_raw_bytes > 0