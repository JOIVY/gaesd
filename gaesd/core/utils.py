#!/usr/bin/env python
# -*- coding: latin-1 -*-


def datetime_to_timestamp(dt):
    return dt.isoformat('T') + 'Z'
