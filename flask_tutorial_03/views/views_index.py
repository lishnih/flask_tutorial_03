#!/usr/bin/env python
# coding=utf-8
# Stan 2016-04-24

from __future__ import (division, absolute_import,
                        print_function, unicode_literals)

from flask import request, redirect, url_for, jsonify, flash, escape
from werkzeug.wrappers import Response

from sqlalchemy import func, column, desc, or_

from ..app import app, db
from ..core.parse_multi_form import parse_multi_form
from ..core.render_response import render_ext
from ..forms.message import MessageForm
from ..models.message import Message


# ===== Constants =====

limit_default = 15


# ===== Interface =====

# Здесь же маскируются выводимые значения
def row_iter(names, row, seq=None):
    for i in names:
        yield i, escape(getattr(row, i))

    yield "_seq", seq


# ===== Routes =====

@app.route("/", methods=['GET', 'POST'])
def index():
    if not db.engine.dialect.has_table(db.engine, "messages"):
        db.create_all()

    columns = Message.__table__.columns.keys()
    columns = [i for i in columns if not i.startswith('_')]

    columns_exclude = ['deleted']
    required_columns = [i for i in columns if i not in columns_exclude]

    draw = request.values.get('draw')
    if draw:
        start = request.values.get('start', '')
        length = request.values.get('length', '')
        _ = request.values.get('_')

        requested_params = parse_multi_form(request.values) # columns, order, search

        start = int(start) if start.isdigit() else 0
        length = int(length) if length.isdigit() else limit_default

        s = db.session.query(Message).filter_by(deleted=False)
        total = s.count()

        column_params = requested_params.get('columns', {})
        column_names = dict([(i, column_params.get(i, {}).get('data')) for i in column_params.keys()])
        column_searchables = dict([(i, column_params.get(i, {}).get('searchable')) for i in column_params.keys()])
        column_searchables = [column_names.get(k) for k, v in column_searchables.items() if v == 'true']

        search_params = requested_params.get('search', {})
        search = search_params.get('value')
        regex = search_params.get('regex')

        criterion = or_(*[column(i).like("%{0}%".format(search)) for i in column_searchables]) \
            if search else None

        if criterion is None:
            filtered = total
        else:
            s = s.filter(criterion)
            filtered = s.count()

        order_params = requested_params.get('order', {})
        order = []
        for i in sorted(order_params.keys()):
            column_sort_dict = order_params.get(i)
            column_id = int(column_sort_dict.get('column', ''))
            sort_dir = column_sort_dict.get('dir', '')
            sort_column = column_names.get(column_id)
            if sort_column:
                c = desc(column(sort_column)) if sort_dir == 'desc' else column(sort_column)
                order.append(c)

        if order:
            s = s.order_by(*order)

        if start and start < filtered:
            s = s.offset(start)
        if length:
            s = s.limit(length)

        rows = s.all()
        rows = [dict(row_iter(required_columns, row, start+j)) for j, row in enumerate(rows, 1)]

        return render_ext(
            format = "json",
            draw = draw,    # Переменная получена из запроса, но не используется для вывода (потенциально безопасная)
            recordsTotal = total,
            recordsFiltered = filtered,
            data = rows,    # Данные полученные из запроса, необходимо маскировать (потенциально опасная) - маскировка в row_iter
        )

    required_columns.remove('id')

    columns_dictionary = dict(
        name = "Name",
        author = "Author",
        message = "Message",
        created = "Created",
        updated = "Updated",
    )
    names = [columns_dictionary.get(i) or i for i in required_columns] + ['']

    return render_ext("message/messages.html",
        title = "Messages",
        required_columns = required_columns,
        names = names,
        seq = True,
        column_info = {"url": ["id", "fa fa-info", "fa fa-info", url_for('message_info')]},
        columns_extra = [
            ["id", "fa fa-edit", "", "fa fa-edit", "", url_for('message_edit')],
        ],
    )


@app.route("/madd", methods=['GET', 'POST'])
def message_add():
    form = MessageForm(request.form)

    if request.method == 'POST':
        if form.validate():
            message = Message(
                author = form.author.data,
                message = form.message.data,
            )
            db.session.add(message)
            db.session.commit()

            return render_ext("base.html",
                default = redirect(url_for('index')),
                message = "The message successfully added!",
            )

        else:
            return render_ext("message/add_edit.html",
                default = redirect(url_for('index')),
                message = ("Please check your data entered!", "warning"),
                section = "Add a message",
                form = form,
                # (потенциально опасная) - маскировка (если отключено по умолчанию) в _formhelpers.html
                # в json переменная не попадает (и не сможет быть конвертирована функцией jsonify)
            )

    return render_ext("message/add_edit.html",
        title = "Messages :: Add",
        section = "Add a message",
        form = form,    # (потенциально опасная)
    )


@app.route("/medit", methods=['GET', 'POST'])
def message_edit():
    id = request.values.get('id')
    message = db.session.query(Message).filter_by(id=id, deleted=False).first()

    if not message:
        return render_ext("base.html",
            default = redirect(url_for('index')),
            message = ("The message not found or deleted!", "warning"),
        )

    form = MessageForm(request.form, message, "Update")

    if request.method == 'POST':
        if form.validate():
            message.author = form.author.data
            message.message = form.message.data
            db.session.commit()

            return render_ext("message/add_edit.html",
                default = redirect(url_for('index')),
                message = "The message successfully updated!",
                section = "Edit the message",
                form = form,    # (потенциально опасная)
            )

        else:
            return render_ext("message/add_edit.html",
                default = redirect(url_for('index')),
                message = ("Please check your data entered!", "warning"),
                section = "Edit the message",
                form = form,    # (потенциально опасная)
            )

    return render_ext("message/add_edit.html",
        title = "Messages :: Edit",
        section = "Edit the message",
        form = form,    # (потенциально опасная)
    )


@app.route("/mdelete", methods=['GET', 'POST'])
def message_delete():
    id = request.values.get('id')
    message = db.session.query(Message).filter_by(id=id, deleted=False).first()

    if not message:
        return render_ext("base.html",
            default = redirect(url_for('index')),
            message = ("The message not found or deleted!", "warning"),
        )

    message.deleted = True
    db.session.commit()

    return render_ext("base.html",
        default = redirect(url_for('index')),
        message = ("The message successfully deleted!", "dark"),
    )


@app.route("/minfo", methods=['GET', 'POST'])
def message_info():
    id = request.values.get('id')

    return ""
