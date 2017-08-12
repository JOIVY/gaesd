#!/usr/bin/env python
# -*- coding: latin-1 -*-

import datetime

__all__ = [
    'NoDurationError',
    'InvalidSliceError',
    'DuplicateSpanEntryError',
    'find_spans_in_datetime_range',
    'find_spans_in_float_range',
    'find_spans_with_duration_less_than',
]


class NoDurationError(ValueError):
    """
    There was an error calculating the span's duration.
    Most likely, the span either hasn't started or finished.
    """

    def __init__(self, span):
        super(NoDurationError, self).__init__(
            'Span has no duration ({start_time} -> {end_time})'.format(
                start_time=span.start_time, end_time=span.end_time))
        self.span = span


class InvalidSliceError(TypeError):
    """
    The slice's start, stop, step combination is not supported.
    """

    def __init__(self, s):
        super(InvalidSliceError, self).__init__(
            'Invalid slice {slice}'.format(slice=s))
        self.slice = s


class DuplicateSpanEntryError(RuntimeError):
    """
    The span's context is already entered.
    """

    def __init__(self, span):
        super(DuplicateSpanEntryError, self).__init__(
            'Already entered this span\'s context: {span}'.format(span=span))
        self.span = span


def datetime_to_timestamp(dt=None):
    """
    Create a StackDriver compatible timestamp.

    :param datetime.datetime dt: datetime object to convert.
    :rtype: six.string_types
    """
    return dt.isoformat('T') + 'Z' if dt else None


def datetime_to_float(dt):
    """
    Convert a datetime to floating point value since the epoch.

    :param datetime.datetime dt:
    :rtype: float
    """
    epoch = datetime.datetime.utcfromtimestamp(0)
    total_seconds = (dt - epoch).total_seconds()
    # total_seconds will be in decimals (millisecond precision)
    return total_seconds


def _find_spans_in_datetime_range(spans, from_, to_, func):
    result = []

    for span in spans:
        span_from = False
        span_to = False

        if from_ is not None:
            if span.start_time is not None:
                start_time = func(span.start_time)
                # Deliberately `>=` not `>`:
                if start_time >= from_:
                    span_from = True
        else:
            if span.start_time is not None:
                span_from = True

        if to_ is not None:
            if span.end_time is not None:
                end_time = func(span.end_time)
                # Deliberately `<` not `<=`:
                if end_time < to_:
                    span_to = True
        else:
            if span.end_time is not None:
                span_to = True

        if span_from and span_to:
            result.append(span)

    return result


def find_spans_in_datetime_range(spans, from_=None, to_=None):
    """
    Find all the spans such that:
    (span.start_time <= from) and (to_ < span.end_time)

    :param spans: The spans to parse.
    :type spans: List(Span)
    :param from_: The optional lower bound.
    :type from_: datetime.datetime
    :param to_: The optional upper bound .
    :type to_: datetime.datetime
    :return: The spans that satisfy the bounds.
    :rtype: List(Span)
    """
    return _find_spans_in_datetime_range(
        spans=spans,
        from_=from_,
        to_=to_,
        func=lambda x: x,
    )


def find_spans_in_float_range(spans, from_=None, to_=None):
    """
    Find all the spans such that:
    (span.start_time <= from) and (to_ < span.end_time)

    :param spans: The spans to parse.
    :type spans: List(Span)
    :param from_: The optional lower bound.
    :type from_: float
    :param to_: The optional upper bound .
    :type to_: float
    :return: The spans that satisfy the bounds.
    :rtype: List(Span)
    """
    return _find_spans_in_datetime_range(
        spans=spans,
        from_=from_,
        to_=to_,
        func=datetime_to_float,
    )


def find_spans_with_duration_less_than(spans, duration):
    """
    Find all spans with durations less than the given one.
    Spans with no duration will not be returned.

    :param list(Span) spans:
    :param duration: The duration to use.
    :type duration: Union[float, int]
    :return: The spans that satisfy the duration.
    :rtype: List(Span)
    """
    if isinstance(duration, (float, int)):
        duration = datetime.timedelta(seconds=duration)

    results = []

    for span in spans:
        try:
            if span.duration <= duration:
                results.append(span)
        except NoDurationError:
            continue

    return results
