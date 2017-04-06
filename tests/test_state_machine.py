"""Unit tests for state_machine_db package"""
import unittest
import sqlite3 as sql
import os
from datetime import datetime
from time import sleep
from collections import OrderedDict
from state_machine_db import StateMachine

SQLITE_FILE = 'tests_sm_db.sqlite'
SQLITE_BASE_PATH = os.path.abspath(SQLITE_FILE)
if not os.path.isfile(SQLITE_BASE_PATH):
    PATH_SPLIT = SQLITE_BASE_PATH.split('/')
    SQLITE_BASE_PATH = '/'.join(PATH_SPLIT[:-1])+'/tests/'+SQLITE_FILE

class MessAroundSM(StateMachine):
    """ Supporting child class of StateMachine """
    def __init__(self, sqlite_bp, activity_id):
        super(MessAroundSM, self).__init__(sqlite_bp, activity_id)
        self._states_methods_dict = OrderedDict()
        self._states_methods_dict['read_file'] = {'method':self.read_file}
        self._states_methods_dict['apply_regex'] = {'method':self.apply_regex}
        self._states_methods_dict['save_file'] = {'method':self.save_file}
        self._states_methods_dict['exit'] = {'method':self.exit}
        self.sm_fields = {'activity_creation_date':datetime.now(),
                          'activity_name': 'mess_around_a_bit'}
        self.updated_states_list = ['read_file']

    def get_updated_states(self):
        return self.updated_states_list


    def read_file(self):
        "read_file state method"
        self.sm_fields['current_state_creation_date'] = datetime.now()
        sleep(0.002)
        return True

    def apply_regex(self):
        "apply_regex state method"
        self.sm_fields['current_state_creation_date'] = datetime.now()
        sleep(0.002)
        return True

    def save_file(self):
        "save_file state method"
        self.sm_fields['current_state_creation_date'] = datetime.now()
        sleep(0.002)
        return True

    def exit(self):
        "exit state method"
        self.sm_fields['current_state_creation_date'] = datetime.now()
        sleep(0.002)
        return True


class StateMachineTest(unittest.TestCase):
    """Unittest tests for all StateMachine's class methods"""
    @classmethod
    def setUpClass(cls):
        cls.sm = MessAroundSM(SQLITE_BASE_PATH, '001')
        cls.sm.start()
        cls.sm.sleep_interval = 0.001

    @classmethod
    def tearDownClass(cls):
        con = sql.connect(SQLITE_BASE_PATH)
        with con:
            cur = con.cursor()
            cur.execute('DELETE FROM "STATE_MACHINE"')

    def test01_check_if_thread_alive(self):
        """Tests check_if_thread_alive method """
        self.assertTrue(self.sm.check_if_thread_alive(self.sm.activity_id))

    def test02_read_file(self):
        """Tests current state read_file """
        sleep(0.15)
        self.assertEqual(self.sm.current_state, 'read_file')

    def test03_apply_regex(self):
        """Tests current state apply_regex """
        self.sm.updated_states_list.append('apply_regex')
        self.sm.update_flag = True
        sleep(0.15)
        self.assertEqual(self.sm.current_state, 'apply_regex')

    def test04_save_file(self):
        """Tests current state save_file """
        self.sm.updated_states_list.append('save_file')
        self.sm.update_flag = True
        sleep(0.15)
        self.assertEqual(self.sm.current_state, 'save_file')

    def test05_exit(self):
        """Tests current state exit """
        self.sm.updated_states_list.append('exit')
        self.sm.update_flag = True
        sleep(0.15)
        self.assertEqual(self.sm.current_state, 'exit')
        self.sm.is_finished = True
        sleep(0.15)

    def test06_check_if_thread_finished(self):
        """Tests if state machine thread happily died"""
        self.assertFalse(self.sm.check_if_thread_alive(self.sm.name))


if __name__ == "__main__":
    unittest.main()
