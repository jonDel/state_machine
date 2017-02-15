import unittest
from state_machine import StateMachine
import sqlite3 as sql
import os
from datetime import datetime
from time import sleep
from collections import OrderedDict

SQLITE_FILE = 'tests_sm_db.sqlite'
SQLITE_BASE_PATH = os.path.abspath(SQLITE_FILE)
if not os.path.isfile(SQLITE_BASE_PATH):
    path_split = SQLITE_BASE_PATH.split('/')
    SQLITE_BASE_PATH = '/'.join(path_split[:-1])+'/tests/'+SQLITE_FILE

class MessAroundSM(StateMachine):
    def __init__(self, sqlite_bp, activity_id):
        super(MessAroundSM, self).__init__(sqlite_bp, activity_id)
        self._states_methods_dict = OrderedDict()
        self._states_methods_dict['read_file']={'method':self.read_file}
        self._states_methods_dict['apply_regex']={'method':self.apply_regex}
        self._states_methods_dict['save_file']={'method':self.save_file}
        self._states_methods_dict['exit']={'method':self.exit}
        self.__states_to_exec_name_list = []
        self._sm_fields = {'activity_creation_date':datetime.now(),
                           'activity_name': 'mess_around_a_bit'}
        self.activity_creation_date = datetime.now()


    def read_file(self):
        self._sm_fields['current_state_creation_date'] = datetime.now()
        sleep(0.002)
        return True

    def apply_regex(self):
        self._sm_fields['current_state_creation_date'] = datetime.now()
        sleep(0.002)
        return True

    def save_file(self):
        self._sm_fields['current_state_creation_date'] = datetime.now()
        sleep(0.002)
        return True

    def exit(self):
        self._sm_fields['current_state_creation_date'] = datetime.now()
        sleep(0.002)
        return True


class StateMachineTest(unittest.TestCase):
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
        self.assertTrue(self.sm.check_if_thread_alive(self.sm._activity_id))

    def test02_read_file(self):
        self.assertEqual(self.sm._current_state, 'read_file')

    def test03_apply_regex(self):
        self.sm.update_flag= True
        sleep(0.15)
        self.assertEqual(self.sm._current_state, 'apply_regex')

    def test04_save_file(self):
        self.sm.update_flag= True
        sleep(0.15)
        self.assertEqual(self.sm._current_state, 'save_file')

    def test05_exit(self):
        self.sm.update_flag= True
        sleep(0.15)
        self.assertEqual(self.sm._current_state, 'exit')
        self.sm.update_flag= True
        sleep(0.15)
        self.assertTrue(self.sm._is_finished)

    def test06_check_if_thread_finished(self):
        self.assertFalse(self.sm.check_if_thread_alive(self.sm.name))


if __name__ == "__main__":
    unittest.main()
