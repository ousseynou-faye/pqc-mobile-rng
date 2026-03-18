from software.entropy import CPUJitterSource, SensorEntropySource, EntropyPool

cpu = CPUJitterSource(
    sample_count=256,
    inner_loops=128,
    lsb_count=2,
)

sensor = SensorEntropySource(
    frame_count=128,
    lsb_count=2,
)

pool = EntropyPool(
    target_min_entropy_bits=256.0,
    target_min_symbols=512,
)

cpu_report = pool.add_chunk(cpu.collect())
sensor_report = pool.add_chunk(sensor.collect())

print("CPU report :", cpu_report)
print("Sensor report :", sensor_report)
print("Snapshot :", pool.snapshot())
print("Metadata :", pool.export_metadata())
print("Raw bytes (hex) :", pool.export_raw_bytes(32).hex())