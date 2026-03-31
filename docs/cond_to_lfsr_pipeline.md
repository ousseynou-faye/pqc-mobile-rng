# COND to LFSR Pipeline

## 1. Purpose

This document isolates the exact software path that links the conditioner
output to the two recurrence sequences used by the Multiplexed Sponge
prototype.

The goal is to make explicit, in one place, how the project moves from:

```text
raw entropy -> conditioning -> seedinit -> seed_s / seed_t -> S_n / T_n
```

without changing the mathematical definition:

```text
u_n = t_{n + phi(l, n)}
```

## 2. End-to-end view

```text
[Entropy Sources]
    |
    v
[Entropy Pool / Raw Data]
    |
    v
[Conditioner: Toeplitz + SHAKE-256]
    |
    v
[ConditioningResult.seedinit]
    |
    v
[MultiplexedSpongeAdapter.instantiate(seed_material=seedinit)]
    |
    v
[Internal sponge seed_digest = SHAKE-256("sponge_init:" || personalization || seedinit)]
    |
    v
[derive_sponge_lfsr_seeds(seed_digest)]
   / \
  v   v
[seed_s] [seed_t]
   |       |
   v       v
[RecurrenceSequence S_n]   [RecurrenceSequence T_n]
          |
          v
[PhiFunction on S_n]
          |
          v
[u_n = t_{n + phi(l, n)}]
          |
          v
[Multiplexed Sponge]
          |
          v
[DRBG output bytes]
```

## 3. Software path

### 3.1 SRC

The canonical service builds entropy in `software/api/rng_service.py`:

- `RNGService._build_entropy_pool()`
- `CPUJitterSource.collect()`
- `SensorEntropySource.collect()`
- `EntropyPool.add_chunk(...)`

This produces the accepted raw bytes returned by `pool.export_raw_bytes()`.

### 3.2 COND

Conditioning is handled by `software/conditioner/entropy_mixer.py`:

- `EntropyMixer.condition_from_pool(...)`
- `EntropyMixer.condition_raw_data(...)`

The conditioner performs:

1. context construction via `build_context_info(...)`
2. Toeplitz public seed derivation via `derive_toeplitz_seed(...)`
3. Toeplitz extraction via `ToeplitzExtractor.from_seed_bytes(...).extract_bytes(...)`
4. final seed derivation via `ShakeConditioner.derive_seed(...)`

The canonical output is `ConditioningResult.seedinit`.

### 3.3 DRBG bridge

The bridge into the Multiplexed Sponge happens in two stages.

First stage, in `software/api/rng_service.py`:

- `RNGService.instantiate_rng(...)`
- calls `drbg.instantiate(result.seedinit, ...)`

Second stage, in `software/pqc_drbg/sponge_core.py`:

- `MultiplexedSpongeAdapter.instantiate(...)`
- computes `self._seed_digest = SHAKE-256("sponge_init:" || personalization || seed_material)`
- then calls `_build_instance_from_digest(self._seed_digest)`
- which uses `build_reference_sponge(seed_digest)`

In the nominal path, `seed_material` is exactly `ConditioningResult.seedinit`.

### 3.4 Explicit derivation of `seed_s` and `seed_t`

The dedicated module is `software/sponge/seed_derivation.py`.

It exposes:

- `derive_lfsr_seed(...)`
- `derive_sponge_lfsr_seeds(...)`

Properties of the derivation:

- deterministic
- reproducible
- domain-separated
- degree-aware
- non-zero by construction

The domain separation is explicit:

- `SEQ_S` for `S_n`
- `SEQ_T` for `T_n`

The reduction rule is:

```text
candidate = SHAKE-256(payload)
seed = (candidate mod (2^degree - 1)) + 1
```

So the derived state always stays in:

```text
[1, 2^degree - 1]
```

and the all-zero LFSR state is impossible.

### 3.5 Construction of `S_n` and `T_n`

`software/pqc_drbg/sponge_core.py::build_reference_sponge(...)` performs:

1. `derived = derive_sponge_lfsr_seeds(seed_digest, degree_s=16, degree_t=16, context=b"build_reference_sponge")`
2. `seq_s = RecurrenceSequence(degree=16, seed=derived.seed_s)`
3. `seq_t = RecurrenceSequence(degree=16, seed=derived.seed_t)`
4. `sponge = MultiplexedSponge(seq_s=seq_s, seq_t=seq_t, l=4, rate=128, capacity=128)`

These two sequences are therefore the ones actually injected into the
Multiplexed Sponge used by the nominal DRBG engine.

## 4. Phi and multiplexing

`software/sponge/phi_function.py` defines `PhiFunction`.

It reads only from `sequence_s` and uses `peek_bits(...)` or `peek_bit(...)`,
so it is non-destructive.

`software/sponge/multiplexed_sequence.py` defines `MultiplexedSequence`.

Its `next_bit()` method keeps the prototype relation exact:

```text
shift = phi.compute()
bit = seq_t.peek_bit(shift % seq_t.period)
seq_s.advance(1)
seq_t.advance(1)
return bit
```

This is the operational implementation of:

```text
u_n = t_{n + phi(l, n)}
```

with non-destructive preview and one-step advancement of both source
sequences after each produced multiplexed bit.

## 5. Sponge usage

`software/sponge/multiplexed_sponge.py` wires:

- `MultiplexedSequence`
- `SpongeAbsorb`
- `SpongeSqueeze`
- `SpongeState`

Absorption:

- `SpongeAbsorb.absorb_block(...)`
- generates one multiplexed block
- XORs it with the input block
- absorbs the result
- permutes the state

Squeeze:

- `SpongeSqueeze.squeeze_block(...)`
- reads one block from the sponge rate part
- XORs it with one multiplexed block
- permutes the state

So the same `S_n` / `T_n` lineage influences both absorb and squeeze phases.

## 6. What is and is not directly fed by COND

Important distinction:

- the canonical conditioner output is `seedinit`
- the LFSR seeds are not derived directly from raw entropy
- they are derived from the internal `seed_digest` built by the sponge DRBG
  adapter from `seedinit`

So the effective chain is:

```text
seedinit -> seed_digest -> seed_s / seed_t
```

This is still a valid canonical branch from COND into the two LFSR sequences,
because `seed_digest` is deterministically and exclusively derived from
`seedinit` in the nominal sponge engine path.

## 7. Current limits

- `build_reference_sponge(...)` fixes `degree_s=16`, `degree_t=16`, `l=4`,
  `rate=128` and `capacity=128` in code
- this is an explicit prototype baseline, not a configurable family yet
- the prototype still adds an internal absorb pre-mix derived from
  `shake_256(b"rng-service-sponge:" + seed_digest)` after sequence creation
- the academic prototype uses deterministic software sources and derivations;
  it is not a formal cryptographic proof

## 8. Tests that cover this path

- `tests/test_conditioner_layer.py`
  validates the conditioner and `seedinit` production
- `tests/test_lfsr_core.py`
  validates non-zero seeds and non-destructive preview semantics
- `tests/test_phi_and_multiplexing.py`
  validates `phi()` non-destructiveness and `u_n = t_{n + phi(l,n)}`
- `tests/test_multiplexed_sponge.py`
  validates absorb/squeeze behaviour
- `tests/test_rng_service.py`
  validates canonical service instantiation and reseed
- `tests/test_end_to_end_pipeline.py`
  validates the baseline `SRC -> COND -> DRBG -> STATE`
- `tests/test_sponge_seed_derivation.py`
  validates the explicit bridge from canonical seed material to `S_n` and `T_n`

## 9. Recommended commands

```powershell
venv\Scripts\pytest.exe tests\test_conditioner_layer.py
venv\Scripts\pytest.exe tests\test_lfsr_core.py
venv\Scripts\pytest.exe tests\test_phi_and_multiplexing.py tests\test_multiplexed_sponge.py
venv\Scripts\pytest.exe tests\test_sponge_seed_derivation.py
venv\Scripts\pytest.exe tests\test_rng_service.py tests\test_pqc_drbg_complete.py tests\test_end_to_end_pipeline.py
```
