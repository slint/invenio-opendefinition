# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
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

"""Invenio module integrating Invenio repositories and OpenDefinition."""

from __future__ import absolute_import, print_function

import click

from .tasks import harvest_licenses


@click.group()
def opendefinition():
    """Invenio-OpenDefinition commands."""
    pass


@opendefinition.command('loadlicenses')
@click.option('--source', '-s', default='opendefinition')
@click.option('--path', '-p', type=click.Path(exists=True, dir_okay=False))
@click.option('--eager', '-e', is_flag=True)
def loadlicenses(source, path=None, eager=False):
    """Load licenses to local database."""
    click.secho('Loading licenses from {}'.format(source), fg='blue')
    task = harvest_licenses.s(source, path=path, eager=eager)
    if eager:
        task.apply(throw=True)
    else:
        task.apply_async()
        click.echo('Loading licenses in a background job.')
