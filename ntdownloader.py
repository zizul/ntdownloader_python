#!/usr/bin/env python

import os
import sys
import argparse
from datetime import date, timedelta
from urllib.request import urlopen
#from urllib2 import urlopen
import json
import requests
import re
import spotipy
import spotipy.util as util
import pprint
from tqdm import tqdm
from clint.textui import progress
import unicodedata

from bs4 import BeautifulSoup

URL = "http://apipr.polskieradio.pl/api/playlist?date={}&antenneId=4";
SAVE_FILE_JSON = "data/{}.json"
SAVE_FILE_JSON_ALL = "data/all.json"
SAVE_FILE_MP3 = "data/{}.mp3"
AVAILABILITY_LOG = "availability.log"
AVAILABLE_LOG = "available.log"
UNAVAILABLE_LOG = "unavailable.log"
PLAYLIST_TRACKS_IDS = "pl_tr_id.log"
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
    #get_playlist_tracks()

    # results = sp.user_playlist("lenygot", "2wNndlDuIvPRVr6VUN5JAR", fields="tracks,next")
    # arts = [str(unicodedata.normalize('NFKD', item['track']['artists'][0]['name']).encode('ascii', 'ignore'),'utf-8') + " " + str(unicodedata.normalize('NFKD', item['track']['name']).encode('ascii', 'ignore'),'utf-8') for item in results['tracks']['items']]
    # for i, a in enumerate(arts):
    #     print("{} {}".format(i, a))

def get_playlist_tracks():
    scope = 'playlist-modify-public'
    token = util.prompt_for_user_token('lenygot', scope, client_id = 'c16cb518264d4a90ae5fbcabd8d417f7',
         client_secret = '0a31c89f3c1147059095e854cafdfef4', redirect_uri = 'https://zizul.github.io/callback')
    sp = spotipy.Spotify(auth=token)

    current_count = 0;
    available_count = 0

    results = sp.user_playlist_tracks("lenygot", "2wNndlDuIvPRVr6VUN5JAR")
    ids = [item['track']['id'] for item in results['items']]
    #arts = [str(unicodedata.normalize('NFKD', item['track']['artists'][0]['name']).encode('ascii', 'ignore'),'utf-8') + " " + str(unicodedata.normalize('NFKD', item['track']['name']).encode('ascii', 'ignore'),'utf-8') for item in results['items']]
    while results['next']:
        results = sp.next(results)
        ids.extend([item['track']['id'] for item in results['items']])
        #arts.extend([str(unicodedata.normalize('NFKD', item['track']['artists'][0]['name']).encode('ascii', 'ignore'),'utf-8') + " " + str(unicodedata.normalize('NFKD', item['track']['name']).encode('ascii', 'ignore'),'utf-8') for item in results['items']])
    # arts = [" ".join(a.lower().replace("ft.", "") \
    #                     .replace("feat.", "").replace("PROD. BY ", "") \
    #                     .replace("feat", "").replace("remix", "") \
    #                     .replace("rework", "").replace("mix", "").replace("&", "").split()) for a in arts]
    #for i, a in enumerate(arts):
    #   print("{} {}".format(i, a))
    return ids

def add_tracks_to_playlist():
    with open(SAVE_FILE_JSON_ALL, encoding='utf-8') as data_file:
        data = json.loads(data_file.read())
        total_count = 0;
        for audition in data:
            total_count += len(audition['Songs'])
        scope = 'playlist-modify-public'
        token = util.prompt_for_user_token('lenygot', scope, client_id = 'c16cb518264d4a90ae5fbcabd8d417f7',
             client_secret = '0a31c89f3c1147059095e854cafdfef4', redirect_uri = 'https://zizul.github.io/callback')
        sp = spotipy.Spotify(auth=token)

        current_count = 0;
        available_count = 0
        pl_tracks = get_playlist_tracks()
        i = 0
        tracks_to_playlist = []
        if not os.path.exists(PLAYLIST_TRACKS_IDS): open(PLAYLIST_TRACKS_IDS, "w+").close()
        with open(AVAILABILITY_LOG, 'w', encoding='utf8') as avaall, open(AVAILABLE_LOG, 'w', encoding='utf8') as ava, open(UNAVAILABLE_LOG, 'w', encoding='utf8') as unava:
            ### GO THROUGH ALL SONGS FROM ALL AUDITIONS JSON
            for audition in data:
                for song in audition['Songs']:
                    current_count += 1

                    artist = xstr(song['Artist']).lower().replace("ft.", "") \
                        .replace("feat.", "").replace("PROD. BY ", "") \
                        .replace("feat", "").replace("remix", "") \
                        .replace("rework", "").replace("mix", "").replace("&", "")
                    title = song['Title'].lower().replace("ft.", "") \
                        .replace("feat.", "").replace("PROD. BY ", "") \
                        .replace("feat", "").replace("remix", "") \
                        .replace("rework", "").replace("mix", "").replace("&", "")
                    qry = '{} {}'.format(artist, title)
                    qry = " ".join(qry.split())
                    track_id = ""

                    ### SEARCH FOR SONG IN CACHE
                    with open(PLAYLIST_TRACKS_IDS, 'r', encoding='utf8') as pl_tr_id:
                        lines = pl_tr_id.readlines()
                        #print(lines)
                        for line in lines:
                            #print("reading " + line)
                            if qry in line and str(current_count) == line.split(";")[0] :
                                track_id = line.split(";")[2]

                    ### IF NOT IN CACHE -> QUERY SPOTIFY FOR IT             
                    if(track_id == ""):    
                        results = sp.search(q=qry, limit=1)
                        items = results['tracks']['items']
                        ### IF IN SPOTIFY -> ADD IT TO CACHE AND TO PLAYLIST
                        if(len(items) > 0):
                            with open(PLAYLIST_TRACKS_IDS, 'a', encoding='utf8') as pl_tr_id:
                                pl_tr_id.write(str(current_count) + ";"+qry + ";" + items[0]['id']+"\n")
                                print("{}/{}".format(current_count, total_count) + " writing " + qry + ";" + items[0]['id'])
                            tracks_to_playlist.append(items[0]['id'])
                            artist = song['Artist'] 
                            avaall.write(qry + ' ' + str(1) + "\n")
                            ava.write(qry + "\n")
                            #print(qry + ' ' + str(1))
                            #print(items[0]['name'])
                            available_count += 1
                            #add_res = sp.user_playlist_add_tracks('lenygot', '2wNndlDuIvPRVr6VUN5JAR', {items[0]['id']})
                        else: 
                            #results = sp.search(q=title, limit=1)
                            #arts = " ".join([art["name"] for art in results['tracks']['items'][0]['artists']])
                            #print("arts: " + arts)
                            avaall.write(qry + ' ' + str(0) + "\n")
                            unava.write(qry + "\n")
                            print("   {}/{} ".format(current_count, total_count) +  qry + ' ' + str(0))
                    else:
                        print("### in playlist " + qry)

        ### ADD PREVIOUSLY COLLECTED TRACKS TO PLAYLIST IN BATCHES 
        #for i in range(0, len(tracks_to_playlist), 100):
            #if i == 0:
                #add_res = sp.user_playlist_replace_tracks('lenygot', '2wNndlDuIvPRVr6VUN5JAR', tracks_to_playlist[i:i+100])
            #add_res = sp.user_playlist_add_tracks('lenygot', '2wNndlDuIvPRVr6VUN5JAR', tracks_to_playlist[i:i+100])
        print(str(current_count) + '/' +  str(available_count))

        # items = results['tracks']['items']
        # print('track id: ' + items[0]['name'] + ' ' + items[0]['id'])

        # results = sp.user_playlist_add_tracks('lenygot', '2wNndlDuIvPRVr6VUN5JAR', {items[0]['id']})    

def xstr(s):
    if s is None:
        return ''
    return s

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