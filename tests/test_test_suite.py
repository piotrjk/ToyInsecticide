import random
from internals.test_suite import TestSuite
from runner import log


class TestTestSuite(TestSuite):

    def __init__(self):
        self.id = "test_test_suite_001"
        self.description = "Test description of a test test suite."
        self.labels = ["test", "suite", "first"]

    def setup(self):
        pass

    def teardown(self):
        pass

    def test_pass(self):
        assert True


class TestTestSuite2(TestSuite):

    def __init__(self):
        self.id = "test_test_suite_002"
        self.description = "Test description of a test test suite 2."
        self.labels = ["test", "suite", "second"]

    def setup(self):
        pass

    def teardown(self):
        pass

    def test_fail(self):
        assert False


class TestTestSuite3(TestSuite):

    def __init__(self):
        self.id = "test_test_suite_003"
        self.description = "Test description of a test test suite 3."
        self.labels = ["test", "suite", "third"]
        self.something = 0

    def setup(self):
        self.something = 1

    def teardown(self):
        self.something = 0

    def test_random_1(self):
        random_value = random.random()
        log.info("Something is: {}, something random is: {}".format(self.something, random_value))
        if random_value > 0.5:
            log.info("Something random is greater than 0.5")
        else:
            raise AssertionError("Something random is less than 0.5")

    def test_random_2(self):
        random_value = random.random()
        log.info("Something is: {}, something random is: {}".format(self.something, random_value))
        if random_value < 0.5:
            log.info("Something random is less than 0.5")
        else:
            raise AssertionError("Something random is greater than 0.5")




