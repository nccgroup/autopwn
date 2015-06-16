import autopwn
import os
import unittest
import mock
import tempfile
from collections import OrderedDict, defaultdict

class ConfigurationTestCase(unittest.TestCase):
    tmppath = tempfile.gettempdir()

    @mock.patch('autopwn.os')
    def test_find_path(self, candidate):
        print("debug: " + str(self.tmppath))
        print("debug: " + str(autopwn.Configuration.find_path(self, self.tmppath)))
        assert(autopwn.Configuration.find_path(self, self.tmppath) == self.tmppath)

if __name__ == '__main__':
    unittest.main()
