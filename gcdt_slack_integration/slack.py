# -*- coding: utf-8 -*-
"""gcdt-plugin to handle slack notifications."""
from __future__ import unicode_literals, print_function
import json

import requests
from requests import codes

from gcdt import gcdt_signals
from gcdt.gcdt_logging import getLogger


log = getLogger(__name__)

# we use "Incoming Webhooks" to integrate with slack
# docu: https://api.slack.com/incoming-webhooks


# map tools to AWS emojis (which we uploaded to slack)
EMOJIS = {
    'kumo': ':cloudformation:',
    'tenkai': ':codedeploy:',
    'ramuda': ':lambda:',
    'yugen': ':apigateway:'
}


def _slack_notification(context, webhook, channel, message):
    # helper to actually send a slack notification using Slacker
    # curl -X POST --data-urlencode 'payload={"channel": "@andreas.sieferlinger", "username": "gcdt master of the universe", "text": "This is posted to #ops-test  and comes from a bot named webhookbot trullu.", "icon_emoji": ":ghost:"}' https://hooks.slack.com/services/1234/AB1234/xyz1234
    payload = {
        'channel': channel,
        'username': 'gcdt %s' % context['tool'],
        'icon_emoji': EMOJIS[context['tool']],
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

    res = requests.post(
        webhook,
        data=json.dumps(payload)
    )
    if res.status_code != codes.ok:
        print('ERROR: %s' % res.text)
        return


def notify(params):
    """Check if we need to send a slack notification.
    Note: if we do not have a slack_webhook we do not send notifications.
    :param params: context, config (context - the _awsclient, etc..
                   config - The stack details, etc..)
    """
    context, config = params
    tool = context['tool']
    if 'plugins' not in config or 'gcdt_slack_integration' not in config['plugins']:
        return
    webhook = config['plugins']['gcdt_slack_integration'].get('slack_webhook', None)
    if not webhook.startswith('https'):
        return
    channel = config['plugins']['gcdt_slack_integration'].get('channel', '#systemmessages')
    message = None

    status = 'failed' if 'error' in context else 'complete'

    # tool specific messages (later this could be part of the plugin config)
    if 'error' in context and tool not in config.keys():
        # handle the missing config case - we can not provide any specifics
        message = '%s %s: %s' % (
            tool,
            context['command'],
            status
        )
    elif tool == 'kumo':
        if context['command'] in ['deploy', 'delete']:
            message = '%s %s for stack \'%s\'' % (
                context['command'],
                status,
                config[tool]['cloudformation'].get('StackName')
            )
    elif tool == 'tenkai':
        if context['command'] in ['deploy']:
            message = '%s %s for deployment group \'%s\'' % (
                context['command'],
                status,
                config[tool]['codedeploy'].get('deploymentGroupName')
            )
    elif tool == 'ramuda':
        if context['command'] in ['deploy', 'delete']:
            message = '%s %s for lambda function \'%s\'' % (
                context['command'],
                status,
                config[tool]['lambda'].get('name')
            )
        elif context['command'] in ['wire', 'unwire']:
            message = '%s %s for lambda function \'%s\' with alias \'ACTIVE\'' % (
                context['command'],
                status,
                config[tool]['lambda'].get('name')
            )
        elif context['command'] in ['rollback']:
            if '<version>' in context['_arguments'] and context['_arguments'][
                '<version>']:
                message = '%s %s for lambda function \'%s\' to version \'%s\'' % (
                    context['command'],
                    config[tool]['lambda'].get('name'),
                    context['_arguments']['<version>']
                )
            else:
                message = '%s %s for lambda function \'%s\' to previous version' % (
                    context['command'],
                    status,
                    config[tool]['lambda'].get('name')
                )
    elif tool == 'yugen':
        if context['command'] in ['deploy', 'delete']:
            message = '%s %s for api \'%s\'' % (
                context['command'],
                status,
                config[tool]['api'].get('name')
            )

    # only send if we prepared a message
    if message:
        _slack_notification(context, webhook, channel, message)


def register():
    """Please be very specific about when your plugin needs to run and why.
    notify is able to handle both 'command_finalized' and 'error' signals.
    """
    gcdt_signals.command_finalized.connect(notify)
    gcdt_signals.error.connect(notify)


def deregister():
    gcdt_signals.command_finalized.disconnect(notify)
    gcdt_signals.error.disconnect(notify)
