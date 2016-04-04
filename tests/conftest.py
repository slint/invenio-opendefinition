# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import json
import os
import shutil
import tempfile
from os.path import abspath, dirname, join

import httpretty
import jsonschema
import pkg_resources
import pytest
from flask import Flask
from flask_celeryext import FlaskCeleryExt
from flask_cli import FlaskCLI, ScriptInfo
from invenio_db import InvenioDB, db
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from invenio_opendefinition import InvenioOpenDefinition


@pytest.yield_fixture
def app(licenses_example):
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    app = Flask('testapp', instance_path=instance_path)
    app.config.update(
        JSONSCHEMAS_HOST='localhost',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite://'),
        TESTING=True,
        CELERY_ALWAYS_EAGER=True,
        CELERY_RESULT_BACKEND="cache",
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    )

    FlaskCeleryExt(app)
    FlaskCLI(app)
    InvenioDB(app)
    InvenioJSONSchemas(app)
    InvenioRecords(app)
    InvenioPIDStore(app)
    InvenioOpenDefinition(app)

    with app.app_context():
        if str(db.engine.url) != "sqlite://" and \
           not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.drop_all()
        db.create_all()

    def teardown():
        drop_database(str(db.engine.url))

    httpretty.register_uri(
        httpretty.GET,
        app.config['OPENDEFINITION_LICENSES_URL'],
        body=json.dumps(licenses_example),
        content_type='application/json'
    )

    httpretty.enable()
    yield app
    httpretty.disable()
    shutil.rmtree(instance_path)


@pytest.yield_fixture
def script_info(app):
    """CLI object."""
    with app.app_context():
        yield ScriptInfo(create_app=lambda info: app)


@pytest.fixture(scope="session")
def licenses_example():
    path = dirname(__file__)
    with open(join(
            path,
            'data',
            'all-licenses.json')) as file:
        return json.load(file)
