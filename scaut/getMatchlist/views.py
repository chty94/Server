from django.shortcuts import render
from django.http import HttpResponse
import requests
from time import sleep
from datetime import datetime
from pymongo import MongoClient

API_KEY = 'RGAPI-d9784396-2f0e-4de6-8f2a-3e0b399e19bc'
DELAY = 1.1

# Create your views here.
def index(request):
    # 프론트에서 받아야할 변수 목록
    summonersName = 'jax'

    ACCOUNT_ID_URL = 'https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/{}?api_key={}'
    MATCHLIST_URL = 'https://kr.api.riotgames.com/lol/match/v4/matchlists/by-account/{}?queue=420&beginTime={}&api_key={}'

    client = MongoClient('localhost', 27017)
    db = client['tempUser']


    summoner = list(db['{}_summoners'.format(summonersName)].find({}))
    acc_res = requests.get(ACCOUNT_ID_URL.format(summonersName, API_KEY))
    print(acc_res)
    sleep(DELAY)
    acc_entry = acc_res.json()

    if acc_res.status_code != 200 or acc_entry == None:
        raise Exception('AccountId', acc_res.status_code, acc_entry)

    begin = summoner[0]['Start'][1]

    matches = []
    ml_res = requests.get(MATCHLIST_URL.format(acc_entry['accountId'], begin, API_KEY))
    sleep(DELAY)
    ml_entry = ml_res.json()
    
    if ml_res.status_code != 200 or ml_entry == None:
        raise Exception('Matchlist', ml_res.status_code, ml_entry)

    matches += ml_entry['matches']

    q = {'_id': summoner[0]['_id']}
    v = {
        'accountId': acc_entry['accountId'],
        'matches': matches,
        'getMatchlist': True
        }
    db['{}_summoners'.format(summonersName)].update_one(q, {'$set': v})
    return HttpResponse('success2')