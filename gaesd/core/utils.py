#!/usr/bin/env python
# -*- coding: latin-1 -*-

__all__ = ['datetime_to_timestamp']


def datetime_to_timestamp(dt):
    return dt.isoformat('T') + 'Z'
