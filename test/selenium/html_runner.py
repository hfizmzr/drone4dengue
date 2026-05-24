"""
html_runner.py
──────────────
Compatibility shim for html-testRunner 1.2.1 on Python 3.13+.

Python 3.13 removed TestResult._count_relevant_tb_levels; html-testRunner
still calls it inside addFailure(), causing:

    AttributeError: 'HtmlTestResult' object has no attribute
    '_count_relevant_tb_levels'. Did you mean: '_is_relevant_tb_level'?

This module monkey-patches the missing method back onto HtmlTestResult
before returning a pre-configured HTMLTestRunner instance.

Usage (in any test file):
    from html_runner import make_runner
    ...
    if __name__ == "__main__":
        runner = make_runner("TC-XX-YYY-SlugName", "TP-XX | Report Title")
        runner.run(suite)
"""

import os

import HtmlTestRunner
from HtmlTestRunner import result as _html_result

# Always write reports to the project-root test-reports/ folder, regardless
# of the working directory from which the test script is invoked.
_REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "test-reports")


def _patch_html_test_result() -> None:
    """Add _count_relevant_tb_levels if the Python version removed it."""
    if hasattr(_html_result.HtmlTestResult, "_count_relevant_tb_levels"):
        return  # already present — nothing to do

    def _count_relevant_tb_levels(self, tb):          # type: ignore[override]
        """Reimplementation removed in Python 3.13."""
        length = 0
        while tb and self._is_relevant_tb_level(tb):
            length += 1
            tb = tb.tb_next
        return length

    _html_result.HtmlTestResult._count_relevant_tb_levels = (  # type: ignore[attr-defined]
        _count_relevant_tb_levels
    )


def make_runner(report_name: str, report_title: str) -> HtmlTestRunner.HTMLTestRunner:
    """
    Apply the Python 3.13 compatibility patch and return a ready-to-use
    HTMLTestRunner that writes HTML reports into the test-reports/ directory.
    """
    _patch_html_test_result()
    return HtmlTestRunner.HTMLTestRunner(
        output=_REPORTS_DIR,
        report_name=report_name,
        report_title=report_title,
        descriptions=True,
        combine_reports=True,
        open_in_browser=False,
    )
