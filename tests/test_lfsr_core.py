from software.lfsr.lfsr_core import LFSR
from software.lfsr.recurrence_sequences import RecurrenceSequence


def test_zero_seed_is_rejected():
    try:
        LFSR(degree=8, seed=0)
        assert False, "Le seed nul aurait dû être refusé."
    except ValueError:
        assert True


def test_peek_bit_does_not_modify_state():
    lfsr = LFSR(degree=8, seed=0xA5)
    state_before = lfsr.state
    _ = lfsr.peek_bit(5)
    assert lfsr.state == state_before


def test_peek_bits_match_clone_generation():
    seq = RecurrenceSequence(degree=8, seed=0xA5)
    ref = seq.clone()

    expected = [ref.next_bit() for _ in range(16)]
    got = seq.peek_bits(16)

    assert got == expected
    assert seq.get_state() == 0xA5


def test_generate_block_returns_integer():
    seq = RecurrenceSequence(degree=8, seed=0xA5)
    block = seq.generate_block(8, msb_first=True)
    assert isinstance(block, int)
    assert 0 <= block <= 0xFF