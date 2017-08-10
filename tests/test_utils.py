#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# @source source.module
# @version 1.0.0
# @copyright (c) 2016-present Joivy Ltd.

import datetime
import itertools
import unittest
from types import FloatType

from gaesd import DuplicateSpanEntryError, InvalidSliceError, NoDurationError, SDK
from gaesd.core.utils import datetime_to_float, datetime_to_timestamp, \
    find_spans_with_duration_less_than


class TestUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.project_id = 'my-project'
        self.sdk = SDK.new(project_id=self.project_id, auto=False)
        self.sdk.clear(traces=True, enabler=True, dispatcher=True, loggers=True)

    def tearDown(self):
        SDK.clear(loggers=True)

    def test_NoDurationError(self):
        span = self.sdk.current_span
        try:
            raise NoDurationError(span)
        except NoDurationError as e:
            self.assertIs(e.span, span)
            self.assertEqual(e.message, 'Span has no duration ({start_time} -> {end_time})'.format(
                start_time=span.start_time, end_time=span.end_time))

    def test_InvalidSliceError(self):
        s = 123
        try:
            raise InvalidSliceError(s)
        except InvalidSliceError as e:
            self.assertIs(e.slice, s)
            self.assertEqual(e.message, 'Invalid slice {s}'.format(s=s))

    def test_DuplicateSpanEntryError(self):
        span = self.sdk.current_span
        try:
            raise DuplicateSpanEntryError(span)
        except DuplicateSpanEntryError as e:
            self.assertIs(e.span, span)
            self.assertEqual(e.message, 'Already entered this span\'s context: {span}'.format(
                span=span))

    def test_datetime_to_timestamp(self):
        dt = datetime.datetime.utcnow()

        self.assertEqual(datetime_to_timestamp(dt), '{0}Z'.format(dt.isoformat('T')))
        self.assertEqual(datetime_to_timestamp(None), None)

    def test_datetime_to_float(self):
        SECONDS_IN_A_DAY = (60 * 60 * 24)
        epoch = datetime.datetime.utcfromtimestamp(0)
        epoch_plus_one_day = epoch + datetime.timedelta(seconds=SECONDS_IN_A_DAY)
        self.assertIsInstance(epoch_plus_one_day, datetime.datetime)

        result = datetime_to_float(epoch_plus_one_day)
        self.assertEqual(result, SECONDS_IN_A_DAY)
        self.assertIsInstance(result, FloatType)

    def test_find_spans_with_duration_less_than_duration_is_int(self):
        l = 10
        duration = 5
        end_time = datetime.datetime.utcnow()
        type_changer = itertools.cycle([int, float])

        def change_type(i):
            return type_changer.next()(i)

        spans = []
        for index in range(l):
            span = self.sdk.span()
            # Make sure some spans raise NoDurationError when duration is called on them:
            if index % 3 != 0:
                span._start_time = end_time - datetime.timedelta(seconds=change_type(index))
            if index % 4 != 0:
                span._end_time = end_time
            spans.append(span)

        result = find_spans_with_duration_less_than(spans, duration)
        self.assertEqual(len(result), 3)


if __name__ == '__main__':
    unittest.main()
