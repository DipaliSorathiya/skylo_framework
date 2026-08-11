# MSG3 Automation & Quality Framework

A lightweight Python automation framework covering **MSG3 log analysis, API validation, and CI quality gating**.

The framework is designed around reusable components rather than independent scripts: the MSG3 analyzer is consumed directly by the quality gate, while optional trend analysis remains isolated from the core implementation.

---

## What It Covers

| Area               | Implementation                           |
| ------------------ | ---------------------------------------- |
| **Part 1**         | MSG3 log parsing + success-rate analysis |
| **Part 2**         | NASA Close-Approach API automation       |
| **Part 3**         | Parameterized CI quality gate            |
| **Bonus**          | Hourly trend + degradation detection     |
| **Reporting**      | Console + JSON + pytest HTML report      |
| **CI**             | GitHub Actions                           |
| **Test Framework** | pytest                                   |

---

## Quick Start

From the repository root:

```bash
./run.sh
```

Run the complete test suite directly:

```bash
python -m pytest -v
```

---

## Architecture

```text
                    ┌──────────────┐
                    │   Log File   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  LogParser   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Msg3Analyzer │
                    └──────┬───────┘
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
          ReportGenerator       QualityGate
                 │                   │
          Console / JSON       PASS / FAIL
```

The bonus trend analysis reuses the parsed records independently:

```text
LogParser → HourlyTrendAnalyzer → Hourly Rates → Degradation Windows
```

This keeps optional functionality from changing the core analyzer.

---

## Project Structure

```text
analyzer/     # Parsing, analysis, reporting and trend analysis
api/          # Reusable API client and API tests
gate/         # CI quality-gate implementation
tests/        # Unit and integration tests
logs/         # Supplied read-only log files
reports/      # Generated JSON reports
.github/      # GitHub Actions workflow
run.sh        # Single-command execution
```

---

# Part 1 — MSG3 Analyzer

### Success Rate

```text
Success Rate (%) =
    successes / (successes + failures) × 100
```

The log file is selected at runtime:

```bash
python -m analyzer.cli --log logs/bs_log.txt
```

```bash
python -m analyzer.cli --log logs/bs_log2.txt
```

### Results

| Log           | Records | Success | Failure | Ignored |       Rate |
| ------------- | ------: | ------: | ------: | ------: | ---------: |
| `bs_log.txt`  |      35 |       9 |      26 |       0 | **25.71%** |
| `bs_log2.txt` |     451 |     409 |      42 |       0 | **90.69%** |

Reports are generated as:

```text
reports/msg3_report.json
```

### Parsing

The parser handles:

* different log formats
* multi-line MSG3 entries
* irrelevant/unrecognized lines
* ANSI/control characters
* unknown statuses
* empty input

The parser produces reusable `Msg3Record` objects consumed by the analyzer and quality gate.

---

# Part 2 — API Automation

The framework validates NASA's public Close-Approach Data API.

The API layer separates HTTP communication from test assertions.

Coverage includes:

* successful responses
* response structure
* expected fields
* non-empty data
* query-parameter behavior
* negative/boundary validation

Run:

```bash
python -m pytest -v api/test_api.py
```

---

# Part 3 — Quality Gate

The quality gate directly reuses the Part 1 analyzer.

```text
Log → Parser → Analyzer → Success Rate → Threshold → PASS / FAIL
```

Example:

```bash
python -m gate.cli \
    --log logs/bs_log2.txt \
    --min-rate 95
```

Result:

```text
Success Rate : 90.69%
Minimum Rate : 95.00%
Gate Status  : FAIL
```

The process exits with a **non-zero exit code**, allowing CI to fail the build.

The boundary is inclusive:

```text
success_rate >= minimum_threshold → PASS
```

---

# Bonus — Trend & Degradation Analysis

Hourly success rates can be analyzed independently:

```bash
python -m analyzer.trend_cli \
    --log logs/bs_log2.txt \
    --degradation-threshold 10
```

The analyzer reports:

* hourly success rates
* measurable hourly outcomes
* significant percentage-point drops
* degradation windows

The threshold is configurable and the feature is isolated from the core Part 1 CLI.




## Stretch Items

In addition to the core requirements, the following stretch items were implemented.

### Completed

- **Reporting:** The MSG3 analyzer produces human-readable console output and a machine-readable JSON report at `reports/msg3_report.json`.
- **CI:** A GitHub Actions workflow is included under `.github/workflows/`.
- **Hourly Trend Analysis:** MSG3 success rates can be calculated for individual hourly time buckets.
- **Degradation Detection:** A configurable percentage-point threshold identifies significant drops in hourly success rate.
- **Extended API Automation:** The API suite contains **10 automated scenarios**, covering positive and negative cases, CRUD operations, query parameters, response validation, and error/boundary behavior.
- **Additional Test Coverage:** Parser, analyzer, quality-gate, and trend-analysis edge cases are covered beyond the minimum scenarios.
- **AI Usage Documentation:** `AI_USAGE.md` documents how AI was used during development and how suggestions were verified.

### Reproducing the Stretch Features

Run the complete automated suite:

```bash
python -m pytest -v

---

# Questions & Assumptions

### Status Classification

**Success**

```text
success
```

**Failure**

```text
failure
timeout
crc-error
crc_error
failed
reject
rejected
```

**Ignored**

```text
unknown
pending
ignored
```

Only measurable success/failure outcomes contribute to the denominator.

### Repeated Attempts

Each parsed MSG3 attempt is counted independently. Records are **not deduplicated by RNTI**, because the metric measures MSG3 attempt success rate rather than unique-device success rate.

### "Recent" Activity

The specification does not define a concrete recency window. The selected log file is therefore treated as the analysis window; no arbitrary time filter is applied.

### Empty Data

No measurable records results in a `0.0%` success rate. This ensures an empty/unusable input cannot accidentally pass a positive CI threshold.

### Hourly Time

Hourly trend analysis preserves the timestamp representation from the source log and does not apply an implicit timezone conversion.

---

# Validation

The framework is validated through:

```bash
python -m pytest -v
```

and execution against both supplied log files.

CI execution is provided through GitHub Actions.

---

# Stretch Work

### Completed

* [x] JSON reporting
* [x] GitHub Actions CI
* [x] Hourly success-rate trend
* [x] Degradation detection
* [x] Parameterized degradation threshold
* [x] Additional edge-case tests
* [x] AI usage documentation


---

## Design Principles

The framework emphasizes:

**Reuse** — Part 3 consumes Part 1 rather than duplicating logic.

**Separation of concerns** — parsing, analysis, reporting, API communication, and gating have distinct responsibilities.

**Fail-safe CI behavior** — invalid/empty measurable input does not silently pass a quality gate.

**Testability** — core behavior is covered with automated tests and parameterized scenarios.

**Minimal change surface** — optional functionality is isolated from the required core implementation.
