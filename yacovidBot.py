from telegram.ext import Updater
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

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
    date = datetime.strptime(str(rjson[0]['date']),"%Y%m%d").date()
    strdate = date.strftime("%d %b %Y")
    
    message = 'Date : ' + strdate + "\n" \
            'New Positives today: ' + "{:,}".format(deltaPos) + '\n' \
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
    x=np.arange(0,(dataLen-startDur))
    axs[0,0].plot(deltaRatio[startDur:dataLen],'xkcd:cerulean')
    axs[0,0].set_title('daily positive ratio')
    axs[0,1].plot(deltaHosp[startDur:dataLen],'xkcd:lilac')
    axs[0,1].set_title('hospitalization')
    axs[1,0].bar(x,deltaDeaths[startDur:dataLen],color=('k'))
    axs[1,0].set_title('death increase')
    axs[1,1].bar(x,deltaPos[startDur:dataLen],color=('xkcd:coral'))
    axs[1,1].set_title('daily new cases')
    plt.tight_layout()
    plt.savefig('tmp.jpg')
    plt.clf()

def trend(update, context):
    generateTrend(context)
    update.message.reply_photo(photo=open('tmp.jpg','rb'))

trend_handler=CommandHandler('trend',trend)
dispatcher.add_handler(trend_handler)

def thousands_formatter(x,pos):
    return str(int(x/1000))+'k'

def weekTrend(context):
    historicUrl = 'https://api.covidtracking.com/v1/us/daily.json'
    r = requests.get(historicUrl)
    rjson = r.json()
    deltaPos = [rjson[i]['positiveIncrease'] for i in range (len(rjson))]
    deltaTests = [rjson[i]['totalTestResultsIncrease'] for i in range (len(rjson))]
    curHosp = [rjson[i]['hospitalizedCurrently'] for i in range (len(rjson))]
    deltaDeaths = [rjson[i]['deathIncrease'] for i in range (len(rjson))]
    deltaHosp = [rjson[i]['hospitalizedIncrease'] for i in range (len(rjson))]
 
    date = [datetime.strptime(str(rjson[i]['date']),"%Y%m%d").date() for i in range (len(rjson))]
    strdate = [date[i].strftime("%A") for i in range (len(date))]
    def safediv(x,y):
        try:
            return x/y
        except ZeroDivisionError:
            return 0
    deltaRatio = [safediv(x,y) for x, y in zip(deltaPos,deltaTests)]
    deltaRatio.reverse()
    deltaHosp.reverse()
    curHosp.reverse()
    deltaDeaths.reverse()
    deltaPos.reverse()
    date.reverse()
    fig,axs=plt.subplots(2,2)
    if(context.args):
        duration = int( " ".join(context.args))*7 #we take in weeks
    else:
        duration = 7
    dataLen = len(deltaRatio)
    startDur = dataLen-duration
    x=np.arange(0,(dataLen-startDur))
     
    axs[0,0].plot(date[startDur:dataLen],deltaRatio[startDur-duration:dataLen-duration],color=('grey'),alpha=0.7,label='Previous week')
    axs[0,0].plot(date[startDur:dataLen],deltaRatio[startDur:dataLen],'xkcd:cerulean')
    axs[0,0].set_title('Daily Positive Ratio')
     
    axs[0,1].plot(date[startDur:dataLen],curHosp[startDur-duration:dataLen-duration],color=('grey'),alpha=0.7)
    axs[0,1].plot(date[startDur:dataLen],curHosp[startDur:dataLen],'xkcd:hot pink')
    hospAxis = axs[0,1].twinx()
    hospAxis.bar(date[startDur:dataLen],deltaHosp[startDur-duration:dataLen-duration],color=('grey'),alpha=0.5)
    hospAxis.bar(date[startDur:dataLen],deltaHosp[startDur:dataLen],color=('xkcd:lilac'),alpha=0.5)
    axs[0,1].set(ylabel="Currently Hospitalized")
    axs[0,1].yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    hospAxis.set(ylabel="New Hospitalization each day")
    hospAxis.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    axs[0,1].set_title('Hospitalization')
    
    axs[1,0].plot(date[startDur:dataLen],deltaDeaths[startDur-duration:dataLen-duration],color=('grey'),alpha=0.7)
    axs[1,0].plot(date[startDur:dataLen],deltaDeaths[startDur:dataLen],color=('black')) 
    axs[1,0].set_title('Death Increase')
    
    axs[1,1].plot(date[startDur:dataLen],deltaPos[startDur-duration:dataLen-duration],color=('grey'),alpha=0.7)
    axs[1,1].plot(date[startDur:dataLen],deltaPos[startDur:dataLen],color=('xkcd:coral'))
    axs[1,1].yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    axs[1,1].set_title('Daily New Cases')
    
    dtFmt = mdates.DateFormatter('%a')
    for i in range(2):
        for j in range(2):
            axs[i,j].xaxis.set_major_formatter(dtFmt)
            axs[i,j].spines['right'].set_color('none')
            axs[i,j].spines['top'].set_color('none')

    fig.legend(loc="lower left",bbox_to_anchor=(0.35, -0.01))
    plt.tight_layout()
    fig.suptitle(date[dataLen-1].strftime("%d %b %Y"))
    fig.subplots_adjust(bottom=0.1)
    plt.savefig('week.jpg',bbox_inches='tight')
    plt.clf()

def week(update, context):
    weekTrend(context)
    update.message.reply_photo(photo=open('week.jpg','rb'))

week_handler=CommandHandler('week',week)
dispatcher.add_handler(week_handler)





from selenium import webdriver
def vote(update, context):
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_argument("--remote-debugging-port=9222")
    chromeOptions.add_argument("--headless")
    chromeOptions.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(chrome_options=chromeOptions)
   # driver.get("https://www.bloomberg.com/graphics/2020-us-election-results")
    driver.set_window_position(0,0)
    driver.set_window_size(1024,1024)
    driver.get("https://www.google.com/search?&q=election")
    driver.save_screenshot("screen.png")
    update.message.reply_photo(photo=open('screen.png','rb'))

vote_handler = CommandHandler('vote',vote)
dispatcher.add_handler(vote_handler)



updater.start_polling()
