from tcgen.progress import NullPhase, Progress


def _collect():
    emitted = []
    p = Progress(total_weight=12.0, sink=lambda pct, msg: emitted.append((pct, msg)))
    return p, emitted


def test_overall_percent_is_monotonic_and_reaches_one():
    p, emitted = _collect()
    for label in ("C", "L"):  # crawler + agent, evaluate => weights 3+2+1 each = 12
        ph = p.phase(3, f"{label}:gen"); ph.update(0.5); ph.update(1.0)
        ph = p.phase(2, f"{label}:exec"); ph.update(1.0)
        ph = p.phase(1, f"{label}:judge"); ph.update(1.0)
    p.finish()
    pcts = [pct for pct, _ in emitted if pct is not None]
    assert pcts == sorted(pcts)
    assert abs(pcts[-1] - 1.0) < 1e-9
    rounded = {round(x, 4) for x in pcts}
    assert {0.25, 0.5, 0.75} <= rounded


def test_log_only_keeps_percent_none():
    p, emitted = _collect()
    ph = p.phase(1, "x")
    ph.log("just a log line")
    assert (None, "just a log line") in emitted


def test_nullphase_is_noop():
    n = NullPhase()
    assert n.update(0.5, "x") is None
    assert n.log("y") is None
