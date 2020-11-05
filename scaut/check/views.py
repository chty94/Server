from django.shortcuts import render
from django.http import HttpResponse
from pymongo import MongoClient

# Create your views here.

def get(request, number):
    client = MongoClient('localhost', 27017)
    db = client['tempUser']

    # 프론트에서 받아야할 변수
    summonersName = 'jax'
    summoners = list(db['{}_summoners'.format(summonersName)].find({}))

    k = int(number)
    if k == 1: # crollTier
        if summoners[0]['crolling'] : return HttpResponse(True)
        else: return HttpResponse(False)
    elif k == 2: # getMatchlist
        if summoners[0]['getMatchlist'] : return HttpResponse(True)
        else: return HttpResponse(False)
    elif k == 3: # getMatches
        if summoners[0]['getMatches'] : return HttpResponse(True)
        else: return HttpResponse(False)
    elif k == 4: # createDatas
        if summoners[0]['createDatas'] : return HttpResponse(True)
        else: return HttpResponse(False)
    else:
        return HttpResponse(False)