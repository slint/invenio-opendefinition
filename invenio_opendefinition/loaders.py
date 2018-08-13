# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
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

"""License loaders."""

from __future__ import absolute_import, print_function

import json

import requests
from flask import current_app
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records.api import Record

from .minters import license_minter
from .resolvers import license_resolver
from .validators import license_validator


def upsert_license_record(license):
    """Insert or update a license record."""
    license_validator.validate(license)
    license['$schema'] = 'http://{0}{1}/{2}'.format(
        current_app.config['JSONSCHEMAS_HOST'],
        current_app.config['JSONSCHEMAS_ENDPOINT'],
        current_app.config['OPENDEFINITION_SCHEMAS_DEFAULT_LICENSE']
    )

    try:
        pid, record = license_resolver.resolve(license['id'])
        record.update(license)
        record.commit()
    except PIDDoesNotExistError:
        record = Record.create(license)
        license_minter(record.id, license)


def harvest_opendefinition(filepath=None):
    """Harvest licenses from https://opendefinition.org."""
    if filepath:
        with open(filepath) as fp:
            return json.load(fp)
    else:
        response = requests.get(
            current_app.config['OPENDEFINITION_LICENSES_URL'])
        return response.json()


def harvest_spdx(filepath=None):
    """Harvest licenses from https://spdx.org."""
    if filepath:
        with open(filepath) as fp:
            spdx_payload = json.load(fp)
    else:
        response = requests.get(
            current_app.config['OPENDEFINITION_SPDX_LICENSES_URL'])
        spdx_payload = response.json()

    # Preprocess the SPDX licenses to conform to the OpenDefinition schema
    licenses = {}
    for l in spdx_payload['licenses']:
        licenses[l['licenseId']] = {
            'id': l['licenseId'],
            'url': l['seeAlso'][-1],  # Last link is the most recent/valid
            'title': l['name'],
            'family': '',
            'maintainer': '',
            'status': 'retired' if l['isDeprecatedLicenseId'] else 'active',
            'osd_conformance': ('approved' if l['isOsiApproved']
                                else 'not reviewed'),
            'od_conformance': 'not reviewed',
            'domain_content': False,
            'domain_data': False,
            'domain_software': False,
        }
    return licenses
