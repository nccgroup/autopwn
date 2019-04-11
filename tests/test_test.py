import unittest
import autopwn2

class TestsContainer(unittest.TestCase):
    longMessage = True

def make_test_function(description, a, b):
    def test(self):
        self.assertEqual(a, b, description)
    return test

if __name__ == '__main__':
    testsmap = {
        'autopwn.Configuration': [self, self]
        }

    for name, params in testsmap.items():
        test_func = make_test_function(name, params[0], params[1])
        setattr(TestsContainer, 'test_{0}'.format(name), test_func)

    unittest.main()
