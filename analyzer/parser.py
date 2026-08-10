import re
from typing import List, Optional

from analyzer.models import Msg3Record


class LogParser:
    """
    Parser for eNodeB MSG3 log entries.

    Responsibilities:
        - Read log files incrementally
        - Remove ANSI escape sequences
        - Handle physical continuation lines
        - Identify MSG3 result records
        - Extract timestamp, RNTI, type and status
        - Ignore malformed/unrelated entries safely

    The parser does not calculate success rate.
    """

    # Example:
    # 2024-04-24 08:04:44
    TIMESTAMP_PATTERN = re.compile(
        r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})"
    )

    # Example:
    # RNTI   306
    RNTI_PATTERN = re.compile(
        r"\bRNTI\s+(\d+)\b",
        re.IGNORECASE
    )

    # Example:
    # type MSG3-RRC-C-REQ
    # type MSG3-UNKNOWN
    # type MSG3-SCHED-REQ
    MSG3_TYPE_PATTERN = re.compile(
        r"\btype\s+(MSG3-[A-Za-z0-9_-]+)\b",
        re.IGNORECASE
    )

    # Example:
    # status success
    # status timeout
    STATUS_PATTERN = re.compile(
        r"\bstatus\s+([A-Za-z0-9_-]+)\b",
        re.IGNORECASE
    )

    # Used to identify the actual result line.
    #
    # Example:
    # <UL TB> RNTI 306 ... type MSG3-RRC-C-REQ status success
    UL_TB_PATTERN = re.compile(
        r"<UL\s+TB",
        re.IGNORECASE
    )

    # MSG3 type must actually be present.
    MSG3_PATTERN = re.compile(
        r"\bMSG3-[A-Za-z0-9_-]+\b",
        re.IGNORECASE
    )

    # ANSI escape sequences such as:
    #
    # \033[32m
    # \033[1;34m
    ANSI_PATTERN = re.compile(
        r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
    )

    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> List[Msg3Record]:
        """
        Parse the complete log file.

        Returns:
            List[Msg3Record]
        """

        records: List[Msg3Record] = []

        with open(
            self.file_path,
            "r",
            encoding="utf-8",
            errors="replace"
        ) as file:

            # Used for physical continuation lines.
            pending_lines: List[str] = []

            for raw_line in file:

                line = self._clean_line(raw_line)

                if not line:
                    continue

                # -------------------------------------------------
                # A line with a timestamp starts a new physical log
                # entry.
                #
                # Example:
                #
                # 2024-04-24 08:04:44 ... <RB> ...:
                #
                #     2e 83 6c ... (9 bytes)
                #
                # The second line has no timestamp and therefore
                # belongs to the previous physical entry.
                # -------------------------------------------------

                if self._has_timestamp(line):

                    # Process anything accumulated previously.
                    if pending_lines:
                        record = self._parse_logical_entry(
                            pending_lines
                        )

                        if record:
                            records.append(record)

                    pending_lines = [line]

                else:

                    # Continuation line.
                    if pending_lines:
                        pending_lines.append(line)

            # Process final entry.
            if pending_lines:

                record = self._parse_logical_entry(
                    pending_lines
                )

                if record:
                    records.append(record)

        return records

    # =============================================================
    # Cleaning
    # =============================================================

    def _clean_line(self, line: str) -> str:
        """
        Remove ANSI escape sequences and whitespace.
        """

        line = self.ANSI_PATTERN.sub("", line)

        return line.strip()

    # =============================================================
    # Timestamp
    # =============================================================

    def _has_timestamp(self, line: str) -> bool:
        """
        Determine whether this is the beginning of a
        timestamped log entry.
        """

        return bool(
            self.TIMESTAMP_PATTERN.match(line)
        )

    # =============================================================
    # Logical entry parsing
    # =============================================================

    def _parse_logical_entry(
        self,
        lines: List[str]
    ) -> Optional[Msg3Record]:
        """
        Parse one logical log entry.

        A logical entry can contain multiple physical lines.

        Example:

            <RB> Srb0::getSdu() gave a packet:
            2e 83 6c d6 4b f4 44 00 00 (9 bytes)

        These are treated as one logical entry.

        Only an actual UL TB MSG3 result is converted into
        Msg3Record.
        """

        # Combine physical continuation lines.
        entry = " ".join(lines)

        # ---------------------------------------------------------
        # We only want actual UL TB MSG3 result lines.
        #
        # This prevents unrelated lines containing the word
        # "MSG3" from being counted.
        # ---------------------------------------------------------

        if not self.UL_TB_PATTERN.search(entry):
            return None

        if not self.MSG3_PATTERN.search(entry):
            return None

        # ---------------------------------------------------------
        # Extract timestamp
        # ---------------------------------------------------------

        timestamp_match = self.TIMESTAMP_PATTERN.search(entry)

        if not timestamp_match:
            return None

        timestamp = timestamp_match.group(1)

        # ---------------------------------------------------------
        # Extract RNTI
        # ---------------------------------------------------------

        rnti_match = self.RNTI_PATTERN.search(entry)

        if not rnti_match:
            return None

        rnti = rnti_match.group(1)

        # ---------------------------------------------------------
        # Extract MSG3 type
        # ---------------------------------------------------------

        type_match = self.MSG3_TYPE_PATTERN.search(entry)

        if not type_match:
            return None

        message_type = type_match.group(1)

        # ---------------------------------------------------------
        # Extract status
        # ---------------------------------------------------------

        status_match = self.STATUS_PATTERN.search(entry)

        if not status_match:
            return None

        status = status_match.group(1).strip().lower()

        return Msg3Record(
            timestamp=timestamp,
            rnti=rnti,
            message_type=message_type,
            status=status
        )