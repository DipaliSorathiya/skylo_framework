import tempfile

import pytest

from analyzer.models import Msg3Record
from analyzer.parser import LogParser


class TestLogParser:

    # ============================================================
    # TC01 - File does not exist
    # ============================================================

    def test_file_not_found(self):

        parser = LogParser(
            "does_not_exist.txt"
        )

        with pytest.raises(FileNotFoundError):
            parser.parse()

    # ============================================================
    # TC02 - Empty file
    # ============================================================

    def test_empty_file(self):

        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False
        ) as f:

            f.write("")
            f.flush()

            parser = LogParser(f.name)

            records = parser.parse()

        assert records == []

    # ============================================================
    # TC03 - Valid single-line MSG3 record
    # ============================================================

    def test_valid_msg3_record(self):

        log = """\
2024-04-24 10:10:10 100,100 [4] <UL TB> RNTI 100 eNB-ID N/A S-TMSI N/A SC-U 1 type MSG3-RRC-C-REQ status success
"""

        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False
        ) as f:

            f.write(log)
            f.flush()

            parser = LogParser(f.name)

            records = parser.parse()

        assert len(records) == 1

        record = records[0]

        assert record.timestamp == "2024-04-24 10:10:10"
        assert record.rnti == "100"
        assert record.message_type == "MSG3-RRC-C-REQ"
        assert record.status == "success"

    # ============================================================
    # TC04 - Ignore non-MSG3 entry
    # ============================================================

    def test_ignore_non_msg3(self):

        log = """\
2024-04-24 10:10:10 100,100 [4] <Layer2> Some unrelated event
"""

        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False
        ) as f:

            f.write(log)
            f.flush()

            parser = LogParser(f.name)

            records = parser.parse()

        assert records == []

    # ============================================================
    # TC05 - ANSI escape sequence cleanup
    # ============================================================

    def test_ansi_cleanup(self):

        log = (
            "\x1b[32m"
            "2024-04-24 10:10:10 100,100 [4] "
            "<UL TB> RNTI 100 eNB-ID N/A "
            "S-TMSI N/A SC-U 1 "
            "type MSG3-RRC-C-REQ status success"
            "\x1b[0m\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False
        ) as f:

            f.write(log)
            f.flush()

            parser = LogParser(f.name)

            records = parser.parse()

        assert len(records) == 1
        assert records[0].status == "success"

    # ============================================================
    # TC06 - Unknown status should still be parsed
    # ============================================================

    def test_unknown_status(self):

        log = """\
2024-04-24 10:10:10 100,200 [4] <UL TB> RNTI 200 eNB-ID N/A S-TMSI N/A SC-U 1 type MSG3-RRC-C-REQ status abc
"""

        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False
        ) as f:

            f.write(log)
            f.flush()

            parser = LogParser(f.name)

            records = parser.parse()

        assert len(records) == 1
        assert records[0].status == "abc"

    # ============================================================
    # TC07 - Multiple MSG3 records
    # ============================================================

    def test_multiple_records(self):

        log = """\
2024-04-24 10:10:10 100,100 [4] <UL TB> RNTI 100 eNB-ID N/A S-TMSI N/A SC-U 1 type MSG3-RRC-C-REQ status success
2024-04-24 10:10:11 100,200 [4] <UL TB> RNTI 200 eNB-ID N/A S-TMSI N/A SC-U 2 type MSG3-RRC-C-REQ status timeout
"""

        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False
        ) as f:

            f.write(log)
            f.flush()

            parser = LogParser(f.name)

            records = parser.parse()

        assert len(records) == 2

        assert records[0].status == "success"
        assert records[1].status == "timeout"

    # ============================================================
    # TC08 - Verify Msg3Record object
    # ============================================================

    def test_record_object(self):

        log = """\
2024-04-24 10:10:10 100,100 [4] <UL TB> RNTI 100 eNB-ID N/A S-TMSI N/A SC-U 1 type MSG3-RRC-C-REQ status success
"""

        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False
        ) as f:

            f.write(log)
            f.flush()

            parser = LogParser(f.name)

            records = parser.parse()

        assert len(records) == 1
        assert isinstance(records[0], Msg3Record)

    # ============================================================
    # TC09 - Timestamp extraction
    # ============================================================

    def test_timestamp_extraction(self):

        log = """\
2024-04-24 14:17:20 381,775 [4] <UL TB> RNTI 306 eNB-ID N/A S-TMSI N/A SC-U 1 type MSG3-RRC-C-REQ status success
"""

        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False
        ) as f:

            f.write(log)
            f.flush()

            parser = LogParser(f.name)

            records = parser.parse()

        assert len(records) == 1

        assert records[0].timestamp == (
            "2024-04-24 14:17:20"
        )

    # ============================================================
    # TC10 - Failure status
    # ============================================================

    def test_failure_status(self):

        log = """\
2024-04-24 14:17:20 381,775 [4] <UL TB> RNTI 306 eNB-ID N/A S-TMSI N/A SC-U 1 type MSG3-RRC-C-REQ status timeout
"""

        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False
        ) as f:

            f.write(log)
            f.flush()

            parser = LogParser(f.name)

            records = parser.parse()

        assert len(records) == 1
        assert records[0].status == "timeout"

    # ============================================================
    # TC11 - Multi-line MSG3 entry
    # ============================================================

    def test_multiline_msg3_entry(self):

        log = """\
2024-04-24 10:10:10 100,100 [4] <UL TB> RNTI 100 eNB-ID N/A S-TMSI N/A SC-U 1 type MSG3-RRC-C-REQ status success
  2e 83 6c d6 4b f4 44 00 00 (9 bytes)
"""

        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False
        ) as f:

            f.write(log)
            f.flush()

            parser = LogParser(f.name)

            records = parser.parse()

        assert len(records) == 1

        record = records[0]

        assert record.timestamp == (
            "2024-04-24 10:10:10"
        )

        assert record.rnti == "100"

        assert record.message_type == (
            "MSG3-RRC-C-REQ"
        )

        assert record.status == "success"

    # ============================================================
    # TC12 - Multiple multi-line MSG3 entries
    # ============================================================

    def test_multiple_msg3_entries_with_continuation_lines(self):

        log = """\
2024-04-24 10:10:10 100,100 [4] <UL TB> RNTI 100 eNB-ID N/A S-TMSI N/A SC-U 1 type MSG3-RRC-C-REQ status success
  2e 83 6c d6 4b f4 44 00 00 (9 bytes)
2024-04-24 10:10:11 100,200 [4] <UL TB> RNTI 200 eNB-ID N/A S-TMSI N/A SC-U 2 type MSG3-UNKNOWN status timeout
  3b 3d 03 01 36 14 88 07 (8 bytes)
"""

        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False
        ) as f:

            f.write(log)
            f.flush()

            parser = LogParser(f.name)

            records = parser.parse()

        assert len(records) == 2

        assert records[0].rnti == "100"
        assert records[0].status == "success"

        assert records[1].rnti == "200"
        assert records[1].status == "timeout"

    # ============================================================
    # TC13 - Malformed multi-line MSG3 entry
    # ============================================================

    def test_malformed_multiline_msg3_is_ignored(self):

        log = """\
2024-04-24 10:10:10 100,100 [4] <UL TB> RNTI 100 eNB-ID N/A S-TMSI N/A SC-U 1 type MSG3-RRC-C-REQ
  2e 83 6c d6 4b f4 44 00 00 (9 bytes)
2024-04-24 10:10:11 100,200 [4] <UL TB> RNTI 200 eNB-ID N/A S-TMSI N/A SC-U 2 type MSG3-RRC-C-REQ status success
"""

        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False
        ) as f:

            f.write(log)
            f.flush()

            parser = LogParser(f.name)

            records = parser.parse()

        # First event is malformed because it has no status.
        # Second event is valid.
        assert len(records) == 1

        assert records[0].rnti == "200"
        assert records[0].status == "success"

    # ============================================================
    # TC14 - Non-MSG3 continuation entry
    # ============================================================

    def test_non_msg3_multiline_entry_is_ignored(self):

        log = """\
2024-04-24 10:10:10 100,100 [4] <RB> Srb0::getSdu() gave a packet:
  2e 83 6c d6 4b f4 44 00 00 (9 bytes)
"""

        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False
        ) as f:

            f.write(log)
            f.flush()

            parser = LogParser(f.name)

            records = parser.parse()

        assert records == []