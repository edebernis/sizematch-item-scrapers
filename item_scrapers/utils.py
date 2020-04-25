#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def urljoin(*args):
    return '/'.join(arg.strip('/') for arg in args)
