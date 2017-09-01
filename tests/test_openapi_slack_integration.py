# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from gcdt.gcdt_openapi import get_openapi_defaults, get_openapi_scaffold_min, \
    get_openapi_scaffold_max, validate_tool_config

from gcdt_slack_integration import read_openapi


def test_default():
    spec = read_openapi()
    expected_defaults = {
        'defaults': {
            'validate': True,
            'slack_webhook': 'lookup:secret:slack.webhook:CONTINUE_IF_NOT_FOUND'
        }
    }

    plugin_defaults = get_openapi_defaults(spec, 'gcdt_slack_integration')
    assert plugin_defaults == expected_defaults
    validate_tool_config(spec, {'plugins': {'gcdt_slack_integration': plugin_defaults}})
