from django.shortcuts import render
from django.http import JsonResponse
from pymongo import MongoClient

# Create your views here.

def check(request, summonerName):
    client = MongoClient('localhost', 27017)
    db = client['tempUser']

    # 프론트에서 받아야할 변수
    summoner = list(db['{}_summoners'.format(summonerName)].find({}))
    k = list(db['QUEUE'].find({'summonerName':summonerName}, {'_id':0, 'wait':1}))

    if k:
        result = {
            'crolling': summoner[0]['crolling'],
            'getMatchlist': summoner[0]['getMatchlist'],
            'getMatches': summoner[0]['getMatches'],
            'createDatas': summoner[0]['createDatas'],
            'wait': k[0]['wait']
        }
    else:
        result = {
            'crolling': summoner[0]['crolling'],
            'getMatchlist': summoner[0]['getMatchlist'],
            'getMatches': summoner[0]['getMatches'],
            'createDatas': summoner[0]['createDatas'],
            'wait': 0
        }
    
    return JsonResponse(result)
