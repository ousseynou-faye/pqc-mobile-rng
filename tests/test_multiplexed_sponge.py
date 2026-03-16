from software.lfsr.recurrence_sequences import RecurrenceSequence
from software.sponge.multiplexed_sponge import MultiplexedSponge


def build_sponge():
    seq_s = RecurrenceSequence(degree=8, seed=0xA5)
    seq_t = RecurrenceSequence(degree=9, seed=0x101)

    return MultiplexedSponge(
        seq_s=seq_s,
        seq_t=seq_t,
        l=4,
        rate=32,
        capacity=32,
    )


def test_absorb_blocks_runs():
    sponge = build_sponge()
    mixed = sponge.absorb_blocks([0x12, 0x34, 0x56], block_size=8)

    assert len(mixed) == 3
    assert all(isinstance(x, int) for x in mixed)


def test_squeeze_bits_length():
    sponge = build_sponge()
    sponge.absorb_blocks([0x12, 0x34], block_size=8)
    out = sponge.squeeze_bits(64)

    assert len(out) == 64
    assert all(bit in (0, 1) for bit in out)


def test_squeeze_bytes_length():
    sponge = build_sponge()
    sponge.absorb_blocks([0x12, 0x34], block_size=8)
    out = sponge.squeeze_bytes(16)

    assert isinstance(out, bytes)
    assert len(out) == 16


def test_same_input_same_output():
    sponge1 = build_sponge()
    sponge2 = build_sponge()

    sponge1.absorb_blocks([0x12, 0x34, 0x56], block_size=8)
    sponge2.absorb_blocks([0x12, 0x34, 0x56], block_size=8)

    out1 = sponge1.squeeze_bytes(16)
    out2 = sponge2.squeeze_bytes(16)

    assert out1 == out2