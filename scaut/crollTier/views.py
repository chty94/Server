from django.shortcuts import render
from django.http import HttpResponse
import requests, re, time, json, sys, random
from pymongo import MongoClient
from bs4 import BeautifulSoup
from selenium import webdriver
from datetime import datetime, timedelta

import os
import sys

_TIERS = (
    'IRON','BRONZE', 'SILVER',
    'GOLD', 'PLATINUM', 'DIAMOND',
    'MASTER', 'GRANDMASTER', 'CHALLENGER'
    )
_RANKS = ('IV', 'III', 'II', 'I')

def integer_to_tier_rank(i):
    if i > 24:
        return _TIERS[6 + i - 25], _RANKS[3]
    else:
        return _TIERS[(i-1)//4], _RANKS[(i-1)%4]

def convertTimestamp(timestamp):
    return [datetime.fromtimestamp(timestamp[0]//1000), timestamp[1]]

def filterTimeStamps(timestamps):
    timestamps = [t for t in timestamps if t]
    if len(timestamps) == 0:
        return []

    result = [convertTimestamp(timestamps[0])]
    for timestamp in timestamps[1:]:
        if result[-1][1] != timestamp[1]:
            result.append(convertTimestamp(timestamp))

    return result

# Create your views here.
def index(request):

    result = {}
    # 프론트에서 받아야할 변수 목록
    summonerName = 'jax'
    summonerID = 'mNELOyrW3AbdLcza63JOOqL9XiapqZv6y6_soZ0l8vXWLIuH'

    client = MongoClient('localhost', 27017)
    db = client['tempUser']

    newCollection = db['{}_summoners'.format(summonerName)]

    URL = 'https://www.leagueofgraphs.com/ko/summoner/kr/{summonerName}'
    driver = webdriver.Chrome()
    driver.get(URL.format(summonerName=summonerName.replace(' ', '+')))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    script = soup.select_one('#rankingHistory-1 > script:nth-child(3)')
    match = re.compile("data: (.*)").search(str(script))
    datas = filterTimeStamps(json.loads(match.group(1)[:-1]))

    result['summonerName'] = summonerName
    result['summonerID'] = summonerID
    result['Tier'] = datas[-1][1]
    for k in datas[-2::-1]:
        if k[1] != result['Tier']:
            result['Start'] = [k[0], int(k[0].timestamp()*1000)]
            break
    result['crolling'] = True
    result['getMatchlist'] = False
    result['getMatches'] = False
    result['createDatas'] = False
    newCollection.insert_one(result)
    driver.close()
    return HttpResponse('success1')