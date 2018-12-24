#!/usr/bin/env python
# coding=utf-8
# Stan 2018-08-02

from __future__ import (division, absolute_import,
                        print_function, unicode_literals)


# ===== Import Application and App DB =====
from .app import app, db


# ===== Import extensions =====
from .extensions import *


# ===== Import views =====
from .core.load_modules import load_modules, require_ext

load_modules('views_user')
load_modules('views')
