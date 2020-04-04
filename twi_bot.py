#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import namedtuple
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from retry import retry
from time import sleep
import logging
import requests
import traceback

TELEGRAM_BOT_TOKEN = ''
TELEGRAM_CHAT_ID = ''
TWITTER_BOT_TOKEN = ''
TWITTER_USER_ID = '975275878673408001' # Suisei's twitter id

session = requests.Session()

session.headers.update({
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip',
    'User-Agent': 'observatory bot/1.0.0'
})

handler = TimedRotatingFileHandler(
    'log/twi_bot.log',
    when = 'midnight',
    backupCount = 7,
    encoding = 'utf-8',
    utc = True
)

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    handlers = [logging.StreamHandler(), handler]
)

@retry(tries=7, delay=1, backoff=2)
def notify(msg):
    uri = 'https://api.telegram.org/bot{}/sendMessage'.format(TELEGRAM_BOT_TOKEN)
    headers={
    }
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': msg,
    }

    return session.get(uri, params=payload, headers=headers).json()

@retry(tries=7, delay=1, backoff=2)
def fetch(since_id):
    uri = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
    headers = {
        'Authorization': 'Bearer {}'.format(TWITTER_TOKEN)
    }
    payload = {
        'user_id': TWITTER_USER_ID,
        'since_id': since_id,
        'exclude_replies': True,
        'include_rts': True,
    }

    return session.get(uri, params=payload, headers=headers).json()

def timeline():
    since_id = 1

    while True:
        for tweet in reversed(fetch(since_id)):
            since_id = max(since_id, tweet['id'])
            yield tweet

        sleep(60)

def main():
    notify('天文台Bot（Twitter限定）启动啦')

    for tweet in timeline():
        dt = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S %z %Y').replace(tzinfo=None)
        uri = 'https://twitter.com/{}/status/{}'.format(tweet['user']['screen_name'], tweet['id'])

        logging.info('New tweet create at: {}, delta: {}, id: {}'.format(dt, datetime.utcnow() - dt, uri))

        if datetime.utcnow() - dt < timedelta(minutes=10):
            notify(uri)

if __name__ == '__main__':
    try:
        main()
    except:
        logging.error(traceback.format_exc())
        notify('天文台Bot（Twitter限定）死掉啦')
