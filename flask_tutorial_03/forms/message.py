#!/usr/bin/env python
# coding=utf-8
# Stan 2018-10-10

from __future__ import (division, absolute_import,
                        print_function, unicode_literals)

from flask_login import current_user

from wtforms import (Form, SubmitField, StringField, TextAreaField,
                     HiddenField, validators)

from ..models.message import Message


class MessageForm(Form):
    id = HiddenField()
    author = StringField('Author:', [
            validators.DataRequired(),
        ],
        render_kw={
            "placeholder": "Your name (required)",
        }
    )
    message = TextAreaField('Message:', [
            validators.DataRequired(),
            validators.Length(min=2),
        ],
        render_kw={
            "placeholder": "Your message (required)",
        }
    )
    format = StringField()
    submit = SubmitField('Submit')

    def __init__(self, form, message=None, label=None, **kargs):
        super(MessageForm, self).__init__(form, **kargs)

        if message and not form:
            self.id.data = message.id
            self.author.data = message.author
            self.message.data = message.message

        elif hasattr(current_user, 'name'):
            self.author.data = current_user.name

        if label:
            self.submit.label.text = label

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        return True
