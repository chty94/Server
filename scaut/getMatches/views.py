from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

import requests
from time import sleep
from datetime import datetime, timedelta
from pymongo import MongoClient

API_KEY = 'RGAPI-d9784396-2f0e-4de6-8f2a-3e0b399e19bc'
DELAY = 1.1

def index(request):
    # 프론트에서 받아야할 변수
    summonersName = 'jax'

    MATCH_URL = 'https://kr.api.riotgames.com/lol/match/v4/matches/{}?api_key={}'

    client = MongoClient('localhost', 27017)
    db = client['tempUser']

    summoners = list(db['{}_summoners'.format(summonersName)].find({}))
    newCollection = db['{}_matches'.format(summonersName)]

    gameIds = sorted(set(m['gameId'] for s in summoners for m in s['matches']))

    fails = []
    successCount = 0
    count = 0
    gameCount = len(gameIds)
    start = datetime.now()

    for gameId in gameIds:
        try:
            count += 1
            response = requests.get(MATCH_URL.format(gameId, API_KEY))
            sleep(1.1)
            entry = response.json()
            
            if response.status_code != 200 or entry == None:
                raise Exception(response.status_code, entry)

            newCollection.insert_one(entry)
        except Exception as e:
            fails.append(gameId)
            # print('\n', gameId, '\n', e)

        print(count, successCount, gameCount, datetime.now()-start)
        successCount += 1

    q = {'_id': summoners[0]['_id']}
    v = {
        'getMatches': True
        }
    db['{}_summoners'.format(summonersName)].update_one(q, {'$set': v})

    return HttpResponse('success3')