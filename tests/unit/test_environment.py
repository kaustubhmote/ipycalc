from __future__ import annotations

from ipycalc.environment import validate_current


def test_validate_current_accepts_an_empty_import_set() -> None:
    report = validate_current(())

    assert report.valid
    assert report.missing == ()


def test_validate_current_reports_every_missing_import() -> None:
    report = validate_current(("module_that_does_not_exist_one", "module_that_does_not_exist_two"))

    assert not report.valid
    assert report.missing == (
        "module_that_does_not_exist_one",
        "module_that_does_not_exist_two",
    )
    assert len(report.errors) == 2

