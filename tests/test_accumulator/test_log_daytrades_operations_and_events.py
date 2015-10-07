"""Tests the logging of Operation, Daytrade and Event objects."""

from __future__ import absolute_import
import unittest

import trade
import trade.plugins

from tests.fixtures.operations import (
    ASSET, OPERATION1, OPERATION18, DAYTRADE2, DAYTRADE3,
)
from tests.fixtures.events import (
    EVENT0, EVENT1, EVENT2,
)
from . fixture_logs import (
    EXPECTED_LOG19, EXPECTED_LOG20, EXPECTED_LOG21
)


class TestLogDaytradesOperationsAndEvents(unittest.TestCase):

    def setUp(self):
        self.accumulator = trade.Accumulator(ASSET, logging=True)


class TestLogDaytradesOperationsAndEventsCase00(
        TestLogDaytradesOperationsAndEvents):
    """Test logging events, operations and daytrades on the same date."""

    def setUp(self):
        super(TestLogDaytradesOperationsAndEventsCase00, self).setUp()
        self.accumulator.accumulate(DAYTRADE2)
        self.accumulator.accumulate(OPERATION18)
        self.accumulator.accumulate(EVENT0)

    def test_log(self):
        self.assertEqual(self.accumulator.log, EXPECTED_LOG19)


class TestLogDaytradesOperationsAndEventsCase01(
        TestLogDaytradesOperationsAndEvents):
    """Test logging all objects on the different dates."""

    def setUp(self):
        super(TestLogDaytradesOperationsAndEventsCase01, self).setUp()
        self.accumulator.accumulate(DAYTRADE2)
        self.accumulator.accumulate(OPERATION1)
        self.accumulator.accumulate(EVENT1)

    def test_log(self):
        self.assertEqual(self.accumulator.log, EXPECTED_LOG20)


class TestLogDaytradesOperationsAndEventsCase02(
        TestLogDaytradesOperationsAndEvents):
    """Test logging objects on different dates."""

    def setUp(self):
        super(TestLogDaytradesOperationsAndEventsCase02, self).setUp()
        self.accumulator.accumulate(DAYTRADE2)
        self.accumulator.accumulate(OPERATION1)
        self.accumulator.accumulate(DAYTRADE3)
        self.accumulator.accumulate(EVENT2)

    def test_log(self):
        self.assertEqual(self.accumulator.log, EXPECTED_LOG21)
