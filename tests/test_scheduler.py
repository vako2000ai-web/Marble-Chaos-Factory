import random
import sqlite3
import unittest

from backend.scheduler import SCHEMA, add_media, choose_next, record_playback


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript(SCHEMA)

    def tearDown(self):
        self.db.close()

    def test_empty(self):
        self.assertIsNone(choose_next(self.db))

    def test_unapproved_skipped(self):
        add_media(self.db, "skip.mp4", "spiral", 10, approved=False)
        add_media(self.db, "play.mp4", "race", 10)
        self.assertEqual(choose_next(self.db).path, "play.mp4")

    def test_no_repeat_when_alternative_exists(self):
        add_media(self.db, "a.mp4", "spiral", 10)
        add_media(self.db, "b.mp4", "race", 10)
        first = choose_next(self.db, random.Random(1))
        record_playback(self.db, first.id)
        second = choose_next(self.db, random.Random(1))
        self.assertNotEqual(first.id, second.id)

    def test_invalid_duration(self):
        with self.assertRaises(ValueError):
            add_media(self.db, "a.mp4", "race", 0)


if __name__ == "__main__":
    unittest.main()
