#!/usr/bin/env python
# -*- coding: latin-1 -*-

import datetime

__all__ = [
    'NoDurationError',
    'InvalidSliceError',
    'DuplicateSpanEntryError']


class NoDurationError(ValueError):
    def __init__(self, start_time, end_time):
        super(NoDurationError, self).__init__(
            'Span has no duration ({start_time} -> {end_time})'.format(
                start_time=start_time, end_time=end_time))
        self.start_time = start_time
        self.end_time = end_time


class InvalidSliceError(TypeError):
    def __init__(self, s):
        super(InvalidSliceError, self).__init__(
            'Invalid slice {slice}'.format(slice=s))
        self._slice = s

    def slice(self):
        return self._slice


class DuplicateSpanEntryError(RuntimeError):
    def __init__(self, span):
        super(DuplicateSpanEntryError, self).__init__(
            'Already entered this span\'s context: {span}'.format(span=span))
        self.span = span


def datetime_to_timestamp(dt):
    return dt.isoformat('T') + 'Z' if dt else None


def datetime_to_float(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    total_seconds = (dt - epoch).total_seconds()
    # total_seconds will be in decimals (millisecond precision)
    return total_seconds


def find_spans_in_datetime_range(spans, dt_from, dt_to):
    result = []

    for span in spans:
        span_from = False
        span_to = False

        if dt_from is not None:
            if span.start_time is not None:
                if span.start_time >= dt_from:
                    span_from = True
        else:
            if span.start_time is not None:
                span_from = True

        if dt_to is not None:
            if span.end_time is not None:
                if span.end_time < dt_to:
                    span_to = True
        else:
            if span.end_time is not None:
                span_to = True

        if span_from and span_to:
            result.append(span)

    return result


def find_spans_in_float_range(spans, f_form, f_to):
    result = []

    for span in spans:
        if span.start_time is not None:
            start_time_float = datetime_to_float(span.start_time)
            end_time_float = datetime_to_float(span.end_time)

            if start_time_float >= f_form:
                if end_time_float:
                    if f_to is None:
                        result.append(span)
                    else:
                        if end_time_float < f_to:
                            result.append(span)
                else:
                    result.append(span)
    return result


def find_spans_with_duration(spans, td):
    result = []

    for span in spans:
        try:
            if span.duration <= td:
                result.append(span)
        except NoDurationError:
            continue

    return result
