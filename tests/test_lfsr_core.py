from software.lfsr.lfsr_core import LFSR
from software.lfsr.recurrence_sequences import RecurrenceSequence


def test_zero_seed_is_rejected():
    try:
        LFSR(degree=8, seed=0)
        assert False, "Le seed nul aurait du etre refuse."
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


def test_generate_block_bit_order_is_explicit():
    seq_msb = RecurrenceSequence(degree=8, seed=0xA5)
    seq_lsb = RecurrenceSequence(degree=8, seed=0xA5)

    block_msb = seq_msb.generate_block(4, msb_first=True)
    block_lsb = seq_lsb.generate_block(4, msb_first=False)

    assert block_msb == 0b1010
    assert block_lsb == 0b0101
