import os
import argparse
from internals.object_library import TestOutcome, ConfigurationDatabase, ReportDatabase
import time
import pyclbr
import importlib.machinery
import importlib.util
import pathlib
import itertools
import json

import logging
from logging.config import dictConfig
from configuration.logging_conf import LOGGING_CONFIGURATION
dictConfig(LOGGING_CONFIGURATION)
log = logging.getLogger()

CONFIG_DB = None

"""
ToyInsecticide - Simple, general purpose test framework.


Copyright 2017 Piotr Koscielski

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

def get_test_suite_names(dir_path):
    # Just getting the names of the .py files containing string "suite" in .\tests directory
    return [f[:-3] for f in os.listdir(dir_path) if "suite" in f and f.endswith(".py")]


def get_test_suite_classes(dir_path):
    # Using pyclbr lib to perform a search for test suite classes in suite files.
    # They will be instantiated here and returned in a list.
    instantiated_classes = []
    for n in get_test_suite_names(dir_path):
        module_path = ".".join((dir_path, n))
        module_info = pyclbr.readmodule(module_path)
        imported_module = importlib.import_module(name=module_path)
        log.info("Found {} TestSuite class(es) in module \"{}\": {}".format(
            len(module_info.keys()), n, ", ".join(('"{}"'.format(j) for j in module_info))))
        for cls in module_info:
            instantiated_classes.append(getattr(imported_module, cls)())
    return instantiated_classes


def run_tests(test_suite_classes_list, included_labels=None, excluded_labels=None):
    # Simple filtering based on include and exclude labels (sets of string values).
    # .run() method of test suites is called, outcomes are collected and returned as a
    # dict of key = suite name, value = list of suite test outcomes.
    suite_results = {}
    for tsc in test_suite_classes_list:
        labels_set = set(tsc.labels)
        if included_labels is not None and not labels_set.intersection(set(included_labels)):
            log.info("Suite \"{}\" was skipped, it does not contain any of specified inclusion labels".format(tsc.id))
            suite_results.update({tsc.id: [TestOutcome(name=n, start_timestamp=time.time(), duration_s=0,
                                                       status_code=2, message="Skipped") for n in tsc.gather_tests()]})
            continue
        if excluded_labels is not None and labels_set.intersection(set(excluded_labels)):
            log.info("Suite \"{}\" was skipped, it contains at least one excluded label".format(tsc.id))
            suite_results.update({tsc.id: [TestOutcome(name=n, start_timestamp=time.time(), duration_s=0,
                                                       status_code=2, message="Skipped") for n in tsc.gather_tests()]})
            continue
        log.info("Running the tests from suite \"{}\"".format(tsc.id))
        suite_results.update({tsc.id: tsc.run()})
    return suite_results


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--include_labels", "-i", default=None, help="Run only test suites that include at least one"
                                                                        "of those labels - write as semicolon separated"
                                                                        "set of strings, e.g. \"label_one;label_two\"")
    argparser.add_argument("--exclude_labels", "-e", default=None, help="Exclude test suites that include at least one"
                                                                        "of those labels - write as semicolon separated"
                                                                        "set of strings, e.g. \"label_one;label_two\"")
    args = argparser.parse_args()
    include_labels = args.include_labels.split(";") if args.include_labels else None
    exclude_labels = args.exclude_labels.split(";") if args.exclude_labels else None

    log.info("Initializing configuration")
    json_config_path = pathlib.Path(".", "configuration", "config.json")  # This is the only hardcoded path
    if json_config_path.exists():
        log.info("JSON configuration exists, will update configuration database with it")
        with open(str(json_config_path), "r") as jf:
            config_dict = json.loads(jf.read(), encoding="utf-8")
        config_db = ConfigurationDatabase(str(pathlib.Path(config_dict["sqlite_db_dir"],
                                                           config_dict["configuration_db_file_name"])))
        config_db.update_many_config_values(config_dict=config_dict)
        CONFIG_DB = config_db
        # Using separate database for configuration is redundant, but I'm doing it for exercise.
    else:
        raise Exception("\"{}\" does not exist, unable to continue".format(json_config_path))

    report_database = ReportDatabase(str(pathlib.Path(CONFIG_DB.get_config_value("sqlite_db_dir"),
                                                      CONFIG_DB.get_config_value("reports_db_file_name"))))

    test_suite_classes = get_test_suite_classes(str(pathlib.Path(CONFIG_DB.get_config_value("test_dir"))))

    results = run_tests(test_suite_classes_list=test_suite_classes, included_labels=include_labels,
                        excluded_labels=exclude_labels)

    for k in results:
        log.info("Results of tests from suite \"{}\":".format(k))
        for outcome in results[k]:
            log.info(outcome)

    tests_done = [t for t in itertools.chain.from_iterable(results.values())]  # flattening the list
    passed_tests = [t for t in tests_done if t.status_code == 0]
    num_of_tests_done = len(tests_done)
    num_of_tests_passed = len(passed_tests)

    log.info("{}/{} ({:.1f}%) tests passed!".format(num_of_tests_passed, num_of_tests_done,
                                                    num_of_tests_passed/num_of_tests_done*100))
    log.info("Storing test results in the database")
    report_database.store_test_outcomes(tests_done)
    log.info("Test run done")

    # import pdb; pdb.set_trace()
