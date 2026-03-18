from software.conditioner import EntropyMixer, ToeplitzExtractor


def test_toeplitz_seed_length_formula():
    assert ToeplitzExtractor.seed_length_bits(16, 8) == 23
    assert ToeplitzExtractor.seed_length_bits(128, 256) == 383


def test_toeplitz_extraction_is_deterministic():
    raw_data = bytes.fromhex("A55A")
    seed = bytes.fromhex("00112233445566778899AABBCCDDEEFF")

    extractor_1 = ToeplitzExtractor.from_seed_bytes(
        input_bits=16,
        output_bits=8,
        seed_bytes=seed,
    )
    extractor_2 = ToeplitzExtractor.from_seed_bytes(
        input_bits=16,
        output_bits=8,
        seed_bytes=seed,
    )

    out_1 = extractor_1.extract_bytes(raw_data)
    out_2 = extractor_2.extract_bytes(raw_data)

    assert out_1 == out_2
    assert len(out_1) == 1


def test_entropy_mixer_changes_output_when_context_changes():
    mixer = EntropyMixer(toeplitz_output_bits=64, shake_output_bytes=32)
    raw_data = b"abcdef0123456789"

    result_1 = mixer.condition_raw_data(
        raw_data=raw_data,
        metadata={"source": "test"},
        personalization=b"ctx-1",
    )
    result_2 = mixer.condition_raw_data(
        raw_data=raw_data,
        metadata={"source": "test"},
        personalization=b"ctx-2",
    )

    assert result_1.seedinit != result_2.seedinit


def test_entropy_mixer_accepts_pool_like_object():
    class DummyPool:
        def export_raw_bytes(self):
            return b"hello entropy pool"

        def export_metadata(self):
            return {"accepted_chunks": 2, "ready": True}

    mixer = EntropyMixer(toeplitz_output_bits=128, shake_output_bytes=32)
    result = mixer.condition_from_pool(DummyPool(), personalization=b"demo")

    assert isinstance(result.seedinit, bytes)
    assert len(result.seedinit) == 32
    assert len(result.toeplitz_output) == 16
