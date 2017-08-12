#!/usr/bin/env python
# -*- coding: latin-1 -*-

import datetime
import itertools
import random
import unittest

import six

from gaesd import (DuplicateSpanEntryError, InvalidSliceError, NoDurationError, SDK)
from gaesd.core.utils import (
    datetime_to_float, datetime_to_timestamp, find_spans_in_datetime_range,
    find_spans_in_float_range, find_spans_with_duration_less_than,
)
from tests import PROJECT_ID


class TestUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.project_id = PROJECT_ID
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
            self.assertEqual(str(e), 'Span has no duration ({start_time} -> {end_time})'.format(
                start_time=span.start_time, end_time=span.end_time))

    def test_InvalidSliceError(self):
        s = 123
        try:
            raise InvalidSliceError(s)
        except InvalidSliceError as e:
            self.assertIs(e.slice, s)
            self.assertEqual(str(e), 'Invalid slice {s}'.format(s=s))

    def test_DuplicateSpanEntryError(self):
        span = self.sdk.current_span
        try:
            raise DuplicateSpanEntryError(span)
        except DuplicateSpanEntryError as e:
            self.assertIs(e.span, span)
            self.assertEqual(str(e), 'Already entered this span\'s context: {span}'.format(
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
        self.assertIsInstance(result, float)

    def test_find_spans_with_duration_less_than_duration_is_int(self):
        l = 10
        duration = 5
        end_time = datetime.datetime.utcnow()
        type_changer = itertools.cycle([int, float])

        def change_type(i):
            if six.PY2:
                return type_changer.next()(i)
            else:
                return type_changer.__next__()(i)

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

    def test_find_spans_in_datetime_range_no_range_specified(self):
        l = 10
        end_time = datetime.datetime.utcnow()

        spans = []

        for index in range(l):
            span = self.sdk.span()
            span._start_time = end_time - datetime.timedelta(seconds=index)
            span._end_time = end_time
            spans.append(span)

        result = find_spans_in_datetime_range(spans)
        self.assertEqual(spans, result)

    def test_find_spans_in_datetime_range_no_endtime_specified(self):
        l = 10
        start_time = datetime.datetime.utcnow()
        end_time = start_time + datetime.timedelta(seconds=60)
        spans = []
        start_times = []

        for index in range(l):
            span = self.sdk.span()
            start_time = start_time + datetime.timedelta(seconds=index)
            start_times.append(start_time)
            span._start_time = start_times[-1]
            span._end_time = end_time
            spans.append(span)

        i = random.randint(0, l - 1)
        result = find_spans_in_datetime_range(spans, from_=start_times[i])
        self.assertEqual(len(result), l - i)
        self.assertEqual(spans[i:], result)

    def test_find_spans_in_datetime_range_no_starttime_specified(self):
        l = 10
        start_time = datetime.datetime.utcnow()
        spans = []
        end_times = []

        for index in range(l):
            span = self.sdk.span()
            end_time = start_time + datetime.timedelta(seconds=index)
            end_times.append(end_time)
            span._start_time = start_time
            span._end_time = end_time
            spans.append(span)

        i = random.randint(0, l - 1)
        result = find_spans_in_datetime_range(spans, to_=end_times[i])
        self.assertEqual(len(result), i)
        self.assertEqual(spans[:i], result)

    def test_find_spans_in_datetime_range(self):
        l = 10
        start_time = datetime.datetime.utcfromtimestamp(0)
        spans = []

        for from_, to_ in [
            (start_time,
                start_time + datetime.timedelta(seconds=30)),
            (start_time + datetime.timedelta(seconds=10),
                start_time + datetime.timedelta(seconds=30)),
            (start_time + datetime.timedelta(seconds=10),
                start_time + datetime.timedelta(seconds=40)),
            (start_time + datetime.timedelta(seconds=20),
                start_time + datetime.timedelta(seconds=50)),
            (start_time + datetime.timedelta(seconds=30),
                start_time + datetime.timedelta(seconds=60)),
            (start_time + datetime.timedelta(seconds=50),
                start_time + datetime.timedelta(seconds=60)),
            (start_time + datetime.timedelta(seconds=70),
                start_time + datetime.timedelta(seconds=80)),
        ]:
            span = self.sdk.span()
            span._start_time = from_
            span._end_time = to_
            spans.append(span)

        from_ = start_time + datetime.timedelta(seconds=10)
        to_ = start_time + datetime.timedelta(seconds=60)

        result = find_spans_in_datetime_range(
            spans,
            from_=from_,
            to_=to_,
        )
        self.assertEqual(len(result), 3)
        self.assertEqual(spans[1:4], result)

    def test_find_spans_in_float_range_no_range_specified(self):
        l = 10
        end_time = datetime.datetime.utcnow()

        spans = []

        for index in range(l):
            span = self.sdk.span()
            span._start_time = end_time - datetime.timedelta(seconds=index)
            span._end_time = end_time
            spans.append(span)

        result = find_spans_in_float_range(spans)
        self.assertEqual(spans, result)

    def test_find_spans_in_float_range_no_endtime_specified(self):
        l = 10
        start_time = datetime.datetime.utcnow()
        end_time = start_time + datetime.timedelta(seconds=60)
        spans = []
        start_times = []

        for index in range(l):
            span = self.sdk.span()
            start_time = start_time + datetime.timedelta(seconds=index)
            start_times.append(start_time)
            span._start_time = start_times[-1]
            span._end_time = end_time
            spans.append(span)

        i = random.randint(0, l - 1)
        result = find_spans_in_float_range(spans, from_=datetime_to_float(start_times[i]))
        self.assertEqual(len(result), l - i)
        self.assertEqual(spans[i:], result)

    def test_find_spans_in_float_range_no_starttime_specified(self):
        l = 10
        start_time = datetime.datetime.utcnow()
        spans = []
        end_times = []

        for index in range(l):
            span = self.sdk.span()
            end_time = start_time + datetime.timedelta(seconds=index)
            end_times.append(end_time)
            span._start_time = start_time
            span._end_time = end_time
            spans.append(span)

        i = random.randint(0, l - 1)
        result = find_spans_in_float_range(spans, to_=datetime_to_float(end_times[i]))
        self.assertEqual(len(result), i)
        self.assertEqual(spans[:i], result)

    def test_find_spans_in_float_range(self):
        l = 10
        start_time = datetime.datetime.utcfromtimestamp(0)
        spans = []

        for from_, to_ in [
            (start_time,
                start_time + datetime.timedelta(seconds=30)),
            (start_time + datetime.timedelta(seconds=10),
                start_time + datetime.timedelta(seconds=30)),
            (start_time + datetime.timedelta(seconds=10),
                start_time + datetime.timedelta(seconds=40)),
            (start_time + datetime.timedelta(seconds=20),
                start_time + datetime.timedelta(seconds=50)),
            (start_time + datetime.timedelta(seconds=30),
                start_time + datetime.timedelta(seconds=60)),
            (start_time + datetime.timedelta(seconds=50),
                start_time + datetime.timedelta(seconds=60)),
            (start_time + datetime.timedelta(seconds=70),
                start_time + datetime.timedelta(seconds=80)),
        ]:
            span = self.sdk.span()
            span._start_time = from_
            span._end_time = to_
            spans.append(span)

        from_ = datetime_to_float(start_time + datetime.timedelta(seconds=10))
        to_ = datetime_to_float(start_time + datetime.timedelta(seconds=60))

        result = find_spans_in_float_range(
            spans,
            from_=from_,
            to_=to_,
        )
        self.assertEqual(len(result), 3)
        self.assertEqual(spans[1:4], result)


if __name__ == '__main__':  # pragma: no-cover
    unittest.main()
