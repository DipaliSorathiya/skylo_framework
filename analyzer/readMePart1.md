# Part 1 — MSG3 Success Rate Analyzer

## 1. Overview

The MSG3 analyzer parses eNodeB logs, identifies MSG3 attempts, classifies their outcomes, and calculates the success rate using the required formula.

```text
Success Rate (%) =
(successes / (successes + failures)) × 100
```

The analyzer is implemented as reusable library logic so that **Part 3 — Quality Gate** can consume it directly without duplicating the calculation.

---

## 2. Implementation Flow

```text
Raw Log
   ↓
LogParser
   ↓
Msg3Record
   ↓
Msg3Analyzer
   ↓
Success / Failure / Ignored
   ↓
Success Rate
   ↓
Console + JSON Report
   ↓
Part 3 Quality Gate
```

### Responsibilities

| Component          | Responsibility                            |
| ------------------ | ----------------------------------------- |
| `parser.py`        | Parse and normalize raw log entries       |
| `models.py`        | Define `Msg3Record`                       |
| `constants.py`     | Define status classifications             |
| `msg3_analyzer.py` | Calculate success/failure counts and rate |
| `report.py`        | Generate console and JSON reports         |
| `cli.py`           | Accept log file at runtime                |

---

## 3. Log Parsing

The supplied logs contain different formatting patterns. The parser handles:

* Multi-line MSG3 entries
* ANSI/control sequences
* Unrecognized log lines
* Malformed entries
* Different MSG3 formats
* Tolerant file decoding

A logical MSG3 event is represented as:

```python
@dataclass
class Msg3Record:
    timestamp: str
    rnti: str
    message_type: str
    status: str
```

Timestamp boundaries are used to distinguish new log entries from continuation lines.

Malformed individual entries are skipped so that one bad record does not terminate analysis of the complete file.

---

## 4. Status Classification

Status definitions are centralized in `constants.py`.

### Success

```text
success
```

### Failure

```text
failure
timeout
crc-error
crc_error
failed
reject
rejected
```

### Ignored

```text
unknown
pending
ignored
```

Unknown or unsupported statuses are not automatically treated as failures.

Only success and failure records contribute to the success-rate denominator.

---

## 5. Runtime Execution

The log file is selected at runtime.

### Analyze `bs_log.txt`

```bash
python -m analyzer.cli --log logs/bs_log.txt
```

### Analyze `bs_log2.txt`

```bash
python -m analyzer.cli --log logs/bs_log2.txt
```

No log file is hard-coded into the analyzer.

---

## 6. Results

### `bs_log.txt`

```text
Total Records : 35
Successes     : 9
Failures      : 26
Ignored       : 0
Success Rate  : 25.71 %
```

Calculation:

```text
9 / (9 + 26) × 100 = 25.71%
```

### `bs_log2.txt`

```text
Total Records : 451
Successes     : 409
Failures      : 42
Ignored       : 0
Success Rate  : 90.69 %
```

Calculation:

```text
409 / (409 + 42) × 100 = 90.69%
```

### Summary

| Log           | Records | Success | Failure | Ignored | Success Rate |
| ------------- | ------: | ------: | ------: | ------: | -----------: |
| `bs_log.txt`  |      35 |       9 |      26 |       0 |   **25.71%** |
| `bs_log2.txt` |     451 |     409 |      42 |       0 |   **90.69%** |

---

## 7. Reporting

The analyzer produces both required output formats.

### Console Report

```bash
python -m analyzer.cli --log logs/bs_log2.txt
```

### JSON Report

Generated at:

```text
reports/msg3_report.json
```

The JSON report is machine-readable and can be consumed by downstream automation such as the Part 3 Quality Gate.

---

## 8. Empty Data Behavior

When there are no measurable success/failure records:

```text
successes = 0
failures  = 0
```

the analyzer returns:

```text
success_rate = 0.0%
```

This avoids division-by-zero and prevents an empty input from accidentally passing a positive quality threshold.

---

## 9. Design Decisions

### Repeated Attempts

Each parsed MSG3 attempt is counted independently.

Records are not deduplicated by RNTI because the metric represents **MSG3 attempt success rate**, rather than unique-device success rate.

### Recent Activity

The specification does not define a concrete recency window.

Therefore, the selected log file is treated as the analysis window and no arbitrary time filter is applied.

### Unknown Statuses

Unknown statuses are ignored for the success-rate calculation rather than being classified as failures.

This prevents an unexpected future status from artificially lowering the metric.

### Reusable Analyzer

Part 3 imports the analyzer directly instead of executing the CLI and parsing console output.

This keeps business logic independent from presentation and CLI formatting.

---

## 10. Testing

### Parser Tests

```bash
python -m pytest tests/test_parser.py -v
```

### Analyzer Tests

```bash
python -m pytest tests/test_msg3_analyzer.py -v
```

### All Part 1 Tests

```bash
python -m pytest tests/test_parser.py tests/test_msg3_analyzer.py -v
```

### Complete Framework

```bash
python -m pytest -v
```

Test coverage includes:

* Valid MSG3 records
* Success/failure classification
* Ignored statuses
* Multi-line records
* ANSI cleanup
* Malformed entries
* Empty input
* Success-rate calculation
* Threshold behavior
* Case normalization

---

## 11. Quality Threshold

The configured default threshold is:

```text
95%
```

The boundary is inclusive:

```text
success_rate >= threshold → PASS
success_rate < threshold  → FAIL
```

Therefore:

```text
95.00% → PASS
94.99% → FAIL
```

This behavior is tested and reused by Part 3.

---

## 12. Bonus — Hourly Trend & Degradation

The optional trend functionality is implemented separately:

```text
analyzer/trend_analyzer.py
analyzer/trend_cli.py
```

Run:

```bash
python -m analyzer.trend_cli \
    --log logs/bs_log2.txt \
    --degradation-threshold 10
```

The bonus provides:

* Hourly success rates
* Trend visibility
* Configurable degradation threshold
* Degradation-window detection

Hourly bucketing uses the timestamp representation from the source log without applying an implicit timezone conversion.

---

## 13. Definition of Done

* [x] Both supplied log files analyzed
* [x] Runtime-selectable log input
* [x] Required success-rate formula
* [x] Multi-line log handling
* [x] ANSI cleanup
* [x] Malformed/unrecognized line handling
* [x] Empty-data handling
* [x] Console reporting
* [x] JSON reporting
* [x] Parser tests
* [x] Analyzer tests
* [x] Threshold boundary testing
* [x] Reusable analyzer for Part 3
* [x] Hourly trend analysis
* [x] Degradation detection

---

## 14. Quick Command Reference

```bash
# Analyze first log
python -m analyzer.cli --log logs/bs_log.txt

# Analyze second log
python -m analyzer.cli --log logs/bs_log2.txt

# Parser tests
python -m pytest tests/test_parser.py -v

# Analyzer tests
python -m pytest tests/test_msg3_analyzer.py -v

# All Part 1 tests
python -m pytest tests/test_parser.py tests/test_msg3_analyzer.py -v

# Complete framework
python -m pytest -v

# Bonus trend analysis
python -m analyzer.trend_cli \
    --log logs/bs_log2.txt \
    --degradation-threshold 10
```

---

## Summary

Part 1 provides a reusable log-analysis component with clear separation between parsing, business logic, reporting, and CI integration.

```text
Raw Log
   ↓
Robust Parser
   ↓
Structured Records
   ↓
MSG3 Analyzer
   ↓
Console + JSON
   ↓
Quality Gate
```
