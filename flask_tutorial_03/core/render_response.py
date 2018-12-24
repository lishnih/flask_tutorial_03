#!/usr/bin/env python
# coding=utf-8
# Stan 2017-07-11

from __future__ import (division, absolute_import,
                        print_function, unicode_literals)

from flask import request, render_template, jsonify, flash
from werkzeug.wrappers import Response


def render_ext(template_name_or_list=None, default=None, message="",
        format=None, form=None, **context):
    format = format or request.values.get('format')

    result = "success"
    if isinstance(message, tuple):
        message, result = message

    if format == 'json':
        return jsonify(dict(
            result = result,
            message = message,
            **context
        ))

    if message:
        flash(message, result or "success")

    if isinstance(default, Response) and not format:
        return default

    return "No template defined!" if not template_name_or_list else \
        render_template(template_name_or_list,
            modal = format == 'modal',
            form = form,
            **context
        )
