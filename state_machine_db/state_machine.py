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
        self.logger = logging.getLogger(__name__)
        self.activity_id = activity_id
        self._sm_database_path = sm_database_path
        self.is_finished = False
        self.current_states_list = []
        self.current_state = None
        self._recovering = False
        self._external_id = None
        self._last_executed_state = None
        # MUST implement in the child class
        self._states_methods_dict = NotImplemented
        self.sm_fields = NotImplemented
        # Thread class parameters and initialization:
        threading.Thread.__init__(self)
        # If daemon = True, the thread will die with its parent
        self.daemon = True
        # Time between each thread flags checking
        self.sleep_interval = 1
        # Naming the thread
        self.name = 'state_machine_' + self.activity_id
        # flag that sinalizes an update in the state machine
        self.update_flag = False


    def _restore_state_from_db(self):
        '''
        Inspects the data base and tries to restore the thread related to
        the current activity (activity_id)

        '''
        current_state = None
        con = sql.connect(self._sm_database_path)
        con.row_factory = sql.Row
        with con:
            cur = con.cursor()
            execute = '''SELECT * FROM STATE_MACHINE WHERE `activity_id` = "'''\
                +str(self.activity_id)+'''"'''
            cur.execute(execute)
        rows = cur.fetchall()
        if rows:
            # Fetching fields from data base
            self.is_finished = ast.literal_eval(rows[0]["is_finished"].encode('utf-8'))
            if not self.is_finished:
                self._external_id = rows[0]["external_id"]
                current_state = rows[0]["current_state"].encode('utf-8')
            else:
                logging.warning('The activity with id ' + self.activity_id\
                    +' has been already finished.')
        return current_state

    def get_updated_states(self):
        '''
        This method must be implemented in the child class and return, after an
        update in the update_flag, a list of updated states
        '''
        raise NotImplementedError('This method must be implemented in the child class!')

    def __convert_str(self, str_to_cv):
        '''
        Convert a variable to string(python3) or unicode(python2) representation

        Arguments:
            str_to_cv (:obj:`str`): variable to be converted

        Returns:
            conv_str (:obj:`str` or `unicode`): 

        '''
        try:
            conv_str = unicode(str(str_to_cv.decode('utf-8')))
        except (AttributeError, NameError):
            conv_str = str(str_to_cv)
        return conv_str

    def _exec_state(self, state_to_exec):
        '''

        Execute the method described in self._states_methods_dict that
        corresponds to the state state_to_exec

        Arguments:
            state_to_exec (:obj:`string`): state that must have its methods executed.

        Returns:
            True if all methods were executed successfully, False otherwise

        '''
        if self._states_methods_dict:
            self.logger.debug('The following state will be executed: '+state_to_exec)
            if state_to_exec in self._states_methods_dict:
                self.logger.debug('Executing state '+state_to_exec)
                try:
                    ret = self._states_methods_dict[state_to_exec]['method']()
                except Exception as error:
                    self.logger.error('Error '+str(error)+\
                        ' while executing state '+state_to_exec)
                    return False
                else:
                    if not ret:
                        self.logger.error("Error while executing stage "\
                                +state_to_exec+" from "+" activity's id "\
                                +self.activity_id+". Its thread will be finished.")
                        return False
            else:
                self.logger.warning('The method corresponding to state '+state_to_exec\
                    +' is not implemented. It must be done in the super class.')
                return False
            self._save_state_to_db(state_to_exec)
            return True
        else:
            self.logger.error('Error! You must fill properly the states`s methods'\
                +' dictionary self._states_methods_dict in the super class!')
            return False

    def __check_activity_in_db(self):
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
                + self.activity_id+"'")
        rows = cur.fetchall()
        return True if rows else False

    def _save_state_to_db(self, current_state):
        '''

        Saves necessary fields of this activity into the database, in table STATE_MACHINE

        '''
        entry_exist = self.__check_activity_in_db()
        con = sql.connect(self._sm_database_path)
        self.logger.debug('Saving activity '+self.activity_id+' state to database')
        self.current_state = current_state
        with con:
            cur = con.cursor()
            if not entry_exist:
                sm_table_fields_list = [
                    self.__convert_str(self.sm_fields['activity_name']),  # activity_name
                    self.__convert_str(self.is_finished),  # is_finished
                    self.__convert_str(current_state),  # current_state
                    self.__convert_str(self.activity_id),  # activity_id
                    self.__convert_str((self.sm_fields['activity_creation_date']).strftime(
                        "%Y-%m-%d %H:%M:%S")),  # creationDate
                    self.__convert_str(self.sm_fields['current_state_creation_date'].\
                        strftime("%Y-%m-%d %H:%M:%S")),
                    self.__convert_str(self._external_id)  # external_id
                ]
                cur.execute("INSERT INTO STATE_MACHINE VALUES("\
                    +'"'+'", "'.join(sm_table_fields_list)+'"'+")")
            else:
                cur.execute("UPDATE STATE_MACHINE SET "\
                    +"current_state = '"+self.__convert_str(current_state)+"',"\
                    +"is_finished = '"+self.__convert_str(self.is_finished)+"',"\
                    +"current_state_creation_date = '"\
                        +self.__convert_str(self.sm_fields['current_state_creation_date'].\
                        strftime("%Y-%m-%d %H:%M:%S"))+"',"\
                    +"external_id = '"+self.__convert_str(self._external_id)+"' "\
                    +"WHERE activity_id = '" + self.__convert_str(self.activity_id)+"'")

    def _synchronize_states(self):
        '''
        Initializes the list of states to be executed and restore the
        machine state from database if it was interrupted before

        '''

        self.logger.info("Synchronizing activity's id "+self.activity_id+" ...")
        states_list = self.get_updated_states()
        restored_current_state = self._restore_state_from_db()
        self.update_flag = False
        if not self.is_finished:
            if not restored_current_state == states_list[-1]:
                if restored_current_state:
                    states_to_exec_list = states_list[states_list.index(restored_current_state)+1:]
                else:
                    states_to_exec_list = states_list
                for state in states_to_exec_list:
                    ret = self._exec_state(state)
                    if not ret:
                        return False
                    self._last_executed_state = state
            else:
                self._last_executed_state = restored_current_state
        return True

    def _execute_current_actions(self):
        '''
        Updates the list of states and executes those which
        was not exected before

        '''
        self.update_flag = False
        states_list = self.get_updated_states()
        if not self.is_finished:
            if not self._last_executed_state == states_list[-1]:
                states_to_exec_list = states_list[states_list.index(self._last_executed_state)+1:]
                for state in states_to_exec_list:
                    ret = self._exec_state(state)
                    if not ret:
                        return False
                    self._last_executed_state = state
        else:
            self.logger.info("Activity's id "+self.activity_id+" thread is finished.")
        return True

    def run(self):
        '''
        Initiates the thread that effectivelly implements the state machine.
        A change of state must be sinalized by a flag (update, must be True)
        The final state must be sinalized by a flag (is_finished, must be True)

        '''
        if self.sm_fields == NotImplemented:
            raise NotImplementedError('Must implement sm_fields dictionary in the child class!')
        if self._states_methods_dict == NotImplemented:
            raise NotImplementedError('Must implement _states_methods_dict dictionary'\
                                      +'in the child class!')
        if not self._synchronize_states():
            return
        while not self.is_finished:
            mlock = threading.RLock()
            with mlock:
                if self.update_flag:
                    if not self._execute_current_actions():
                        return
            sleep(self.sleep_interval)
        self.logger.info("Activity's id "+self.activity_id+" thread is finished.")

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
