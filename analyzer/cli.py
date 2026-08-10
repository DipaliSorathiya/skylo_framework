import argparse

from analyzer.parser import LogParser
from analyzer.msg3_analyzer import Msg3Analyzer
from analyzer.report import ReportGenerator


def main():

    parser = argparse.ArgumentParser(
        description="MSG3 Success Rate Analyzer"
    )

    parser.add_argument(

        "--log",

        required=True,

        help="Path to log file"

    )

    args = parser.parse_args()

    # ----------------------------

    parser_obj = LogParser(args.log)

    records = parser_obj.parse()

    analyzer = Msg3Analyzer()

    result = analyzer.analyze(records)

    report = ReportGenerator()

    report.print_console(result)

    report.save_json(result)


if __name__ == "__main__":

    main()