from datetime import datetime, timedelta, timezone
import unittest

from pandas import DataFrame

from .analysis import ACTIVITY, CASE_ID, TIMESTAMP, analyze, analyze_dataframe, cycle_time_days

START = datetime(2020, 1, 1, tzinfo=timezone.utc)


class Trace(list):
    def __init__(self, case_id, *events):
        super().__init__(
            {"concept:name": name, "time:timestamp": START + timedelta(days=day)}
            for day, name in events
        )
        self.attributes = {"concept:name": case_id}


class AnalysisTests(unittest.TestCase):
    def test_all_answers_and_overlapping_categories(self):
        log = [
            Trace("a", (0, "O_Accepted"), (1, "O_Accepted"), (2, "O_Refused")),
            Trace("b", (1, "O_Cancelled"), (0, "A_Start"), (2, "A_End")),
            Trace("c", (3, "O_Cancelled"), (1, "A_Start"), (3, "O_Cancelled")),
            Trace("d", (0, "A_Start"), (1, "O_Cancelled"), (1, "A_End")),
        ]

        a, b, c, d, e = analyze(log)

        self.assertEqual(a.count, 4)
        self.assertAlmostEqual(b.mean_days, 1.75)
        self.assertEqual([case.case_id for case in c.cases], ["a"])
        self.assertEqual(c.mean_days, 2)
        self.assertEqual([case.case_id for case in d.cases], ["a"])
        self.assertEqual(d.mean_days, 2)
        self.assertEqual([case.case_id for case in e.cases], ["c"])
        self.assertEqual(e.mean_days, 2)
        self.assertEqual(log[1][0]["concept:name"], "O_Cancelled")

    def test_empty_groups_and_single_event(self):
        answers = analyze([Trace("only", (0, "A_Start"))])

        self.assertEqual(answers[1].mean_days, 0)
        self.assertEqual([answer.count for answer in answers[2:]], [0, 0, 0])
        self.assertIsNone(answers[2].mean_days)
        self.assertIsNone(analyze([])[1].mean_days)

    def test_cycle_time_normalizes_timezones(self):
        plus_seven = timezone(timedelta(hours=7))
        start = datetime(2020, 1, 1, 7, tzinfo=plus_seven)
        end = datetime(2020, 1, 2, 12)

        self.assertEqual(cycle_time_days(start, end), 1.5)

    def test_invalid_timestamp_reports_case(self):
        trace = Trace("invalid", (0, "A_Start"))
        del trace[0]["time:timestamp"]
        with self.assertRaisesRegex(ValueError, "invalid.*Timestamp"):
            analyze([trace])

    def test_dataframe_uses_shared_order_for_tied_timestamps(self):
        log = DataFrame({
            CASE_ID: ["one", "one", "one", "two", "two"],
            ACTIVITY: ["O_Cancelled", "O_Refused", "O_Accepted", "O_Accepted", "O_Cancelled"],
            TIMESTAMP: [START, START, START - timedelta(days=2), START, START],
        })
        received = []

        def prepare(frame):
            received.append(frame)
            return frame.sort_values(TIMESTAMP, kind="stable")

        a, b, c, d, e = analyze_dataframe(log, prepare)
        self.assertIs(received[0], log)
        self.assertEqual(a.count, 2)
        self.assertEqual(b.mean_days, 1)
        self.assertEqual(c.count, 2)
        self.assertEqual(d.count, 1)
        self.assertEqual([case.case_id for case in e.cases], ["two"])

    def test_dataframe_rejects_missing_columns(self):
        with self.assertRaisesRegex(ValueError, "Kolom log hilang"):
            analyze_dataframe(DataFrame({CASE_ID: ["one"]}), lambda log: log)


    def test_duplicate_case_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Case ID ganda"):
            analyze([Trace("same", (0, "A_Start")), Trace("same", (1, "A_End"))])


if __name__ == "__main__":
    unittest.main()
