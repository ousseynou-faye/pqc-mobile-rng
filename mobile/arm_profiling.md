# ARM profiling protocol

## Goal

Provide a reproducible profiling path for a future ARM or Android target without inventing measurements.

## Current status

The repository can export profiling metadata today, but it does not include validated measurements from a real ARM mobile device in this stage.

## Reference script

Use:

`python benchmarks/mobile_profile.py`

The script:

- detects the current machine architecture
- records environment metadata
- measures instantiate, generate, reseed, and zeroize on the Python reference path
- marks the run with `not_measured_on_arm` when the host is not a real ARM target

## Required measurements on a real target

Minimum set:

- instantiate latency
- reseed latency
- generate latency for several output sizes
- throughput
- peak Python-level memory or native memory equivalent if the future wrapper exposes it

## Suggested execution conditions

- run on physical ARM64 hardware when possible
- pin the build and Python version
- record thermal state and power mode if available
- avoid background workload spikes
- repeat enough rounds to get stable medians

## Methodology warnings

- desktop x86 results are not substitutes for ARM results
- emulators are useful for integration checks but not for credible performance claims
- Python-only timings do not predict a future JNI or NDK wrapper without dedicated measurement
