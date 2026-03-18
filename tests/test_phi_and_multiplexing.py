from software.lfsr.recurrence_sequences import RecurrenceSequence
from software.sponge.phi_function import PhiFunction
from software.sponge.multiplexed_sequence import MultiplexedSequence


def test_phi_does_not_consume_sequence():
    s = RecurrenceSequence(degree=8, seed=0xA5)
    phi = PhiFunction(sequence_s=s, l=4)

    state_before = s.get_state()
    v1 = phi.compute()
    v2 = phi.compute()

    assert v1 == v2
    assert s.get_state() == state_before


def test_phi_with_explicit_offsets():
    s = RecurrenceSequence(degree=8, seed=0xA5)
    phi = PhiFunction(sequence_s=s, l=3, offsets=(0, 2, 5))

    value = phi.compute()
    assert isinstance(value, int)
    assert 0 <= value < (1 << 3)


def test_phi_msb_first_flag_changes_bit_assembly_only():
    s_msb = RecurrenceSequence(degree=8, seed=0xA5)
    s_lsb = RecurrenceSequence(degree=8, seed=0xA5)

    phi_msb = PhiFunction(sequence_s=s_msb, l=4, msb_first=True)
    phi_lsb = PhiFunction(sequence_s=s_lsb, l=4, msb_first=False)

    assert phi_msb.compute() == 0b1010
    assert phi_lsb.compute() == 0b0101


def test_multiplexed_sequence_uses_t_n_plus_phi():
    s = RecurrenceSequence(degree=8, seed=0xA5)
    t = RecurrenceSequence(degree=9, seed=0x101)

    s_ref = s.clone()
    t_ref = t.clone()

    phi = PhiFunction(sequence_s=s_ref, l=4)
    shift = phi.compute()
    expected = t_ref.peek_bit(shift % t_ref.period)

    u = MultiplexedSequence(seq_s=s, seq_t=t, l=4)
    got = u.next_bit()

    assert got == expected


def test_multiplexed_sequence_advances_one_step_only():
    s = RecurrenceSequence(degree=8, seed=0xA5)
    t = RecurrenceSequence(degree=9, seed=0x101)

    u = MultiplexedSequence(seq_s=s, seq_t=t, l=4)

    state_s_before = s.get_state()
    state_t_before = t.get_state()

    _ = u.next_bit()

    assert s.get_state() != state_s_before
    assert t.get_state() != state_t_before
