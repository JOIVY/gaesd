#!/usr/bin/env python
# -*- coding: latin-1 -*-


def datetime_to_timestamp(dt):
    return ''.join([dt.isoformat(), 'Z'])
