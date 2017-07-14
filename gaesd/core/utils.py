#!/usr/bin/env python
# -*- coding: latin-1 -*-
import datetime

__all__ = ['datetime_to_timestamp']


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


def datetime_to_timestamp(dt):
    return dt.isoformat('T') + 'Z' if dt else None


def datetime_to_float(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    total_seconds = (dt - epoch).total_seconds()
    # total_seconds will be in decimals (millisecond precision)
    return total_seconds


def find_spans_in_datetime_range(spans, dt_form, dt_to):
    result = []

    for span in spans:
        if span.start_time is not None:
            if span.start_time >= dt_form:
                result.append(span)
            elif span.end_time:
                if dt_to is None:
                    result.append(span)
                else:
                    if span.end_time < dt_to:
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
