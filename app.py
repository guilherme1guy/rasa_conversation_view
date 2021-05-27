from flask import Flask, request
from flask import render_template, redirect
from flask_paginate import Pagination, get_page_parameter

from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.errors import InvalidOperation
from datetime import datetime

import pytz
import os

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')
app.config['ENV_TITLE'] = os.getenv('ENV_TITLE')


def get_db():
    client = MongoClient(
        host=os.getenv('MONGO_URL'),
        username=os.getenv('MONGO_USER'),
        password=os.getenv('MONGO_PASSWORD')
    )

    return client[os.getenv('DB_NAME')]


def get_date_from_timestamp(timestamp):

    date = datetime.utcfromtimestamp(timestamp)
    date.replace(tzinfo=pytz.timezone('UTC'))
    date = date.astimezone(
        pytz.timezone(os.getenv('TIMEZONE', 'UTC'))
    )

    return date


def pretty_date(date):
    return date.strftime('%Y-%m-%d  ~  %H:%M:%S')


@app.context_processor
def utility_processor():

    def convert_timestamp(timestamp):
        return pretty_date(get_date_from_timestamp(timestamp))

    return dict(convert_timestamp=convert_timestamp)


@app.route('/')
def root():

    return redirect('/conversations')


@app.route('/conversations')
def conversation_list():

    per_page = 10
    page = request.args.get(get_page_parameter(), type=int, default=1)

    db = get_db()
    conversations = []

    search = False
    q = request.args.get('q')
    query = {}
    if q:
        search = True

        # {"events.parse_data.intent.name": {$regex : ".*<intent_name>*"}}
        # {"events.text": {$regex : ".*<search text>.*"}}
        # {$or: [<q1>, <q2> ...]}
        query = {'$or':
                 [
                     {'events.parse_data.intent.name': {'$regex': f'.*{q}*'}},
                     {'events.text': {'$regex': f'.*{q}.*'}},
                     # only match conversations with an event
                     {'events.0': {'$exists': True}}
                 ]
                 }

    conversations_from_db = db['conversations'].find(
        query).sort('latest_event_time', DESCENDING)
    current_page_conversations = conversations_from_db.skip(
        (page - 1) * per_page).limit(per_page)

    def count_messages(events):

        count = 0

        for event in events:
            if (event['event'] == 'user' or event['event'] == 'bot') and event['text'] != None:
                count += 1

        return count

    for conversation in current_page_conversations:

        date = get_date_from_timestamp(conversation['latest_event_time'])

        conv = {
            'date': pretty_date(date),
            'sender_id': conversation['sender_id'],
            'event_count': count_messages(conversation['events'])
        }
        conversations.append(conv)

    pagination = Pagination(
        page=page, total=conversations_from_db.count(),
        per_page=per_page,
        search=search, record_name='conversations',
        css_framework='bootstrap4')

    return render_template(
        'conversation_list.html',
        socket_url=os.getenv('SOCKET_URL', ''),
        conversations=conversations,
        pagination=pagination,
        js_src=os.getenv(
            'JS_SRC', 'https://cdn.jsdelivr.net/npm/rasa-webchat/lib/index.js'),
        init_payload=os.getenv('INIT_PAYLOAD', '')
    )


@app.route('/conversations/<string:conversation_id>')
def conversation_detail(conversation_id):

    db = get_db()
    all_conversations = db['conversations']

    conversation = all_conversations.find_one({'sender_id': conversation_id})

    previous_conversation_search = all_conversations\
        .find({'latest_event_time': {'$lt': conversation['latest_event_time']}})\
        .sort('latest_event_time', DESCENDING).limit(1)

    try:
        previous_conversation = previous_conversation_search[0]
    except (InvalidOperation, IndexError):
        previous_conversation = None

    next_conversation_search = all_conversations\
        .find({'latest_event_time': {'$gt': conversation['latest_event_time']}})\
        .sort('latest_event_time', ASCENDING).limit(1)

    try:
        next_conversation = next_conversation_search[0]
    except (InvalidOperation, IndexError):
        next_conversation = None

    display_events = []

    def get_common_data(event):

        evt = {
            'sender': event['event'],
            'text': event['text'],
            'date': pretty_date(get_date_from_timestamp(event['timestamp']))
        }

        return evt

    def get_user_event(event):

        evt = get_common_data(event)

        try:
            evt['intent'] = event['parse_data']['intent']['name']
            evt['confidence'] = event['parse_data']['intent']['confidence']
        except KeyError:
            evt['intent'] = 'null'
            evt['confidence'] = 1

        return evt

    def get_bot_event(event):

        evt = get_common_data(event)
        evt['metadata'] = event['metadata']

        return evt

    filters = {
        'bot': get_bot_event,
        'user': get_user_event
    }

    for event in conversation['events']:

        evt_type = event['event']

        if evt_type in filters:

            evt = filters[evt_type](event)

            if evt['text'] is not None:
                display_events.append(evt)

    return render_template(
        'conversation_detail.html',
        conversation=conversation,
        socket_url=os.getenv('SOCKET_URL', ''),
        previous_conversation=previous_conversation,
        next_conversation=next_conversation,
        display_events=display_events,
        js_src=os.getenv(
            'JS_SRC', 'https://cdn.jsdelivr.net/npm/rasa-webchat/lib/index.js'),
        init_payload=os.getenv('INIT_PAYLOAD', '')
    )
