# Part 1 — MSG3 Success Rate Analyzer

## 1. Overview

Part 1 implements a reusable Python-based analyzer for calculating the **MSG3 success rate** from raw eNodeB base-station logs.

The goal is to take a production-style log file, identify relevant MSG3 attempts, classify their outcomes, calculate the success rate, and produce both human-readable and machine-readable results.

The implementation is designed as a reusable library rather than a one-off script so that the same analyzer can be consumed later by **Part 3 — the Quality Gate**.

### Success-rate formula

The assignment defines the success rate as:

```text
Success Rate (%) =
    (successes / (successes + failures)) × 100
```

Only measurable outcomes — successes and failures — participate in the denominator.

Ignored or unrecognized statuses do not affect the success rate.

---

# 2. Requirements Covered

The implementation addresses the following Part 1 requirements:

| Requirement                     | Implementation                                           |
| ------------------------------- | -------------------------------------------------------- |
| Analyze both supplied log files | `LogParser` + `Msg3Analyzer`                             |
| Runtime-selectable log file     | CLI accepts log path                                     |
| Calculate MSG3 success rate     | `Msg3Analyzer`                                           |
| Handle malformed lines          | Parser safely ignores incomplete entries                 |
| Handle multi-line entries       | Parser joins physical continuation lines                 |
| Handle ANSI escape sequences    | Parser removes ANSI formatting                           |
| Ignore unrelated log entries    | Parser identifies actual MSG3 result records             |
| Handle unknown statuses         | Unknown statuses are preserved and classified as ignored |
| Handle empty input              | Analyzer returns zero measurable records                 |
| Machine-readable output         | JSON report                                              |
| Human-readable output           | CLI console output                                       |
| Reusable by Part 3              | Analyzer is independent of CLI                           |
| Unit tests                      | Parser and analyzer tests                                |

---

# 3. Project Structure

The Part 1 implementation is organized as follows:

```text
QA-Framework/
│
├── analyzer/
│   ├── __init__.py
│   ├── models.py
│   ├── constants.py
│   ├── parser.py
│   ├── msg3_analyzer.py
│   ├── report.py
│   ├── cli.py
│   └── README_Part1.md
│
├── logs/
│   ├── bs_log.txt
│   └── bs_log2.txt
│
├── reports/
│   └── msg3_report.json
│
├── tests/
│   ├── test_parser.py
│   └── test_msg3_analyzer.py
│
├── api/
│   └── ...
│
├── gate/
│   └── ...
│
├── pytest.ini
├── requirements.txt
└── README.md
```

---

# 4. Architecture

The Part 1 flow is:

```text
                Raw Log File
                     │
                     ▼
              ┌─────────────┐
              │   Parser    │
              │             │
              │ ANSI cleanup│
              │ Multi-line  │
              │ validation  │
              │ extraction  │
              └──────┬──────┘
                     │
                     ▼
              List[Msg3Record]
                     │
                     ▼
             ┌──────────────┐
             │   Analyzer   │
             │              │
             │ success      │
             │ failure      │
             │ ignored      │
             │ success rate │
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────┐
             │   Reporter   │
             └──────┬───────┘
                    │
             ┌──────┴───────┐
             ▼              ▼
        Console Output   JSON Report
                              │
                              ▼
                       Part 3 Quality Gate
```

The key design decision is that **parsing and business logic are separated**.

The parser answers:

> "What MSG3 records exist in this log?"

The analyzer answers:

> "What is the success rate of those records?"

The reporter answers:

> "How should the result be exposed?"

This separation allows Part 3 to reuse the analyzer without depending on the command-line interface.

---

# 5. `models.py`

`models.py` defines the internal representation of a parsed MSG3 record.

```python
@dataclass
class Msg3Record:
    timestamp: str
    rnti: str
    message_type: str
    status: str
```

Each valid MSG3 event is converted into one `Msg3Record`.

Example:

```text
timestamp:
2024-04-24 10:10:10

rnti:
306

message_type:
MSG3-RRC-C-REQ

status:
success
```

This gives the analyzer a stable data structure instead of making it work directly with raw strings.

---

# 6. `constants.py`

Status definitions are kept outside the parser and analyzer so that the classification rules are configurable and easy to maintain.

Current configuration:

```python
SUCCESS_STATUS = {
    "success",
}

FAILURE_STATUS = {
    "failure",
    "timeout",
    "crc-error",
    "crc_error",
    "failed",
    "reject",
    "rejected",
}

IGNORED_STATUS = {
    "unknown",
    "pending",
    "ignored",
}

DEFAULT_SUCCESS_THRESHOLD = 95.0
```

## Why this is important

The parser should not contain business rules such as:

```python
if status == "success":
```

Instead, the analyzer uses the centralized status definitions.

This makes it easier to add a new failure status without changing the parser.

For example, if the log format later introduces:

```text
collision
```

as a failure status, it can be added to:

```python
FAILURE_STATUS
```

without redesigning the parser.

---

# 7. `parser.py`

`parser.py` is responsible only for converting raw log data into structured `Msg3Record` objects.

It does not calculate success rate.

## Parser responsibilities

The parser handles:

1. File reading
2. ANSI escape sequence removal
3. Timestamp detection
4. Physical continuation lines
5. MSG3 identification
6. RNTI extraction
7. MSG3 type extraction
8. Status extraction
9. Malformed records
10. Unrelated log entries

---

# 8. Multi-line Log Handling

The supplied logs are not guaranteed to contain one complete logical event per physical line.

For example:

```text
2024-04-24 10:10:10 ... <UL TB> ... type MSG3-RRC-C-REQ status success
  2e 83 6c d6 4b f4 44 00 00 (9 bytes)
```

The second line is a continuation of the previous physical entry.

The parser therefore maintains a pending entry:

```text
Physical line 1
       │
       ├── timestamp
       │
       ▼
pending entry

Physical line 2
       │
       └── no timestamp
              │
              ▼
       continuation line
```

The parser combines these lines before attempting to parse the logical event.

This prevents continuation data from being incorrectly treated as a separate record.

---

# 9. Why Timestamp Boundaries Are Used

A timestamped line represents the beginning of a new physical log entry.

The parser identifies timestamps using:

```python
TIMESTAMP_PATTERN
```

Conceptually:

```text
YYYY-MM-DD HH:MM:SS
```

When another timestamped line is encountered:

```text
previous pending entry
        ↓
parse it

new timestamp
        ↓
start new entry
```

This is preferable to grouping every line with the same timestamp because a real log can contain multiple independent events within the same second.

---

# 10. Identifying a Valid MSG3 Record

The parser intentionally does not treat every occurrence of the word `MSG3` as an attempt.

A valid result is expected to contain the relevant result information, including:

```text
<UL TB>
MSG3-...
RNTI
status
```

For example:

```text
<UL TB> RNTI 306 ... type MSG3-RRC-C-REQ status success
```

This reduces false positives from unrelated log messages that merely mention MSG3.

---

# 11. Malformed Entry Handling

A production log may contain incomplete or unexpected records.

For example:

```text
2024-04-24 10:10:10 ... <UL TB> RNTI 100
type MSG3-RRC-C-REQ
```

If the status is missing, the parser does not crash.

Instead:

```text
Malformed entry
      │
      ▼
ignored
      │
      ▼
continue parsing next entry
```

This is important because one malformed log line should not prevent analysis of the entire file.

The parser opens files using:

```python
errors="replace"
```

so unexpected encoding bytes do not terminate the complete analysis.

---

# 12. ANSI Escape Sequence Handling

The supplied logs contain terminal color/formatting sequences such as:

```text
\x1b[32m
\x1b[0m
```

These sequences are useful for terminal display but should not affect parsing.

The parser removes ANSI escape sequences before processing the line.

Therefore:

```text
ANSI formatting
      ↓
removed
      ↓
clean log content
      ↓
regex extraction
```

This keeps parsing independent of terminal formatting.

---

# 13. `msg3_analyzer.py`

The analyzer receives:

```python
List[Msg3Record]
```

and calculates:

```text
successes
failures
ignored
success_rate
threshold
gate result
```

The analyzer does not know where the records came from.

They could come from:

* `bs_log.txt`
* `bs_log2.txt`
* a unit test
* another Python program
* Part 3 Quality Gate

This makes the analyzer reusable.

---

# 14. Status Classification

Each record is normalized using lowercase status values.

For example:

```text
SUCCESS
Success
success
SUCCESS
```

are normalized to:

```text
success
```

The analyzer then checks the configured status sets.

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

Unknown/unrecognized statuses are not counted as either success or failure.

---

# 15. Success Rate Calculation

The analyzer follows the exact assignment formula:

```text
success_rate =
    successes / (successes + failures) * 100
```

Example:

```text
successes = 9
failures  = 1

success_rate =
    9 / (9 + 1) × 100

= 90%
```

Ignored records are excluded:

```text
successes = 9
failures  = 1
ignored   = 5

success rate = 90%
```

The five ignored records do not affect the denominator.

---

# 16. Empty Case

If there are no measurable records:

```text
successes = 0
failures  = 0
```

the denominator is zero.

The implementation handles this explicitly instead of performing:

```python
0 / 0
```

The analyzer returns a safe zero success rate rather than crashing.

This is important for CI because an empty or invalid input should not result in a Python exception that hides the actual problem.

---

# 17. Quality Threshold

The current configured threshold is:

```text
95%
```

Therefore:

```text
success_rate >= 95%
```

passes.

And:

```text
success_rate < 95%
```

fails.

The boundary condition is intentional.

For example:

```text
95% → PASS
94.99% → FAIL
```

This behavior is covered by unit tests.

---

# 18. `report.py`

The reporting layer converts the analyzer result into machine-readable JSON.

Example:

```json
{
    "successes": 2778,
    "failures": 52,
    "ignored": 0,
    "success_rate": 98.16,
    "success_threshold": 95.0,
    "gate_status": "PASS"
}
```

The JSON report is intended for downstream automation.

Part 3 can consume this information without parsing console output.

---

# 19. CLI

The command-line interface allows the log file to be selected at runtime.

Example:

```bash
python -m analyzer.cli --log logs/bs_log.txt
```

Another file can be analyzed without modifying the source code:

```bash
python -m analyzer.cli --log logs/bs_log2.txt
```

This satisfies the requirement that the input log must not be hard-coded.

---

# 20. Running Part 1

Activate the virtual environment:

```bash
source venv/bin/activate
```

Run the analyzer:

```bash
python -m analyzer.cli --log logs/bs_log.txt
```

Run against the second log:

```bash
python -m analyzer.cli --log logs/bs_log2.txt
```

---

# 21. Example Human-Readable Output

The CLI produces output similar to:

```text
========== MSG3 Analysis ==========

Successes     : 51
Failures      : 26
Ignored       : 0
Success Rate  : 66.23 %
Threshold     : 95.00 %
Gate Status   : FAIL
```

For the second log:

```text
========== MSG3 Analysis ==========

Successes     : 2778
Failures      : 52
Ignored       : 0
Success Rate  : 98.16 %
Threshold     : 95.00 %
Gate Status   : PASS
```

The exact values depend on the current parser and supplied log contents.

---

# 22. Unit Testing

Part 1 contains unit tests for both parsing and analysis.

## Parser tests

`tests/test_parser.py` validates:

* Missing file
* Empty file
* Valid MSG3 record
* Non-MSG3 records
* ANSI cleanup
* Unknown status
* Multiple records
* `Msg3Record` object creation
* Timestamp extraction
* Failure status
* Multi-line MSG3 entries
* Multiple multi-line entries
* Malformed multi-line entries
* Non-MSG3 multi-line entries

Run:

```bash
python -m pytest tests/test_parser.py -v
```

Expected:

```text
14 passed
```

---

# 23. Analyzer Tests

`tests/test_msg3_analyzer.py` validates:

* All-success input
* All-failure input
* Mixed success/failure
* Ignored statuses
* Empty records
* Success-rate precision
* Threshold failure
* Threshold boundary
* Case normalization
* Ignored records not affecting the rate
* Analyzer reusability

Run:

```bash
python -m pytest tests/test_msg3_analyzer.py -v
```

---

# 24. Run All Part 1 Tests

Run:

```bash
python -m pytest tests/test_parser.py tests/test_msg3_analyzer.py -v
```

Current expected result:

```text
25 passed
```

This provides regression protection for both parsing and business logic.

---

# 25. Production-Readiness Decisions

Several design decisions were intentionally made to make the implementation more robust.

### Decision 1 — Separate parser and analyzer

The parser does not calculate business metrics.

The analyzer does not understand raw log syntax.

This follows separation of concerns.

### Decision 2 — Ignore malformed records instead of crashing

A single bad log entry should not prevent analysis of the remaining file.

### Decision 3 — Don't count every MSG3 mention

Only actual MSG3 result records are converted into `Msg3Record`.

This reduces false positives.

### Decision 4 — Externalize status definitions

Status classification is centralized in `constants.py`.

### Decision 5 — Don't hard-code the input file

The log path is provided at runtime.

### Decision 6 — Preserve unknown statuses

Unknown statuses are not silently converted into failures.

They are retained as records and classified as ignored by the analyzer.

This prevents an unexpected future status from artificially reducing the success rate.

### Decision 7 — Avoid volatile assertions

The tests focus on structural properties and invariants rather than hard-coded values that may change between runs.

---

# 26. Handling Large Files

The parser reads the file incrementally:

```python
for raw_line in file:
```

rather than loading the entire file into memory.

Therefore the memory usage is primarily associated with the current logical entry and the resulting parsed records rather than the complete raw log file.

This is more suitable for production-sized log files.

---

# 27. Error Handling Strategy

The parser follows a fail-soft strategy for malformed log content.

### File does not exist

Raises:

```text
FileNotFoundError
```

This is an environmental/configuration error and should be visible to the caller.

### Invalid individual log entry

The parser skips the malformed entry and continues.

### Invalid encoding

The file is opened with:

```python
errors="replace"
```

to avoid terminating analysis because of an isolated invalid byte.

### Empty file

Returns:

```text
[]
```

and the analyzer handles the empty case.

---

# 28. Part 1 Data Flow

The complete flow is:

```text
CLI
 │
 │ --log logs/bs_log.txt
 ▼
LogParser
 │
 ├── Read file
 ├── Clean ANSI codes
 ├── Detect timestamp boundaries
 ├── Combine continuation lines
 ├── Detect MSG3 result
 ├── Extract timestamp
 ├── Extract RNTI
 ├── Extract type
 └── Extract status
 │
 ▼
Msg3Record[]
 │
 ▼
Msg3Analyzer
 │
 ├── Classify success
 ├── Classify failure
 ├── Classify ignored
 ├── Calculate success rate
 └── Evaluate threshold
 │
 ▼
Report
 │
 ├── Console
 └── JSON
 │
 ▼
Part 3 Quality Gate
```

---

# 29. Why This Design Supports Part 3

Part 3 requires the MSG3 analyzer to be reused as a library.

The architecture already supports this.

Part 3 does not need to execute:

```bash
python analyzer.py
```

and parse console output.

Instead it can directly call:

```python
parser = LogParser(log_file)

records = parser.parse()

analyzer = Msg3Analyzer()

result = analyzer.analyze(records)
```

The Quality Gate can then evaluate:

```python
result["success_rate"]
```

against a threshold supplied by the gate.

This keeps the quality gate independent from console formatting.

---

# 30. Testing Strategy

The testing strategy has two levels.

## Unit tests

Test individual components:

```text
Parser
   ↓
Parser unit tests

Analyzer
   ↓
Analyzer unit tests
```

These tests use small synthetic inputs and validate specific behaviors.

## Integration-style validation

Run the complete analyzer against:

```text
logs/bs_log.txt
logs/bs_log2.txt
```

This validates that the parser and analyzer work together against the supplied production-style data.

---

# 31. Definition of Done

Part 1 is considered complete when:

* [x] Both supplied logs can be analyzed
* [x] Log file is selectable at runtime
* [x] MSG3 records are parsed
* [x] Multi-line entries are handled
* [x] Malformed entries do not crash the parser
* [x] ANSI escape sequences are handled
* [x] Non-MSG3 entries are ignored
* [x] Status classification is centralized
* [x] Success rate follows the required formula
* [x] Empty input is handled
* [x] JSON output is generated
* [x] Human-readable output is generated
* [x] Parser unit tests exist
* [x] Analyzer unit tests exist
* [x] Threshold behavior is tested
* [x] Analyzer is reusable by Part 3

---

# 32. Stretch / Future Improvements

The assignment identifies per-hour trend/degradation analysis as a Part 1 bonus.

Possible future implementation:

```text
Timestamp
    ↓
Hour bucket
    ↓
Success / Failure count
    ↓
Hourly success rate
    ↓
Trend
    ↓
Degradation detection
```

For example:

```text
10:00 → 98%
11:00 → 97%
12:00 → 96%
13:00 → 82%  ← degradation
14:00 → 80%
```

This could identify when a problem started rather than reporting only the overall success rate.

This feature is intentionally separate from the core success-rate calculation.

---

# 33. Commands Cheat Sheet

### Run Part 1 analyzer

```bash
python -m analyzer.cli --log logs/bs_log.txt
```

### Analyze second log

```bash
python -m analyzer.cli --log logs/bs_log2.txt
```

### Run parser tests

```bash
python -m pytest tests/test_parser.py -v
```

### Run analyzer tests

```bash
python -m pytest tests/test_msg3_analyzer.py -v
```

### Run complete Part 1 test suite

```bash
python -m pytest tests/test_parser.py tests/test_msg3_analyzer.py -v
```

### Run all project tests

```bash
python -m pytest -v
```

---

# 34. Summary

Part 1 provides a small but reusable log-analysis component rather than a single script.

The main design principle is:

```text
Raw logs
   ↓
Robust parser
   ↓
Structured records
   ↓
Business-rule analyzer
   ↓
Machine-readable report
   ↓
Reusable quality-gate input
```

The parser is responsible for understanding the log format, including multi-line and malformed entries.

The analyzer is responsible for calculating the MSG3 success rate.

The reporter is responsible for exposing the result.

This separation makes the implementation easier to test, maintain, extend, and reuse in Part 3.
