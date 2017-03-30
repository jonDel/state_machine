'''
    This module implements a state machine that waits for flags to
    jump from state to state until it is finished

'''

import sqlite3 as sql
import ast
import threading
from time import sleep
import logging


class StateMachine(threading.Thread):
    '''

    Implements a totally configurable state machine

    Arguments:
        sm_database_path (:obj:`str`): path to the sqlite database
        activity_id (:obj:`str`): identifier for the current state
            machine instance

        '''
    def __init__(self, sm_database_path, activity_id):
        self.logger = logging.getLogger('state_machine'+'.'+str(activity_id))
        self._activity_id = activity_id
        self._sm_database_path = sm_database_path
        self._is_finished = False
        self._states_to_exec_list = []
        self._all_states_list = []
        self._recovering = False
        self._previous_state = None
        self._current_state = None
        self._next_state = None
        self.actual__current_state = None
        self._external_id = None
        # MUST implement in the child class
        self._states_methods_dict = {}
        self._states_to_exec_name_list = []
        self._sm_fields = {}
        # Thread class parameters and initialization:
        threading.Thread.__init__(self)
        # If daemon = True, the thread will die with its parent
        self.daemon = True
        # Time between each thread flags checking
        self.sleep_interval = 1
        # Naming the thread
        self.name = 'state_machine_' + self._activity_id
        # flag that sinalizes an update in the state machine
        self.update_flag = False

    def _restore_state_from_db(self):
        '''

        Inspects the data base and tries to restore the thread related to
        the current activity (activity_id)

        '''
        con = sql.connect(self._sm_database_path)
        con.row_factory = sql.Row
        with con:
            cur = con.cursor()
            execute = '''SELECT * FROM STATE_MACHINE WHERE `activity_id` = "'''\
                +str(self._activity_id)+'''"'''
            cur.execute(execute)
        rows = cur.fetchall()
        # Fetching fields from data base
        self._is_finished = ast.literal_eval(rows[0]["_is_finished"].encode('utf-8'))
        if not self._is_finished:
            self._recovering = True
            self._previous_state = rows[0]["_current_state"].encode('utf-8')
            self._current_state = rows[0]["_next_state"].encode('utf-8')
            self._external_id = rows[0]["external_id"]
            # Getting next state index
            ns_idx = self._all_states_list.index(self._current_state)+1
            # Checking if there is a next state, else set to none
            if not ns_idx > len(self._all_states_list) -1:
                self._next_state = self._all_states_list[ns_idx]
            else:
                self._next_state = None
            states_list = list(self._states_methods_dict.keys())
            curr_st_idx = states_list.index(self._current_state)
            # if actual__current_state exists, it means that there was an
            # external update in the current state machine state, i.e,
            # we must forward the state machine from the _current_state recovered from the
            # database to the actual__current_state
            if self.actual__current_state in states_list:
                act_curr_st_idx = states_list.index(self.actual__current_state)
                self._states_to_exec_list = states_list[curr_st_idx:act_curr_st_idx+1]
            else:
                self._states_to_exec_list = [self._current_state]
        else:
            logging.warning('The activity with id ' + self._activity_id\
                +' has been already finished.')

    def _update_states(self):
        '''

        Update each state: _current_state becomes _previous_state,
        _next_state becomes _current_state and _next_state is replaced
        by the first state after _current_state in _states_to_exec_list.
        The flag _is_finished is updated too if the last executed state is the
        last in _states_to_exec_list

        '''
        # If current state is the last state
        # update the states accordingly
        if self._current_state == self._all_states_list[-1]:
            self._is_finished = True
        else:
            self._previous_state = self._current_state
            self._current_state = self._next_state
            ns_idx = self._all_states_list.index(self._current_state)+1
            # If next state is the last, state
            # update the states accordingly
            if not ns_idx >= len(self._all_states_list):
                self._next_state = self._all_states_list[ns_idx]
            else:
                self._next_state = None

    def __convert_str(self, str_to_cv):
        try:
            conv_str = unicode(str_to_cv.decode('utf-8'))
        except (AttributeError, NameError):
            conv_str = str(str_to_cv)
        return conv_str

    def _exec_state(self, state_to_exec_name=None):
        '''

        Executes all methods described in self._states_methods_dict that
        corresponds to states listed in states_to_exec_name_list

        Arguments:
            state_to_exec_name (:obj:`string`, *default* = None):
                state that must have its methods executed. If not given, self._current_state
                is used instead.

        Returns:
            True if all methods were executed successfully, False otherwise

        '''
        self.update_flag = False
        if self._states_methods_dict:
            self.logger.debug('The following state will be executed: '+self._current_state)
            if self._current_state in self._states_methods_dict:
                self.logger.debug('Executing state '+self._current_state)
                try:
                    ret = self._states_methods_dict[self._current_state]['method']()
                except Exception as error:
                    self.logger.error('Error '+str(error)+\
                        ' while executing state '+self._current_state)
                    return False
                else:
                    if not ret:
                        self.logger.error("Error while executing stage "\
                                +self._current_state+" from "+" activity's id "\
                                +self._activity_id+". Its thread will be finished.")
                        return False
            else:
                self.logger.warning('The method corresponding to state '+self._current_state\
                    +' is not implemented. It must be done in the super class.')
                return False
            self._save_state_to_db()
            self._update_states()
            return True
        else:
            self.logger.error('Error! You must fill properly the states`s methods'\
                +' dictionary self._states_methods_dict in the super class!')
            return False

    def _check_activity_in_db(self):
        '''
        Checks if there is an entry in table STATE_MACHINE in the database corresponding
        to this activity_id

        Returns:
            True if there is an entry, False otherwise

        '''
        con = sql.connect(self._sm_database_path)
        with con:
            cur = con.cursor()
            cur.execute("SELECT * FROM STATE_MACHINE WHERE `activity_id` = '" \
                + self._activity_id+"'")
        rows = cur.fetchall()
        return True if rows else False

    def _save_state_to_db(self):
        '''

        Saves necessary fields of this activity into the database, in table STATE_MACHINE

        '''
        entry_exist = self._check_activity_in_db()
        con = sql.connect(self._sm_database_path)
        self.logger.debug('Saving activity '+self._activity_id+' state to database')
        with con:
            cur = con.cursor()
            if not entry_exist:
                sm_table_fields_list = [
                    self.__convert_str(self._sm_fields['activity_name']),  # activity_name
                    self.__convert_str(self._is_finished),  # is_finisheda
                    self.__convert_str(self._previous_state)\
                        if self._previous_state else str(self._previous_state),  # previous_state
                    self.__convert_str(self._current_state)\
                        if self._current_state else str(self._current_state),  # current_state
                    self.__convert_str(self._next_state)\
                        if self._next_state else str(self._next_state), # next_state
                    str(self._activity_id),  # activity_id
                    self.__convert_str((self._sm_fields['activity_creation_date']).strftime(
                        "%Y-%m-%d %H:%M:%S")),  # creationDate
                    self.__convert_str(self._sm_fields['current_state_creation_date'].\
                        strftime("%Y-%m-%d %H:%M:%S")),
                    str(self._external_id)  # external_id
                ]
                cur.execute("INSERT INTO STATE_MACHINE VALUES("\
                    +'"'+'", "'.join(sm_table_fields_list)+'"'+")")
            else:
                cur.execute("UPDATE STATE_MACHINE SET "\
                    +"previous_state = '"+(self.__convert_str(self._previous_state)\
                        if self._previous_state else str(self._previous_state))+"',"\
                    +"current_state = '"+(self.__convert_str(self._current_state)\
                        if self._current_state else str(self._current_state))+"',"\
                    +"next_state = '"+(self.__convert_str(self._next_state)\
                        if self._next_state else str(self._next_state))+"',"\
                    +"is_finished = '"+self.__convert_str(str(self._is_finished))+"',"\
                    +"current_state_creation_date = '"\
                        +self.__convert_str(self._sm_fields['current_state_creation_date'].\
                        strftime("%Y-%m-%d %H:%M:%S"))+"',"\
                    +"external_id = '"+str(self._external_id)+"' "\
                    +"WHERE activity_id = '" + self._activity_id+"'")

    def _initial_configs(self):
        '''
        Initializes the list of states to be executed and restore the
        machine state from datebase if it was interrupted before

        '''
        self._all_states_list = list(self._states_methods_dict.keys())
        if self._check_activity_in_db():
            self._restore_state_from_db()
        else:
            self._current_state = self._all_states_list[0]
            self._states_to_exec_list = [self._current_state]
            if len(self._all_states_list) > 1:
                ns_idx = self._all_states_list.index(self._current_state)+1
                self._next_state = self._all_states_list[ns_idx]

    def run(self):
        '''

        Initiates the thread that effectivelly implements the state machine.
        A change of state must be sinalized by a flag (update, must be True)
        The final state must be sinalized by a flag (_is_finished, must be True)

        '''
        def _execute_current_action(self):
            if self._recovering and self.update_flag:
                for _ in self._states_to_exec_list:
                    ret = self._exec_state()
                    if not ret:
                        self._recovering = False
                        return False
                self._recovering = False
            elif self.update_flag:
                return self._exec_state()
            return True

        self._initial_configs()
        while not self._is_finished:
            mlock = threading.RLock()
            with mlock:
                if not _execute_current_action(self):
                    return
            sleep(self.sleep_interval)
        self.logger.info("Activity's id "+self._activity_id+" thread is finished.")

    @staticmethod
    def check_if_thread_alive(activity_id):
        '''
        Checks if there is a thread related to activity_id

        Arguments:
            activity_id (:obj:`str`): identifier for the current state
                machine instance

        Returns:
            True if there is a thread, False otherwise

        '''
        for mthread in threading.enumerate():
            if 'state_machine_'+activity_id in mthread.name:
                return True
        return False

    @staticmethod
    def get_sm_alive_threads():
        '''
        Get info about all running threads related to state machine

        Returns:
            A dictionary containing the name of each running thread and its thread object
        '''
        threads_dict = {}
        for mthread in threading.enumerate():
            if 'state_machine_' in mthread.name:
                threads_dict[mthread.name] = mthread
        return threads_dict
