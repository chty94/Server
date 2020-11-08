from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
import requests, re, time, json, sys, random
from pymongo import MongoClient
from bs4 import BeautifulSoup
from selenium import webdriver
from pyvirtualdisplay import Display
from datetime import datetime, timedelta
from time import sleep
import os
import sys
import numpy as np
import pandas as pd

# global
API_KEY = 'RGAPI-d9784396-2f0e-4de6-8f2a-3e0b399e19bc'
DELAY = 1.1
_TIERS = (
'IRON','BRONZE', 'SILVER',
'GOLD', 'PLATINUM', 'DIAMOND',
'MASTER', 'GRANDMASTER', 'CHALLENGER'
)
_RANKS = ('IV', 'III', 'II', 'I')
FEATURES = ('kills', 'deaths', 'assists', 'largestKillingSpree', 'largestMultiKill', 'killingSprees',
    'totalDamageDealt', 'totalDamageDealtToChampions', 'totalDamageTaken', 'goldEarned', 'goldSpent',
    'totalMinionsKilled', 'totalTimeCrowdControlDealt', 'champLevel'
    )
client = MongoClient('localhost', 27017, username='Riot', password='Riot')
db = client['tempUser']


# CrollTier
crollingpossible = 0
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
def crollTier(summonerName):

    result = {}

    newCollection = db['{}_summoners'.format(summonerName)]
    display = Display(visible=0, size=(1024, 768))
    display.start()
    path = '/home/ubuntu/chromedriver'
    try:
        URL = 'https://www.leagueofgraphs.com/ko/summoner/kr/{summonerName}'
        driver = webdriver.Chrome(path)
        driver.get(URL.format(summonerName=summonerName.replace(' ', '+')))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        script = soup.select_one('#rankingHistory-1 > script:nth-child(3)')
        match = re.compile("data: (.*)").search(str(script))
        datas = filterTimeStamps(json.loads(match.group(1)[:-1]))
    except:
        global crollingpossible
        newCollection.drop()
        crollingpossible = 1
        driver.close()
        return

    v = {}
    v['Tier'] = datas[-1][1]
    for k in datas[-2::-1]:
        if k[1] != v['Tier']:
            v['Start'] = [k[0], int(k[0].timestamp()*1000)]
            break
    v['crolling'] = True

    summoner = list(db['{}_summoners'.format(summonerName)].find({}))
    q = {'_id': summoner[0]['_id']}
    db['{}_summoners'.format(summonerName)].update_one(q, {'$set': v})
    driver.close()

# GetMatchlist
def getMatchlist(summonerName):
    ACCOUNT_ID_URL = 'https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/{}?api_key={}'
    MATCHLIST_URL = 'https://kr.api.riotgames.com/lol/match/v4/matchlists/by-account/{}?queue=420&beginTime={}&api_key={}'

    summoner = list(db['{}_summoners'.format(summonerName)].find({}))
    while True:
        try:
            acc_res = requests.get(ACCOUNT_ID_URL.format(summonerName, API_KEY))
            sleep(DELAY)
            acc_entry = acc_res.json()

            if acc_res.status_code != 200 or acc_entry == None:
                raise Exception('AccountId', acc_res.status_code, acc_entry)

            begin = summoner[0]['Start'][1]
            break
        
        except:
            print('error in ACCOUNT_ID_URL')
            continue

    matches = []
    while True:
        try:
            ml_res = requests.get(MATCHLIST_URL.format(acc_entry['accountId'], begin, API_KEY))
            sleep(DELAY)
            ml_entry = ml_res.json()
            
            if ml_res.status_code != 200 or ml_entry == None:
                raise Exception('Matchlist', ml_res.status_code, ml_entry)

            matches += ml_entry['matches']
            break
        
        except:
            print('error in MATCHLIST_URL')
            continue

    q = {'_id': summoner[0]['_id']}
    v = {
        'accountId': acc_entry['accountId'],
        'matches': matches,
        'getMatchlist': True
        }
    db['{}_summoners'.format(summonerName)].update_one(q, {'$set': v})

# GetMatches
def getMatches(summonerName):
    MATCH_URL = 'https://kr.api.riotgames.com/lol/match/v4/matches/{}?api_key={}'

    summoners = list(db['{}_summoners'.format(summonerName)].find({}))
    newCollection = db['{}_matches'.format(summonerName)]

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
            sleep(0.2)
            entry = response.json()
            
            if response.status_code != 200 or entry == None:
                raise Exception(response.status_code, entry)

            newCollection.insert_one(entry)
        except Exception as e:
            fails.append(gameId)
            continue
            # print('\n', gameId, '\n', e)
        successCount += 1
        print(count, successCount, gameCount, datetime.now()-start)

        q = {'_id': summoners[0]['_id']}
        v = {
            'getMatches': [successCount, gameCount]
            }
        db['{}_summoners'.format(summonerName)].update_one(q, {'$set': v})
    return fails
def getMatches_again(summonerName, fail, timer):
    MATCH_URL = 'https://kr.api.riotgames.com/lol/match/v4/matches/{}?api_key={}'
    newCollection = db['{}_matches'.format(summonerName)]
    summoners = list(db['{}_summoners'.format(summonerName)].find({}))

    fails = []
    successCount = summoners[0]['getMatches'][0]
    count = summoners[0]['getMatches'][0]
    gameCount = summoners[0]['getMatches'][1]
    start = datetime.now()

    for gameId in fail:
        try:
            count += 1
            response = requests.get(MATCH_URL.format(gameId, API_KEY))
            sleep(timer)
            entry = response.json()
            
            if response.status_code != 200 or entry == None:
                raise Exception(response.status_code, entry)

            newCollection.insert_one(entry)
        except Exception as e:
            fails.append(gameId)
            continue
            # print('\n', gameId, '\n', e)
        successCount += 1
        print(count, successCount, gameCount, datetime.now()-start)

        q = {'_id': summoners[0]['_id']}
        v = {
            'getMatches': [successCount, gameCount]
            }
        db['{}_summoners'.format(summonerName)].update_one(q, {'$set': v})
    return fails


# GetMatches
def getRatio(a, b):
    if a + b == 0:
        return 0
    else:
        return a / (a + b)
def createDatas(summonerName):   
    summoners = list(db['{}_summoners'.format(summonerName)].find({}))
    newCollection = db['{}_datas'.format(summonerName)]
    stats = []
    for s in db['{}_summoners'.format(summonerName)].find({}):
    # for s in db['sample_{}_{}_summoners'.format(LEVEL, SAMPLE_SIZE)].find({}):
        gameIds = [match['gameId'] for match in s['matches']]
        matchResults = []
        for match in db['{}_matches'.format(summonerName)].find({'gameId': {'$in': gameIds}}):
            matchResult = {}
            participantId = 0
            for participantIdentity in match['participantIdentities']:
                if participantIdentity['player']['accountId'] == s['accountId']:
                    participantId = participantIdentity['participantId']
                    break

            me = match['participants'][participantId-1]
            matchResult['win'] = me['stats']['win']
            matchResult['you'] = False
            you = None
            for p in match['participants']:
                if all(
                    [me['teamId'] != p['teamId'],
                    me['timeline']['role'] == p['timeline']['role'],
                    me['timeline']['lane'] == p['timeline']['lane']]
                    ):
                    matchResult['you'] = True
                    you = p
                    break

            for feature in FEATURES:
                if you: matchResult[feature] = getRatio(me['stats'][feature], you['stats'][feature])
                else: matchResult[feature] = 0
            
            matchResults.append(matchResult)

        matchResults = pd.DataFrame(matchResults)

        stat = pd.Series(index=['accountId', 'gameCount', 'win', 'loss', 'missing'] + list(FEATURES), dtype='object')
        stat['accountId'] = s['accountId']
        stat['gameCount'] = matchResults.shape[0]
        winCount = matchResults[matchResults['win'] == True].shape[0]
        lossCount = matchResults.shape[0] - winCount
        stat['win'] = getRatio(winCount, lossCount)
        stat['loss'] = getRatio(lossCount, winCount)
        stat['missing'] = matchResults[matchResults['you'] == False].shape[0]
        stat[list(FEATURES)] = matchResults.sum()[list(FEATURES)] / (stat['gameCount'] - stat['missing'])
        stats.append(stat)

    stats = pd.DataFrame(stats)
    newCollection.insert_many(stats.to_dict(orient='records'))

    q = {'_id': summoners[0]['_id']}
    v = {
        'createDatas': True
        }
    db['{}_summoners'.format(summonerName)].update_one(q, {'$set': v})

# redundancy check and sequence check
def check(summonerName):
    k = db['{}_datas'.format(summonerName)].find({}).count()
    if k == 0:
        db['{}_datas'.format(summonerName)].drop()
    else:
        db['{}_summoners'.format(summonerName)].drop()
        db['{}_matches'.format(summonerName)].drop()
        db['{}_datas'.format(summonerName)].drop()

    check = list(db['QUEUE'].find({'summonerName': summonerName}))
    if check:
        return HttpResponse('re_search')

    newCollection = db['{}_summoners'.format(summonerName)]
    count = db['QUEUE'].find({}).count()
    preprocessing1 = {
        'summonerName': summonerName,
        'crolling': False,
        'getMatchlist': False,
        'getMatches': [],
        'createDatas': False,
    }
    newCollection.insert_one(preprocessing1)

    preprocessing2 = {
        'summonerName': summonerName,
        'wait': count
    }
    db['QUEUE'].insert_one(preprocessing2)

    _id = list(db['QUEUE'].find({'wait':count}))[0]['_id']
    while True:
        if count == 0:
            break
        sleep(3)
        w = list(db['QUEUE'].find({'wait':count-1}))
        if w:
            continue
        else:
            v = {'wait':count-1}
            summoner = list(db['QUEUE'].find({}))
            q = {'_id': _id}
            db['QUEUE'].update_one(q, {'$set': v})
            count = count - 1
 
def search(request, summonerName):
    # redundancy check and sequence check

    check(summonerName)

    # Crolling the User's Tier
    global crollingpossible
    crollTier(summonerName)
    if crollingpossible == 1:
        return HttpResponse('fail')

    # Getting Matchlist of User
    getMatchlist(summonerName)
    
    # Getting Matches from Matchlist above
    fail = getMatches(summonerName)
    
    # Creating a datas with the matches
    if len(fail) == 0:
        createDatas(summonerName)
    else:
        timer = 1
        len_before = len(fail)
        while fail:
            print(fail, timer)
            fail = getMatches_again(summonerName, fail, timer)
            if len_before == len(fail):
                timer += 0.1
                if int(timer*10) == 27:
                    timer = 2.6
            else:
                timer = 0.1

        createDatas(summonerName)
    
    # Making a response form
    summoner = list(db['{}_summoners'.format(summonerName)].find({}))
    result = {
        'summonerName': summonerName,
        'crolling': summoner[0]['crolling'],
        'getMatchlist': summoner[0]['getMatchlist'],
        'getMatches': summoner[0]['getMatches'],
        'createDatas': summoner[0]['createDatas'],
        'wait': 0
    }

    db['QUEUE'].remove({'wait': 0})

    return JsonResponse(result)
