# -*- coding: utf-8 -*-
import json
import urllib.request
from urllib import parse
from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template
import random

# 쓰레드, 큐를 위한 라이브러리 추가
import multiprocessing as mp
from threading import Thread

app = Flask(__name__)

slack_token = ""  # oAuth Access Token
slack_client_id = ""  # client id
slack_client_secret = ""
slack_verification = ""

sc = SlackClient(slack_token)

def processing_event(queue):
    while True:

        # 큐가 비어있지 않은 경우 로직 실행
        if not queue.empty():


            slack_event = queue.get()

            # Your Processing Code Block gose to here
            channel = slack_event["event"]["channel"]
            text = slack_event["event"]["text"]

            # 챗봇 크롤링 프로세스 로직 함수
            _crawl_naver_keywords(text[13:], channel)

def _crawl_profile(text, name, channel):
    print(name);
    keywords = [];
    ways = []
    count = -1;
    url = 'http://search.naver.com/search.naver?where=nexearch&query=';
    url = url + text;
    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")
    for title in enumerate(soup.find_all("dl", class_="detail_profile")):
        for tit in title[1].find_all('dd'):
            count = count + 1;
            if count != 0:
                tag_link = tit.find_all('a', href = True)
                if tag_link :
                    for link in tag_link :
                        link_ = link['href'];
                        if 'http://' in link_:
                            if 'twitter' in link_ :
                                ways.insert(0,link_);
                            else :
                                ways.append(link_);
                        else :
                            keywords.append(link.get_text());
                else :
                    keywords.append(tit.get_text() + '\n');

    keywords = u'\n'.join(keywords);
    attachments = [
        {
            "fallback": "Required plain-text summary of the attachment.",
            "color": "#FFA7A7",
            "author_name": name,
            "author_icon": "https://images.emojiterra.com/twitter/v11/512px/2764.png",
            "title": keywords,
            "txt": "",
            "ts": 123456789
        }
    ];

    sc.api_call(
         "chat.postMessage",
         channel=channel,
         as_user=False,
         text='',
         attachments = attachments
    );

    return ways;

def _crawl_photo(text, channel):
    url = "https://search.naver.com/search.naver?where=image&sm=tab_jum&query=";
    url = url + text;
    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser");
    urls = [];

    for idx, photo in enumerate(soup.find_all('a', class_='thumb _thumb')):
        if idx < 10:
            urls.append(photo.find('img')['data-source'])
    a= random.randrange(1,10)

    attachments = [
        {"fallback": "Required plain-text summary", "image_url": urls[a]}]
    sc.api_call("chat.postMessage", channel=channel, as_user=False, text='', attachments=attachments)

def _crwal_twitter(name, twitter_link,channel):
    soup = BeautifulSoup(urllib.request.urlopen(twitter_link).read(), "html.parser");
    fields = []


    for idx, tweet in enumerate(soup.find_all('div','content')):
        txt = []
        time = []
        time_ = []
        if idx < 3:
            for x in tweet.find_all('p', class_='TweetTextSize TweetTextSize--normal js-tweet-text tweet-text'):
                txt.append(x.get_text())
            txt.append('\n')
            print(txt)
            txt= u'\n'.join(txt);

            for x in tweet.find_all('small', class_='time'):
                time.append(x.get_text())
            time = u'\n'.join(time);
            fields.append({'title':time, 'value':txt, 'short':False})

    attachments = [
        {
            "fallback": "Required plain-text summary of the attachment.",
            "color": "#3AA3E3",
            "author_name": name + "의 최근 Twitter",
            "author_icon": "https://is2-ssl.mzstatic.com/image/thumb/Purple128/v4/c3/17/43/c31743d4-6279-0a62-ef88-f39348a2f471/ProductionAppIcon-0-1x_U007emarketing-0-0-GLES2_U002c0-512MB-sRGB-0-0-0-85-220-0-0-0-7.png/246x0w.jpg",
            "title": "",
            "text": "",
            "fields": fields,
            "ts": 123456789
        }
    ]
    sc.api_call("chat.postMessage", channel=channel, as_user=False, text='', attachments=attachments)

def _print_qus_button(channel, ways):
    actions = []
    for way in ways:
        waydic = {}
        if 'twitter' in way:
            waydic["name"] = 'twitter';
            waydic["text"] = '*Twitter*';
            waydic["type"] = 'button';
            waydic["url"] = way;
            actions.append(waydic);
        elif 'facebook' in way:
            waydic["name"] = 'facebook';
            waydic["text"] = '*Facebook*';
            waydic["type"] = 'button';
            waydic["url"] = way
            actions.append(waydic);
        elif 'instagram' in way:
            waydic["name"] = 'instagram';
            waydic["text"] = '*Instagram*';
            waydic["type"] = 'button';
            waydic["url"] = way;
            actions.append(waydic);
        elif 'youtube' in way:
            waydic["name"] = 'youtube';
            waydic["text"] = 'Youtube';
            waydic["type"] = 'button';
            waydic["url"] = way;
            actions.append(waydic);
    if not actions:
        attachments = [
            {
                "title": "",
                "text": "",
                "fallback": "You are unable to choose",
                "callback_id": "wopr_choice",
                "color": "#36a64f",
                "attachment_type": "default",
                "actions": actions
            }
        ]
        sc.api_call("chat.postMessage", channel=channel, as_user=False, text='\n\n\n*이제 덕질을 좀 해보실까요??*',
                    attachments=attachments);
    else :
        attachments = [
            {
                "title": "",
                "text": "*아래의 방법으로 덕질을 할 수 있습니다.*",
                "fallback": "You are unable to choose",
                "callback_id": "wopr_choice",
                "color": "#36a64f",
                "attachment_type": "default",
                "actions": actions
            }
        ]
        sc.api_call("chat.postMessage", channel=channel, as_user=False, text='\n\n\n*이제 덕질을 좀 해보실까요??*',
                attachments=attachments);



def _crawl_detail_profile(name, channel):
    text = parse.quote(name);
    text = text.replace(' ', '+');
    _crawl_photo(text, channel);
    ways = _crawl_profile(text,name,channel);
    print(len(ways))
    if not ways:
        pass;
    else :
        if 'twitter' in ways[0] :
            _crwal_twitter(name, ways[0] ,channel);
        _print_qus_button(channel,ways);
# 크롤링 함수 구현하기

def _crawl_naver_keywords(text,channel):
    print(text)
    _crawl_detail_profile(text, channel);

# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):

    if event_type == "app_mention":
        event_queue.put(slack_event)


        return make_response("App mention message has been sent", 200, )

    else :
    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
        message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
        return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })
    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    event_queue = mp.Queue()

    p = Thread(target=processing_event, args=(event_queue,))
    p.start()

    app.run(port=5000, debug=True)
    p.join()