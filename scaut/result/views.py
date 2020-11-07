from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
import numpy as np
import pandas as pd
from pymongo import MongoClient
import joblib
import os

# Create your views here.
def result(request, summonerName):
    client = MongoClient('localhost', 27017, username='Riot', password='Riot')
    db = client['tempUser']
    
    # user = db['{}_summoners'.format(summonerName)]
    # Tier = list(user.find({}))[0]['Tier']
    # print(Tier)

    model_ = client['userINFO']
    model_df = pd.DataFrame(model_['16_500_datas'].find())
    # model_df = pd.DataFrame(model_['{}_500_datas'.format(Tier)].find())

    testDf = pd.DataFrame(db['{}_datas'.format(summonerName)].find())
    # load the model from disk
    filename = 'LinearRegression.sav'
    loaded_model = joblib.load(os.getcwd() + "/result/" + filename)

    x_cols = testDf.drop(['_id', 'accountId'], axis=1).columns.tolist()
    x_test = testDf[x_cols]
    y_predict = loaded_model.predict(x_test)

    promotion = True
    if y_predict >= 0.5: promotion = True
    else: promotion = False

    _average = model_df.groupby(['promotion'], as_index=False).mean()
    _standard = model_df.groupby(['promotion'], as_index=False).std()

    average = _average.groupby('promotion').get_group(promotion).to_dict()
    standard = _standard.groupby('promotion').get_group(promotion).to_dict()

    for key, value in average.items():
        average[key] = list(value.values())[0]

    for key, value in standard.items():
        standard[key] = list(value.values())[0]

    info = {
        'user_promotion': y_predict[0],
        'user_info': list(db['{}_datas'.format(summonerName)].find({}, {'_id':0}))[0],
        'public_average': average,
        'public_standard': standard, 
    }
    return JsonResponse(info)
