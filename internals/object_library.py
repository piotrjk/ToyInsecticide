from collections import namedtuple
import datetime
import sqlite3

import logging

log = logging.getLogger()

STATUS_CODES = {
    0: "pass",
    1: "fail",
    2: "skip"
}


class TestOutcome(namedtuple('TestOutcome', ("name", "start_timestamp", "duration_s", "status_code", "message"))):
    def __repr__(self):
        return "TestOutcome(name: \"{}\", start time: {}, duration: {:.2f} seconds, " \
               "status code: {} ({}), message: \"{}\")".format(self.name,
                                                               datetime.datetime.fromtimestamp(self.start_timestamp),
                                                               self.duration_s, self.status_code,
                                                               STATUS_CODES.get(self.status_code, "unknown"),
                                                               self.message)


class SQLiteDatabase(object):
    """
    Simple abstraction layer for SQLite database interactions.
    """

    def __init__(self, db_file_name, *args, **kwargs):
        self.connection = sqlite3.connect(db_file_name, *args, **kwargs)
        self.cursor = self.connection.cursor()

    def execute(self, query_string, *args, **kwargs):
        with self.connection:
            self.cursor.execute(query_string, *args, **kwargs)

    def execute_and_fetchone(self, query_string, *args, **kwargs):
        with self.connection:
            self.cursor.execute(query_string, *args, **kwargs)
            return self.cursor.fetchone()

    def execute_and_fetchall(self, query_string, *args, **kwargs):
        with self.connection:
            self.cursor.execute(query_string, *args, **kwargs)
            return self.cursor.fetchall()

    def fetchone(self):
        with self.connection:
            return self.cursor.fetchone()

    def fetchall(self):
        with self.connection:
            return self.cursor.fetchall()

    def wipe_table(self, table_name):
        with self.connection:
            self.cursor.execute("DELETE FROM {};".format(table_name))
        self.cursor.execute("VACUUM;")

    def get_table(self, table_name):
        return self.execute_and_fetchall("SELECT * FROM {};".format(table_name))


class ConfigurationDatabase(SQLiteDatabase):
    """
    Configuration database consists of only one table with columns K = keys and V = values, both TEXT.
    """

    def __init__(self, config_db_file, table_name="CONFIG", *args, **kwargs):
        super(ConfigurationDatabase, self).__init__(db_file_name=config_db_file, *args, **kwargs)
        self.table_name = table_name
        # find out if the table is existing
        self.execute("SELECT NAME FROM SQLITE_MASTER WHERE TYPE='table';")
        if not self.fetchone():
            log.info("Database is not initialized with a table named \"{}\", will create it".format(table_name))
            self.execute("CREATE TABLE {} (K TEXT PRIMARY KEY NOT NULL, V TEXT);".format(table_name))

    def get_config_value(self, item_name):
        v = self.execute_and_fetchone("SELECT V FROM {} WHERE K=?;".format(self.table_name), (item_name,))
        if v:
            return v[0]

    def update_one_config_value(self, item_name, value):
        self.execute("REPLACE INTO {} (K, V) VALUES(?, ?);".format(self.table_name), (item_name, value))

    def update_many_config_values(self, config_dict):
        with self.connection:
            for k, v in config_dict.items():
                self.cursor.execute("REPLACE INTO {} (K, V) VALUES(?, ?);".format(self.table_name), (k, v))

    def get_config_as_dict(self):
        return dict(self.execute_and_fetchall("SELECT * FROM {};".format(self.table_name)))


class ReportDatabase(SQLiteDatabase):
    """
    Database for storing test outcomes, in one table.
    """

    def __init__(self, report_db_file, table_name="REPORT", *args, **kwargs):
        super(ReportDatabase, self).__init__(db_file_name=report_db_file, *args, **kwargs)
        self.table_name = table_name
        # find out if the table is existing
        self.execute("SELECT NAME FROM SQLITE_MASTER WHERE TYPE='table';")
        if not self.fetchone():
            log.info("Database is not initialized with a table named \"{}\", will create it".format(table_name))
            self.execute("CREATE TABLE {} (NAME TEXT NOT NULL, START_TIMESTAMP REAL, DURATION_S REAL,"
                         "STATUS_CODE INT, MESSAGE TEXT);".format(table_name))

    def store_test_outcomes(self, test_outcomes):
        with self.connection:
            for test_outcome in test_outcomes:
                self.cursor.execute("INSERT INTO {} (NAME, START_TIMESTAMP, DURATION_S, STATUS_CODE, MESSAGE)"
                                    "VALUES (?, ?, ?, ?, ?);".format(self.table_name), (test_outcome.name,
                                                                                        test_outcome.start_timestamp,
                                                                                        test_outcome.duration_s,
                                                                                        test_outcome.status_code,
                                                                                        test_outcome.message))
