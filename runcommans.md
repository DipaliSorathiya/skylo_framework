QA Framework — Run Commands

Run all commands from the project root.

Project root:

/Users/dipalisorthiya/Documents/QA-Framework

0. Setup

cd /Users/dipalisorthiya/Documents/QA-Framework
source venv/bin/activate

### Part 1 — MSG3 Success-Rate Analyzer

Run against bs_log.txt

### python -m analyzer.cli --log logs/bs_log.txt

Expected result:

Total Records : 35
Successes     : 9
Failures      : 26
Ignored       : 0
Success Rate  : 25.71 %
Quality Gate  : FAIL

### Run against bs_log2.txt

### python -m analyzer.cli --log logs/bs_log2.txt

Expected result:

Total Records : 451
Successes     : 409
Failures      : 42
Ignored       : 0
Success Rate  : 90.69 %
Quality Gate  : FAIL

Check JSON report

cat reports/msg3_report.json

Generated report:

reports/msg3_report.json

### Part 2 — API Automation

Run API tests only

### python -m pytest -v api/test_api.py

### Run API tests as part of the complete suite

### python -m pytest -v

The API tests validate the NASA Close-Approach Data API, includingresponse behavior, response structure, expected fields, and query parameters.

### Part 3 — Quality Gate

The quality gate reuses the Part 1 analyzer.

Expected FAIL

### python -m gate.cli \
    --log logs/bs_log2.txt \
    --min-rate 95

Expected:

Success Rate   : 90.69%
Minimum Rate   : 95.00%
Gate Status    : FAIL

Check the exit code:

echo $?

Expected:

1

Expected PASS

### python -m gate.cli \
    --log logs/bs_log2.txt \
    --min-rate 90

Check the exit code:

### echo $?

Expected:

0

The gate uses an inclusive boundary:

success_rate >= minimum_threshold

Therefore, a rate exactly equal to the threshold passes.

Part 1 Bonus — Hourly Trend and Degradation

Run against bs_log2.txt

python -m analyzer.trend_cli \
    --log logs/bs_log2.txt \
    --degradation-threshold 10

Run against bs_log.txt

python -m analyzer.trend_cli \
    --log logs/bs_log.txt \
    --degradation-threshold 10

The bonus reports hourly success rates and degradation windows.

Complete Test Suite

Run all automated tests:

python -m pytest -v

This covers Part 1, Part 2, Part 3, and the bonus tests.

One-Command Framework Execution

The repository provides run.sh as the single execution entry point:

./run.sh

Check its exit code:

echo $?

This is the primary command intended for an evaluator.

GitHub Actions / CI

The CI workflow is under:

.github/workflows/

After pushing changes:

git add .
git commit -m "Complete MSG3 automation framework"
git push


### Commands to Runs : 

Run:

source venv/bin/activate

python -m pytest -v

python -m analyzer.cli --log logs/bs_log.txt

python -m analyzer.cli --log logs/bs_log2.txt

python -m pytest -v api/test_nasa_api.py

python -m gate.cli --log logs/bs_log2.txt --min-rate 95
echo "Gate exit code: $?"

python -m gate.cli --log logs/bs_log2.txt --min-rate 90
echo "Gate exit code: $?"

python -m analyzer.trend_cli \
    --log logs/bs_log2.txt \
    --degradation-threshold 10

./run.sh

