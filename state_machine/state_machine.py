# coding: utf-8
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
        self.logger = logging.getLogger('state_machine.StateMachine')
        self._activity_id = activity_id
        self._sm_database_path = sm_database_path
        self.is_finished = False
        self.present_state = None
        self.__execution_state = None
        self._external_id = None
        # MUST implement in the child class
        self._states_methods_dict = {}
        self.__states_to_exec_name_list = []
        self.__sm_fields = self.get_present_sm_fields()
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

    def __restore_state_from_db(self):
        '''

        Inspects the data base and tries to restore the thread related to
        the present activity (activity_id)

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
        if rows:
            self.is_finished = ast.literal_eval(rows[0]["is_finished"].encode('utf-8'))
            if not self.is_finished:
                self.present_state = rows[0]["present_state"].encode('utf-8')
                self._external_id = rows[0]["external_id"]
                states_list = self._states_methods_dict.keys()
                states_to_exec_list = states_list[(states_list.index(self.present_state) + 1):]
                for state in states_to_exec_list:
                    if not state in self.__states_to_exec_name_list:
                        self.__states_to_exec_name_list.append(state)
        else:
            self.__update_states_to_execute()

    def __update_states_to_execute(self):
        '''

        Updates the list of states' actions that must be executed

        '''
        states_list = self._states_methods_dict.keys()
        states_to_exec_list = states_list[
            (states_list.index(self.present_state) + 1):] if self.present_state else states_list
        for state in states_to_exec_list:
            if not state in self.__states_to_exec_name_list:
                self.__states_to_exec_name_list.append(state)

    def __exec_states_list(self, states_to_exec_name_list=None):
        '''

        Executes all methods described in self._states_methods_dict that
        corresponds to states listed in states_to_exec_name_list

        Arguments:
            states_to_exec_name_list (:obj:`list`, *default* = self.__states_to_exec_name_list):
                list containing the states that must have its methods executed
            activity_id (:obj:`str`): identifier for the current state
                machine instance

        Returns:
            True if all methods were executed successfully, False otherwise

        '''
        self.logger.debug('Executing activity '+self.activity_id+' states list')
        if self._states_methods_dict:
            states_to_exec_name_list = states_to_exec_name_list \
                if states_to_exec_name_list else self.__states_to_exec_name_list
            self.logger.debug('The following states: will be executed: '\
                +', '.join(states_to_exec_name_list))
            # these [:] make the loop be done over a copy of the
            # original list
            for state in states_to_exec_name_list[:]:
                self.__execution_state = state
                if state in self._states_methods_dict:
                    self.logger.debug('Executing state '+state)
                    try:
                        ret = self._states_methods_dict[state]['method']()
                    except Exception as error:
                        self.logger.error('Error '+str(error)+' while executing state '+state)
                        return False
                    else:
                        if ret:
                            self.present_state = state
                            self.__states_to_exec_name_list.remove(self.present_state)
                            self.save_state_to_db()
                        else:
                            return False
                else:
                    self.log.warning('The method corresponding to state '+state+' is not '\
                        +' implemented. It must be done in the super class.')
                    return False
            return True
        else:
            self.logger.error('Error! You must fill properly the states`s methods'\
                +' dictionary self._states_methods_dict in the super class!')
            return False

    @staticmethod
    def get_present_sm_fields():
        '''

        Fetches user provided data in order to fill necessary fields
        for the correct execution of the states methods of the current
        activity

        Returns:
            dictionary containing activity related necessary fields
            properly filled
        '''
        # MUST be overloaded in the super class
        present_sm_fields_dict = {}
        return present_sm_fields_dict

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
            cur.execute("SELECT * FROM STATE_MACHINE WHERE `activity_id` = " \
                + self._activity_id)
        rows = cur.fetchall()
        return True if rows else False

    def save_state_to_db(self):
        '''

        Saves necessary fields of this activity into the database, in table STATE_MACHINE

        '''
        entry_exist = self.__check_activity_in_db()
        con = sql.connect(self._sm_database_path)
        self.logger.debug('Saving activity '+self.activity_id+' state to database')
        with con:
            cur = con.cursor()
            if not entry_exist:
                sm_table_fields_list = [
                    self.__sm_fields['activity_name'].decode(),  # activity_name
                    unicode(self.present_state.decode('utf-8')),  # present_state
                    str(self.is_finished).decode(),  # is_finished
                    str(self._activity_id),  # activity_id
                    (self.__sm_fields['activity_creation_date']).strftime(
                        "%Y-%m-%d %H:%M:%S").decode(),  # creationDate
                    self.__sm_fields['present_state_creation_date'].\
                        strftime("%Y-%m-%d %H:%M:%S").decode(),
                    str(self._external_id)  # _external_id
                ]
                cur.execute("INSERT INTO STATE_MACHINE VALUES("\
                    +', '.join(sm_table_fields_list)+")")
            else:
                cur.execute("UPDATE STATE_MACHINE SET "\
                    +"activity_name = "+self.__sm_fields['activity_name'].decode()+","\
                    +"present_state = "+unicode(self.present_state.decode('utf-8'))+","\
                    +"is_finished = "+str(self.is_finished).decode()+","\
                    +"activity_id = "+str(self._activity_id)+","\
                    +"activity_creation_date = "+self.__sm_fields['activity_creation_date']+","\
                    +"present_state_creation_date = "\
                        +self.__sm_fields['present_state_creation_date']+","\
                    +"external_id = "+str(self._external_id)+","\
                    +"WHERE activity_id = " + self._activity_id)

    def __update_state_action(self):
        '''

        Updates the list of states that must de executed

        '''
        self.__sm_fields = self.get_present_sm_fields()
        self.__update_states_to_execute()

    def run(self):
        '''

        Initiates the thread that effectivelly implements the state machine.
        A change of state must be sinalized by a flag (update, must be True)
        The final state must be sinalized by a flag (is_finished, must be True)

        '''
        self.__restore_state_from_db()
        if self.is_finished:
            logging.warning('The activity with id ' + self._activity_id\
                +' has been already finished.')
            return
        self.__sm_fields = self.get_present_sm_fields()
        ret = self.__exec_states_list()
        if not ret:
            self.logger.error("Error while executing stage "+self.__execution_state+" from "\
                    +" activity's id "+self._activity_id+". Its thread will be finished.")
            return
        while not self.is_finished:
            mlock = threading.RLock()
            with mlock:
                if self.update_flag:
                    self.__update_state_action()
                    ret = self.__exec_states_list()
                    if not ret:
                        self.logger.error("Error while executing stage "\
                            +self.__execution_state+" from activity's id "\
                            +self._activity_id+". Its thread will be finished.")
                        return
                    self.update_flag = False
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
