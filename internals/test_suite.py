from abc import ABC, abstractmethod
import time
from internals.object_library import TestOutcome

import logging
from logging.config import dictConfig
from configuration.logging_conf import LOGGING_CONFIGURATION
dictConfig(LOGGING_CONFIGURATION)
log = logging.getLogger("test_case")


class TestSuite(ABC):
    """
    Abstract class for test suites.
    
    The test suite must contain those attributes:
    id: unique identifier of test suite
    description: self explanatory
    labels: an iterable of string values, used for filtering
    
    It also must contain some test cases - i.e. a method with "test" string in its name.
    "setup" and "teardown" methods must be implemented as well.
    """

    @property
    def id(self):
        try:
            return getattr(self, "__id")
        except AttributeError:
            raise NotImplementedError("\"id\" property of a TestSuite must be set")

    @id.setter
    def id(self, value):
        setattr(self, "__id", value)

    @property
    def description(self):
        try:
            return getattr(self, "__description")
        except AttributeError:
            raise NotImplementedError("\"description\" property of a TestSuite must be set")

    @description.setter
    def description(self, value):
        setattr(self, "__description", value)

    @property
    def labels(self):
        try:
            return getattr(self, "__labels")
        except AttributeError:
            raise NotImplementedError("\"labels\" property of a TestSuite must be set")

    @labels.setter
    def labels(self, value):
        setattr(self, "__labels", value)

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def teardown(self):
        pass

    def gather_tests(self):
        return [t for t in dir(self) if t.startswith("test_")]

    def run(self):
        outcomes = []
        for test in self.gather_tests():
            t_zero = time.time()
            name = test
            start_timestamp = t_zero
            try:
                self.setup()
                getattr(self, test)()
                self.teardown()
            except Exception as e:
                # Test Failed
                log.exception("Encountered exception in test case {}:".format(test))
                status_code = 1
                error_msg = repr(e)
            else:
                # Test Passsed
                status_code = 0
                error_msg = None
            finally:
                duration_s = time.time() - t_zero
            outcomes.append(TestOutcome(name=name, start_timestamp=start_timestamp, duration_s=duration_s,
                                        status_code=status_code, message=error_msg))
        return outcomes
