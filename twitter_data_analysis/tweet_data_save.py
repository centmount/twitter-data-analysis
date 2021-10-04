#!/usr/bin/env python3

"""
Twitter APIからツイートに関するデータを分析用に取得して、定期的にcsvファイルに保存します。
（「日時」「テキスト」「文字数」「いいね数」「リツイート数」）
[Google Cloud Platform]の[Cloud Functions]にデプロイして、[Cloud Scheduler]で定期実行します。
[Storge]にcsvを更新して保存します。
"""

# 必要なモジュールのインストール
import tweepy
from datetime import datetime, timedelta
import csv
import os
from google.cloud import storage

# Twitterアカウント名(@含まず、＠以降)、各種ツイッターのキーを入力
def input_twitter_info():
    global screen_name
    global CONSUMER_KEY
    global CONSUMER_SECRET
    global ACCESS_KEY
    global ACCESS_SECRET
    while True:
        screen_name = input('Twitterアカウント名(@含まず、@以降)を入力して下さい: ') # Twitterアカウント名を入力
        CONSUMER_KEY = input('TwitterAPIのCONSUMER_KEYを入力して下さい: ') # TwitterAPIのキーが必要
        CONSUMER_SECRET = input('TwitterAPIのCONSUMER_SECRETを入力して下さい: ')
        ACCESS_KEY = input('TwitterAPIのACCESS_KEYを入力して下さい: ')
        ACCESS_SECRET = input('TwitterAPIのACCESS_SECRETを入力して下さい: ')
        ok = input('入力完了しましたか？(完了の場合 OK と入力): ')
        if ok == 'OK':
            break
    return screen_name, CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET


# 現在時刻
now_time = datetime.now() + timedelta(hours=9)


# ツイッターAPIにアクセス
# OAuth認証
def authTwitter():
    global api
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    #APIインスタンスを作成、レート制限が補充されるまで待機、残り時間を知らせる
    api = tweepy.API(auth, wait_on_rate_limit = True, wait_on_rate_limit_notify=True)
    return api

# データ保存用のファイルパス
FILE_PATH = '/tmp/tweets.csv'

# ファイルが存在するかどうか確認
def is_file():
    global file_check
    file_check = os.path.isfile(FILE_PATH)
    return file_check

# 全ツイートを入れる空のリストを用意
all_tweets = []

# ファイルが存在しない場合、すべてのツイートをリストに入れる
def get_data():
    global all_tweets
    if not file_check:
        for status in tweepy.Cursor(api.user_timeline, screen_name=screen_name).items():
            all_tweets.append(status)
    # ファイルが存在する場合、最新ツイート100件をリストに入れる
    else:
        for status in tweepy.Cursor(api.user_timeline, screen_name=screen_name).items(100):
            all_tweets.append(status)
    return all_tweets

# csvファイルに「日時」「テキスト」「文字数」「いいね数」「リツイート数」を保存
def data_save():
    # ファイルが存在しない場合、新規ファイル作成
    if not file_check:
        with open(FILE_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['save_time','followers', 'tweet_id', 'created_at', 'tweet_text', 'characters', 'favorited', 'retweeted'])
            for tweet in all_tweets:
                tweet.created_at = tweet.created_at + timedelta(hours=9) # 日本時間に修正
                if (tweet.text.startswith('RT')) or (tweet.text.startswith('@')):
                    continue # RTとリプライはスキップ
                else:
                    tweet_characters = tweet.text # ツイートの文字列
                    # urlは、文字数としてカウントしない
                    if len(tweet.entities['urls']) > 0:
                        tweet_characters = tweet_characters.strip(tweet.entities['urls'][0]['url']).strip()
                    writer.writerow([now_time, tweet.user.followers_count, tweet.id, tweet.created_at, tweet.text, len(tweet_characters), tweet.favorite_count, tweet.retweet_count])
    
    # ファイルが存在する場合、データを追加(最新ツイート100件からRTとリプライを除く)
    else:
        with open(FILE_PATH, 'a', newline='') as f:
            writer = csv.writer(f)
            for tweet in all_tweets:
                tweet.created_at = tweet.created_at + timedelta(hours=9) # 日本時間に修正
                if (tweet.text.startswith('RT')) or (tweet.text.startswith('@')):
                    continue # RTとリプライはスキップ
                else:
                    tweet_characters = tweet.text # ツイートの文字列
                    # urlは、文字数としてカウントしない
                    if len(tweet.entities['urls']) > 0:
                        tweet_characters = tweet_characters.strip(tweet.entities['urls'][0]['url']).strip()
                    writer.writerow([now_time, tweet.user.followers_count, tweet.id, tweet.created_at, tweet.text, len(tweet_characters), tweet.favorite_count, tweet.retweet_count])

# Storageへのアップロード処理
def upload_blob(bucket_name, source_file_name, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)  

# Storageからのダウンロード処理
def download_blob(bucket_name, source_blob_name, destination_file_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

# main関数を実行(GCPのCloud Functions用にevent,contextが引数に)
# トリガーをpub/subに設定、ファイルダウンロードしてデータ追加してアップロード
def main(event, context):
    input_twitter_info()
    download_blob('ストレージのバケット名を指定', 'ストレージに保存されているファイル名を指定', FILE_PATH)
    authTwitter()
    is_file()
    get_data()
    data_save()
    upload_blob('ストレージのバケット名を指定', FILE_PATH, 'ストレージに保存するファイル名を指定')


