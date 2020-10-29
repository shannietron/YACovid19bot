from telegram.ext import Updater
import matplotlib.pyplot as plt
import numpy as np
import os

with open (os.path.dirname(os.path.realpath(__file__))+'/token.txt') as file:
    TOKEN = file.readline().strip()

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

import requests

url = 'https://api.covidtracking.com/v1/us/current.json'

def today(update, context):
    r = requests.get(url)
    rjson = r.json()
    deltaPos = rjson[0]['positiveIncrease']
    deltaHosp = rjson[0]['hospitalizedIncrease']
    deltaTests = rjson[0]['totalTestResultsIncrease']
    deltaRatio = round(((deltaPos/deltaTests)*100),2)
    message = 'New Positives today: ' + "{:,}".format(deltaPos) + '\n' \
            'New Hospitalizations: ' + "{:,}".format(deltaHosp) + '\n' \
            'Ratio: ' + str(deltaRatio) + '%'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

from telegram.ext import CommandHandler

today_handler = CommandHandler('today', today)
dispatcher.add_handler(today_handler)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text = "hoi, I update you")

start_handler = CommandHandler('start',start)
dispatcher.add_handler(start_handler)

stateUrlPre = 'https://api.covidtracking.com/v1/states/'
stateUrlSuf = '/current.json'
def state(update, context):
    selectedState = " ".join(context.args) 
    stateUrl = stateUrlPre+selectedState+stateUrlSuf
    r = requests.get(stateUrl)
    rjson = r.json()

    deltaPos = rjson['positiveIncrease']
    deltaHosp = rjson['hospitalizedIncrease']
    deltaTests = rjson['totalTestResultsIncrease']
    deltaRatio = round(((deltaPos/deltaTests)*100),2)
    message ='State: ' + selectedState + '\n' \
            'New Positives today: ' + "{:,}".format(deltaPos) + '\n' \
            'New Hospitalizations: ' + "{:,}".format(deltaHosp) + '\n' \
            'Ratio: ' + str(deltaRatio) + '%'

    update.message.reply_text(message)


state_handler = CommandHandler('state',state)
dispatcher.add_handler(state_handler)

def generateTrend(context):
    historicUrl = 'https://api.covidtracking.com/v1/us/daily.json'
    r = requests.get(historicUrl)
    rjson = r.json()
    deltaPos = [rjson[i]['positiveIncrease'] for i in range (len(rjson))]
    deltaTests = [rjson[i]['totalTestResultsIncrease'] for i in range (len(rjson))]
    deltaHosp = [rjson[i]['hospitalizedCurrently'] for i in range (len(rjson))]
    deltaDeaths = [rjson[i]['deathIncrease'] for i in range (len(rjson))]
    def safediv(x,y):
        try:
            return x/y
        except ZeroDivisionError:
            return 0
    deltaRatio = [safediv(x,y) for x, y in zip(deltaPos,deltaTests)]
    deltaRatio.reverse()
    deltaHosp.reverse()
    deltaDeaths.reverse()
    deltaPos.reverse()
    fig,axs=plt.subplots(2,2)
    if(context.args):
        duration = int( " ".join(context.args)) 
    else:
        duration = 60
    dataLen = len(deltaRatio)
    startDur = dataLen-duration
    axs[0,0].plot(deltaRatio[startDur:dataLen],'xkcd:cerulean')
    axs[0,0].set_title('daily positive ratio')
    axs[0,1].plot(deltaHosp[startDur:dataLen],'xkcd:lilac')
    axs[0,1].set_title('hospitalization')
    axs[1,0].plot(deltaDeaths[startDur:dataLen],'xkcd:black')
    axs[1,0].set_title('death increase')
    axs[1,1].plot(deltaPos[startDur:dataLen],'xkcd:coral')
    axs[1,1].set_title('daily positive ratio')
    plt.savefig('tmp.jpg')
    plt.clf()

def trend(update, context):
    generateTrend(context)
    update.message.reply_photo(photo=open('tmp.jpg','rb'))

trend_handler=CommandHandler('trend',trend)
dispatcher.add_handler(trend_handler)

import re
def vote(update, context):
    r = requests.get('https://electproject.github.io/Early-Vote-2020G/index.html')
    votes = re.findall(r'Total Early Votes: <strong>([0-9,]{10,15})',str(r.content))
    update.message.reply_text("Total Early Votes: "+str(votes[0] + '\n'\
            "Current Turnout: " + str(round(((int(votes[0].replace(',',''))/239247182)*100),3)))+'%')
vote_handler = CommandHandler('vote',vote)
dispatcher.add_handler(vote_handler)



updater.start_polling()
