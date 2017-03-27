# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import json

import pytest
import mock
from gcdt_testtools.helpers import vts

from gcdt_slack_integration.slack import _slack_notification, notify


@mock.patch('gcdt_slack_integration.slack._slack_notification')
def test_slack_notification(mocked_slack_notifications):
    context = {'tool': 'kumo', 'command': 'deploy',
               '_awsclient': 'awsclient-test'}
    config = {
        'kumo': {
            'cloudformation': {
                'StackName': 'infra-dev-test-stack'
            }
        },
        'plugins': {
            'slack_integration': {
                'slack_webhook': 'https://slack.bla.bla'
            }
        }
    }
    notify((context, config))

    mocked_slack_notifications.assert_called_once_with(
        {'tool': 'kumo', 'command': 'deploy', '_awsclient': 'awsclient-test'},
        'https://slack.bla.bla', u'#systemmessages',
        'deploy complete for stack \'infra-dev-test-stack\''
    )


@mock.patch('gcdt_slack_integration.slack._slack_notification')
def test_slack_error(mocked_slack_notifications):
    context = {'tool': 'kumo', 'command': 'deploy',
               '_awsclient': 'awsclient-test',
               'error': 'the following error happened: bang!'
               }
    config = {
        'kumo': {
            'cloudformation': {
                'StackName': 'infra-dev-test-stack'
            }
        },
        'plugins': {
            'slack_integration': {
                'slack_webhook': 'https://slack.bla.bla'
            }
        }
    }
    notify((context, config))

    mocked_slack_notifications.assert_called_once_with(
        {
            'tool': 'kumo', 'command': 'deploy',
            '_awsclient': 'awsclient-test',
            'error': 'the following error happened: bang!'
        },
        'https://slack.bla.bla', '#systemmessages',
        'deploy failed for stack \'infra-dev-test-stack\''
    )


@mock.patch('gcdt_slack_integration.slack._slack_notification')
def test_slack_notification_tenkai(mocked_slack_notifications):
    context = {'tool': 'tenkai', 'command': 'deploy', 'awsclient': 'awsclient-test',
        '_slack_token': 'xoxo-test-token'}
    config = {
        'tenkai': {
            'codedeploy': {
                'deploymentGroupName': 'infra-dev-test-stack-deloyment-grp'
            }
        },
        'plugins': {
            'slack_integration': {
                'slack_webhook': 'https://slack.bla.bla'
            }
        }
    }
    notify((context, config))

    mocked_slack_notifications.assert_called_once_with(
        {'tool': 'tenkai', 'awsclient': 'awsclient-test',
         'command': 'deploy', '_slack_token': 'xoxo-test-token'},
        'https://slack.bla.bla', '#systemmessages',
        'deploy complete for deployment group \'infra-dev-test-stack-deloyment-grp\''
    )


@mock.patch('gcdt_slack_integration.slack._slack_notification')
def test_slack_notification_ramuda(mocked_slack_notifications):
    context = {'tool': 'ramuda', 'command': 'deploy', 'awsclient': 'awsclient-test',
               '_slack_token': 'xoxo-test-token'}
    config = {
        'ramuda': {
            'lambda': {
                'name': 'infra-dev-captaincrunch'
            }
        },
        'plugins': {
            'slack_integration': {
                'slack_webhook': 'https://slack.bla.bla'
            }
        }
    }
    notify((context, config))

    mocked_slack_notifications.assert_called_once_with(
        {'tool': 'ramuda', 'awsclient': 'awsclient-test',
         'command': 'deploy', '_slack_token': 'xoxo-test-token'},
        'https://slack.bla.bla', '#systemmessages',
        'deploy complete for lambda function \'infra-dev-captaincrunch\''
    )


def test_slack_notifications(vts):
    context = {'tool': 'kumo'}
    # careful: we need to replace the webhook with a non-sensitive string
    # and in the vts_cassettes json file, too
    webhook = 'https://hooks.slack.com/services/'
    channel = '#ops-test'
    message = 'my_message'

    _slack_notification(context, webhook, channel, message)

    expected_payload = {
        'channel': channel,
        'username': 'gcdt %s' % context['tool'],
        'icon_emoji': ':cloudformation:',
        'attachments': [
            {
                'fallback': message,
                'pretext': message,
                'color': 'danger' if 'error' in context else 'good',
                'fields': [
                    {
                        'title': 'Error' if 'error' in context else 'Success',
                        'value': context['error'] if 'error' in context else ''
                    }
                ]
            }
        ]
    }

    assert len(vts.responses.calls) == 1
    assert vts.responses.calls[0].request.url == webhook
    assert json.loads(vts.responses.calls[0].request.body) == expected_payload
    assert vts.responses.calls[0].response.status_code == 200
