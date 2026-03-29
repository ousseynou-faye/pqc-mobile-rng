# Mobile reseed policy

## Scope

This is a cautious mobile trajectory policy.
It is compatible with the current Python prototype but is not presented as a final production policy.

## Principles

- keep explicit reseed support at the binary boundary
- do not rely on long-lived state without refresh
- prefer conservative thresholds until real mobile measurements exist
- treat restore, corruption, and integrity anomalies as high-risk events

## Recommended events

Reseed should be triggered on:

- initial instantiate if fresh entropy is available
- app resume after suspension
- process restart with state restoration
- device unlock after a long suspend
- integrity anomaly or health downgrade
- explicit administrative request

## Quantitative thresholds

Recommended provisional thresholds for the future native/mobile side:

- after `1 MiB` generated since the last reseed
- after `1024` generate requests
- after `15 minutes` of wall-clock time since last successful reseed
- immediately after a restore event before serving new application bytes

These thresholds are intentionally conservative.
They still need calibration on a real mobile target.

## Entropy input strategy

The current Python baseline uses:

- CPU jitter source
- simulated sensor entropy source
- Toeplitz + SHAKE-256 conditioner

For a future mobile implementation, complementary entropy should come from the platform source available on device, for example:

- Android Keystore or system RNG feed
- Linux `getrandom()` or equivalent kernel RNG service
- trusted platform or secure element facilities when actually available

This repository does not claim that those sources are already integrated.

## Restore and failure handling

If a future mobile wrapper restores state:

- mark the instance as requiring reseed before normal generation
- reject generation if reseed cannot be completed

If corruption or tampering is suspected:

- enter fail-stop
- require explicit reinitialization
- do not silently continue with degraded confidence

## Current limitation

The public Python SDK already has reseed support, but it does not yet enforce the full mobile event model above.
This document defines the target operational policy for the mobile trajectory, not a claim that all triggers are already wired into the executable baseline.
