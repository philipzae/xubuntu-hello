import unittest

from src import manjaro_hello


class ManjaroHello(unittest.TestCase):
    def setUp(self):
        self.path = "test/"

    def test_read_json(self):
        json = manjaro_hello.read_json(self.path + "test.json")
        self.assertEqual(json, {"test": "json"})
        json = manjaro_hello.read_json(self.path + "test")
        self.assertEqual(json, None)

    def test_get_lsb_infos(self):
        self.assertIsInstance(manjaro_hello.get_lsb_infos(), dict)
