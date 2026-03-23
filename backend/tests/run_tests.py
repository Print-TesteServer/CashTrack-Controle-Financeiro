import json
import io
import sys
import time
import unittest
from collections import defaultdict
from pathlib import Path


def _module_to_file(module_name: str) -> str:
    return f"{module_name.replace('.', '/')}.py"


class StructuredTextResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.entries: list[dict] = []
        self._started_at: float | None = None

    def startTest(self, test):
        self._started_at = time.perf_counter()
        super().startTest(test)

    def _duration_ms(self) -> float:
        if self._started_at is None:
            return 0.0
        return round((time.perf_counter() - self._started_at) * 1000, 2)

    def _build_entry(self, test, status: str, error: str | None = None) -> dict:
        module_name = test.__class__.__module__
        return {
            "id": test.id(),
            "file": _module_to_file(module_name),
            "module": module_name,
            "class": test.__class__.__name__,
            "test": test._testMethodName,
            "description": test.shortDescription(),
            "status": status,
            "duration_ms": self._duration_ms(),
            "error": error,
        }

    def addSuccess(self, test):
        super().addSuccess(test)
        self.entries.append(self._build_entry(test, "passed"))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.entries.append(self._build_entry(test, "failed", self._exc_info_to_string(err, test)))

    def addError(self, test, err):
        super().addError(test, err)
        self.entries.append(self._build_entry(test, "error", self._exc_info_to_string(err, test)))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.entries.append(self._build_entry(test, "skipped", reason))

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.entries.append(
            self._build_entry(test, "expected_failure", self._exc_info_to_string(err, test))
        )

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.entries.append(self._build_entry(test, "unexpected_success"))

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is None:
            self.entries.append(
                self._build_entry(
                    test,
                    "subtest_passed",
                    f"subtest={subtest.params!r}" if hasattr(subtest, "params") else str(subtest),
                )
            )
        else:
            self.entries.append(
                self._build_entry(test, "subtest_failed", self._exc_info_to_string(err, test))
            )


class StructuredTextRunner(unittest.TextTestRunner):
    resultclass = StructuredTextResult


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    if max_len <= 3:
        return text[:max_len]
    return text[: max_len - 3] + "..."


def _format_table_row(values: list[str], widths: list[int]) -> str:
    cells = [f" {value.ljust(width)} " for value, width in zip(values, widths)]
    return "|" + "|".join(cells) + "|"


def _build_console_dashboard(report_data: dict) -> str:
    summary = report_data["summary"]
    entries = sorted(report_data["tests"], key=lambda item: item["duration_ms"], reverse=True)
    by_file: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        by_file[entry["file"]].append(entry)

    lines: list[str] = []
    lines.append("")
    lines.append("=" * 100)
    lines.append("TEST DASHBOARD")
    lines.append("=" * 100)
    lines.append(
        "Total: {ran} | Passed: {passed} | Failed: {failed} | Errors: {errors} | "
        "Skipped: {skipped} | Success: {successful}".format(**summary)
    )
    lines.append("")

    headers = ["STATUS", "TEST", "DURATION", "DESCRIPTION"]
    widths = [10, 54, 10, 20]
    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"

    for file_name in sorted(by_file):
        file_entries = by_file[file_name]
        file_total = len(file_entries)
        file_passed = sum(1 for item in file_entries if item["status"] == "passed")
        file_non_passed = file_total - file_passed
        lines.append(
            f"FILE: {file_name} | tests={file_total} | passed={file_passed} | non_passed={file_non_passed}"
        )
        lines.append(border)
        lines.append(_format_table_row(headers, widths))
        lines.append(border)
        for item in file_entries:
            test_name = f"{item['class']}.{item['test']}"
            description = item["description"] or "-"
            lines.append(
                _format_table_row(
                    [
                        item["status"].upper(),
                        _truncate(test_name, widths[1]),
                        f"{item['duration_ms']:.2f} ms",
                        _truncate(description, widths[3]),
                    ],
                    widths,
                )
            )
        lines.append(border)
        lines.append("")

    lines.append("SLOWEST TESTS")
    lines.append("-" * 100)
    for index, item in enumerate(entries[:5], start=1):
        lines.append(
            f"{index:>2}. {item['duration_ms']:.2f} ms  {item['class']}.{item['test']} ({item['file']})"
        )
    lines.append("=" * 100)
    return "\n".join(lines) + "\n"


def _build_human_report(report_data: dict) -> str:
    summary = report_data["summary"]
    entries = report_data["tests"]
    by_file: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        by_file[entry["file"]].append(entry)

    lines: list[str] = []
    lines.append("TEST DASHBOARD")
    lines.append("=" * 80)
    lines.append(
        "Total: {ran} | Passed: {passed} | Failed: {failed} | Errors: {errors} | "
        "Skipped: {skipped} | Success: {successful}".format(**summary)
    )
    lines.append("")

    for file_name in sorted(by_file):
        file_entries = by_file[file_name]
        file_total = len(file_entries)
        file_passed = sum(1 for item in file_entries if item["status"] == "passed")
        file_non_passed = file_total - file_passed
        lines.append(
            f"FILE: {file_name} | tests={file_total} | passed={file_passed} | non_passed={file_non_passed}"
        )
        for item in file_entries:
            description = item["description"] or "-"
            lines.append(
                f"  - [{item['status']}] {item['class']}.{item['test']} ({item['duration_ms']} ms)"
            )
            lines.append(f"    desc: {description}")
            if item["error"]:
                first_error_line = item["error"].splitlines()[0] if item["error"].splitlines() else "-"
                lines.append(f"    error: {first_error_line}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    backend_root = Path(__file__).resolve().parent.parent
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(backend_root / "tests"), pattern="test_*.py")
    runner = StructuredTextRunner(stream=io.StringIO(), verbosity=0)
    result = runner.run(suite)

    report_path = backend_root / "test-report.json"
    report_data = {
        "summary": {
            "ran": result.testsRun,
            "passed": len(result.entries)
            - len(result.failures)
            - len(result.errors)
            - len(result.skipped)
            - len(result.expectedFailures)
            - len(result.unexpectedSuccesses),
            "failed": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "expected_failures": len(result.expectedFailures),
            "unexpected_successes": len(result.unexpectedSuccesses),
            "successful": result.wasSuccessful(),
        },
        "tests": result.entries,
    }
    report_path.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")
    human_report_path = backend_root / "test-report.txt"
    human_report_path.write_text(_build_human_report(report_data), encoding="utf-8")
    print(_build_console_dashboard(report_data), end="")
    print(f"Structured report generated at: {report_path}")
    print(f"Human-readable report generated at: {human_report_path}")

    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
