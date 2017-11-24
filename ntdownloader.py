#!/usr/bin/env python

import os
import sys
import argparse
from datetime import date, timedelta
from urllib.request import urlopen
import json
import requests
import re
import spotipy
import spotipy.util as util
import pprint
from tqdm import tqdm
from clint.textui import progress
from bs4 import BeautifulSoup

URL = "http://apipr.polskieradio.pl/api/playlist?date={}&antenneId=4";
SAVE_FILE_JSON = "data/{}.json"
SAVE_FILE_JSON_ALL = "data/all.json"
SAVE_FILE_MP3 = "data/{}.mp3"
AVAILABILITY_LOG = "availability.log"
AVAILABLE_LOG = "available.log"
UNAVAILABLE_LOG = "unavailable.log"
URL_RADIO = "https://www.polskieradio.pl"
URL_AUDITION = URL_RADIO + "/10/6069/Strona/{}";
HTTP = "http:{}"

def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('query', help="spotifuy query")

    args = parser.parse_args(arguments)

    #downloadjson()
    add_tracks_to_playlist()
    #downloadmp3()

def add_tracks_to_playlist():
    with open(SAVE_FILE_JSON_ALL, encoding='utf-8') as data_file:
        data = json.loads(data_file.read())

        scope = 'playlist-modify-public'
        token = util.prompt_for_user_token('lenygot', scope, client_id = 'c16cb518264d4a90ae5fbcabd8d417f7',
             client_secret = '0a31c89f3c1147059095e854cafdfef4', redirect_uri = 'https://zizul.github.io/callback')
        sp = spotipy.Spotify(auth=token)
        #sp.trace_out = True

        total_count = 0;
        available_count = 0

        with open(AVAILABILITY_LOG, 'w', encoding='utf8') as avaall, open(AVAILABLE_LOG, 'w', encoding='utf8') as ava, open(UNAVAILABLE_LOG, 'w', encoding='utf8') as unava:
            for audition in data:
                for song in audition['Songs']:
                    total_count += 1
                    
                    qry = '{} {}'.format(song['Artist'], song['Title'])
                    qry = qry.lower().replace("ft.", "") \
                        .replace("feat.", "").replace("PROD. BY ", "") \
                        .replace("feat", "").replace("remix", "") \
                        .replace("rework", "").replace("mix", "").replace("&", "")
                    results = sp.search(q=qry, limit=1)
                    items = results['tracks']['items']
                    if(len(items) > 0):
                        artist = song['Artist'] 
                        avaall.write(qry + ' ' + str(1) + "\n")
                        ava.write(qry + "\n")
                        print(qry + ' ' + str(1))
                        #print(items[0]['name'])
                        available_count += 1
                        #add_res = sp.user_playlist_add_tracks('lenygot', '2wNndlDuIvPRVr6VUN5JAR', {items[0]['id']})
                    else:
                        avaall.write(qry + ' ' + str(0) + "\n")
                        unava.write(qry + "\n")
                        print(qry + ' ' + str(0))

        print(str(total_count) + '/' +  str(available_count))

        # items = results['tracks']['items']
        # print('track id: ' + items[0]['name'] + ' ' + items[0]['id'])

        # results = sp.user_playlist_add_tracks('lenygot', '2wNndlDuIvPRVr6VUN5JAR', {items[0]['id']})    

def downloadjson():
    with open(SAVE_FILE_JSON_ALL, 'w', encoding='utf8') as all:
        all.write("[")
        for date in allsundays(2017):
            print(URL.format(date))
            jsn = requests.get(URL.format(date)).json()
            #pprint.pprint(jsn)
            #print(jsn[len(jsn)-1]['Title'])
            #print(jsn[len(jsn)-2]['Title'])
            if(len(jsn) > 0):
                with open(SAVE_FILE_JSON.format(date), 'w', encoding='utf8') as f:
                    print(SAVE_FILE_JSON.format(date))
                    print(len(jsn))
                    json.dump(jsn[len(jsn)-2], f, indent=4, sort_keys=True, ensure_ascii=False)
                    json.dump(jsn[len(jsn)-1], f, indent=4, sort_keys=True, ensure_ascii=False)
                    json.dump(jsn[len(jsn)-2], all, indent=4, sort_keys=True, ensure_ascii=False)
                    all.write(",")
                    json.dump(jsn[len(jsn)-1], all, indent=4, sort_keys=True, ensure_ascii=False)
                    all.write(",")

        all.write("]")

def downloadmp3():
    for i in range(1, 9):
        f = urlopen(URL_AUDITION.format(i))
        soup = BeautifulSoup(f, "html.parser")
        #print(URL_AUDITION.format(i))
        for i in soup.findAll('a', attrs={'href': re.compile('(?i).*6069/Artykul.*')}):
            #print(i['href'])
            audition_day_url = i['href']
            audition_day_content = urlopen(URL_RADIO + audition_day_url).read().decode('utf-8')
            #print(fa)
            mp3_pattern = re.compile("source: '(.*?\.mp3)'")
            mp3_url = re.findall(mp3_pattern, audition_day_content)
            if(len(mp3_url) > 0):
                #print(mp3_url[0])
                name_pattern = re.compile(",(.*)$")
                audition_day_name = re.findall(name_pattern, audition_day_url)
                mp3_file_name = SAVE_FILE_MP3.format(audition_day_name[0])

                file_head = requests.head(HTTP.format(mp3_url[0]))
                total_size = int(file_head.headers.get('content-length', 0));
                #print(format(os.path.isfile(mp3_file_name)))
                if(os.path.isfile(mp3_file_name) and os.path.getsize(mp3_file_name) == total_size):
                    print("skipping: " + audition_day_name[0])
                else:
                    print("downloading: " + audition_day_name[0])
                    if(os.path.isfile(mp3_file_name)):
                        print("size is: {}, should be: {}".format(os.path.getsize(mp3_file_name), total_size))
                    print("   " + HTTP.format(mp3_url[0]))

                    mp3_file = requests.get(HTTP.format(mp3_url[0]), stream=True)
                    
                    #print("   " + str(total_size))
                    with open(mp3_file_name, 'wb') as f:
                        for chunk in progress.bar(mp3_file.iter_content(chunk_size=1024), expected_size=(total_size/1024) + 1): 
                        #for chunk in tqdm(mp3_file.iter_content(1), total=total_size, unit='B', unit_scale=True):    
                            if chunk:
                                f.write(chunk)
                                f.flush()


def allsundays(year):
    d = date(year, 7, 1)                	
    d += timedelta(days = 9 - d.weekday())  # First Wednesday
    while d.year == year:
      yield d
      d += timedelta(days = 7)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))