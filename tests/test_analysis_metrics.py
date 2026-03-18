from analysis.bit_metrics import compute_bit_balance
from analysis.generators import bits_from_object
from analysis.golomb_checks import compute_golomb_indicators
from analysis.linear_complexity import berlekamp_massey_linear_complexity
from analysis.period_metrics import estimate_observed_period
from analysis.report import build_bit_sequence_report, build_sponge_report
from analysis.run_metrics import compute_run_metrics
from software.lfsr.recurrence_sequences import RecurrenceSequence
from software.sponge.multiplexed_sponge import MultiplexedSponge


def build_sponge():
    seq_s = RecurrenceSequence(degree=8, seed=0xA5)
    seq_t = RecurrenceSequence(degree=9, seed=0x101)
    return MultiplexedSponge(seq_s=seq_s, seq_t=seq_t, l=4, rate=32, capacity=32)


def test_bit_balance_on_simple_sample():
    metrics = compute_bit_balance([0, 1, 1, 0])

    assert metrics["count_0"] == 2
    assert metrics["count_1"] == 2
    assert metrics["frequency_0"] == 0.5
    assert metrics["frequency_1"] == 0.5


def test_run_metrics_on_simple_sample():
    metrics = compute_run_metrics([1, 1, 0, 0, 0, 1])

    assert metrics["total_runs"] == 3
    assert metrics["longest_run"] == 3
    assert metrics["run_counts_by_length"][1] == 1
    assert metrics["run_counts_by_length"][2] == 1
    assert metrics["run_counts_by_length"][3] == 1


def test_observed_period_detects_repetition():
    metrics = estimate_observed_period([1, 0, 1, 0, 1, 0, 1, 0])

    assert metrics["observed_period"] == 2


def test_linear_complexity_returns_structured_result():
    metrics = berlekamp_massey_linear_complexity([1, 0, 0, 1, 1, 0, 1, 0])

    assert metrics["length"] == 8
    assert 0 <= metrics["linear_complexity"] <= 8
    assert 0.0 <= metrics["normalized_linear_complexity"] <= 1.0


def test_bits_from_object_with_recurrence_sequence():
    sequence = RecurrenceSequence(degree=8, seed=0xA5)
    reference = sequence.clone()
    bits = bits_from_object(sequence, 8)

    assert bits == reference.generate_sequence(8)


def test_golomb_indicators_return_expected_keys():
    indicators = compute_golomb_indicators([1, 0, 1, 0, 1, 0, 1, 0])

    assert "balance_gap" in indicators
    assert "run_count_gap" in indicators
    assert "empirical_run_profile" in indicators


def test_bit_sequence_report_is_structured():
    report = build_bit_sequence_report([1, 0, 1, 0, 1, 0, 1, 0], max_period=4)

    assert report["sample_length"] == 8
    assert report["observed_period"]["observed_period"] == 2
    assert "bit_balance" in report
    assert "linear_complexity" in report


def test_sponge_report_runs_after_absorption():
    sponge = build_sponge()
    report = build_sponge_report(sponge, n_bits=32, absorb_blocks=[0x12, 0x34], block_size=8)

    assert report["sample_length"] == 32
    assert report["source"] == "multiplexed_sponge"
    assert report["bit_balance"]["length"] == 32
