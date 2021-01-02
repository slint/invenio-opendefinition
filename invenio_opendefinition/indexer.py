# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record modification prior to indexing."""

from __future__ import absolute_import, print_function

from elasticsearch import VERSION as ES_VERSION
from invenio_pidstore.models import PersistentIdentifier


def indexer_receiver(sender, json=None, record=None, index=None,
                     **dummy_kwargs):
    """Connect to before_record_index signal to transform record for ES."""
    if index.startswith('licenses-'):

        input_terms = [json['id']]

        # Query for all the PIDs the record has
        ids = PersistentIdentifier.query.filter(
            PersistentIdentifier.pid_type == 'od_lic',
            PersistentIdentifier.object_uuid == str(record.id),
            PersistentIdentifier.object_type == 'rec',
        )
        for i in ids:
            input_terms.append(i.pid_value)

        title = json['title']
        input_terms.append(title)

        # Split the title into it words
        title_terms = set()
        for split_char in ' -':
            if split_char in title:
                for w in title.split(split_char):
                    title_terms.add(w)
        input_terms.extend(list(title_terms))

        if ES_VERSION[0] == 2:
            # Generate suggest field
            json['suggest'] = {
                'input': input_terms,
                'output': title,
                'payload': {
                    'id': json['id'],
                    'title': title
                },
            }
        elif ES_VERSION[0] > 2:
            json['suggest'] = {'input': input_terms}
