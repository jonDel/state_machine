import unittest
from state_machine import StateMachine

class StateMachineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sm = StateMachine('tests_sm_db.sqlite', 'test1')
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_dummy(self):
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
