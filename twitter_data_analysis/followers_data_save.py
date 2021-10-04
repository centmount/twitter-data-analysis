#!/usr/bin/env python3

"""
Twitter APIからフォロワーに関するデータを分析用に取得して、定期的にcsvファイルに保存します。
（ID、スクリーン名、フォロワー数、フォロー数、ユーザー名、場所、URL、プロフィール）
[Google Cloud Platform]の[Cloud Functions]にデプロイして、[Cloud Scheduler]で定期実行します。
[Storge]にcsvを更新して保存します。
"""

# 必要なモジュールのインポート
import tweepy
from datetime import datetime, timedelta
import os
import csv
import pandas as pd
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
    #APIインスタンスを作成、レート制限が補充されるまで待機
    api = tweepy.API(auth, wait_on_rate_limit = True)
    return api

# データ保存用のファイルパス
FILE_PATH = '/tmp/followers.csv'

# ファイルが存在するかどうか確認
def is_file():
    global file_check
    file_check = os.path.isfile(FILE_PATH)
    return file_check

# ファイルをpandas読み取り
def read_csv():
    global df
    if file_check:
        df = pd.read_csv(FILE_PATH)
        return df


# フォロワー情報を入れる空のリストを用意
user_infos = []


#設定したTwitterアカウントのフォロワー情報を取得（ID、スクリーン名、フォロワー数、フォロー数、ユーザー名、場所、URL、プロフィール）
def get_data():
    global user_infos
    cursor = -1
    if not file_check:
        while cursor != 0:
            itr = tweepy.Cursor(api.followers_ids, id=screen_name, cursor=cursor).pages()
            try:
                for follower_id in itr.next():
                    try:
                        user = api.get_user(follower_id)
                        user_info = [now_time, user.id_str, user.screen_name, user.followers_count, user.friends_count,
                                     user.name, user.location, user.url, user.description]
                        print(user.screen_name)
                        user_infos.append(user_info)
                    except tweepy.error.TweepError as e:
                        print(e.reason)
            except ConnectionError as e:
              print(e.reason)
            cursor = itr.next_cursor
    # ファイルに重複がないデータのみリストに追加
    else:
        for follower_id in tweepy.Cursor(api.followers_ids, id=screen_name, cursor=cursor).items(100):
            user = api.get_user(follower_id)
            user_info = [now_time, user.id_str, user.screen_name, user.followers_count, user.friends_count,
                         user.name, user.location, user.url, user.description]
            # user_idがファイルに存在するかどうか判定
            if not str(user.id_str) in list(df['user_id']):
                print(user.screen_name)
                user_infos.append(user_info)
    print("[処理が完了しました]")
    return user_infos


# フォロワー情報のリストをpandasのDataFrameに変換
def to_DataFrame():
    global df_new
    list1= user_infos
    columns1 = ['save_time', 'user_id', 'screen_name', 'folowers_count', 
                'friends_count', 'user_name', 'location', 'user_url', 'description']
    df1 = pd.DataFrame(data=list1, columns=columns1)
    df2 = df1.sort_index(ascending=False)
    if file_check:
        df_new = pd.concat([df, df2])
    else:
        df_new = df2
    return df_new


# csvファイルに保存
def data_save():
    df_new.to_csv(FILE_PATH, index = False)
    print('[csvファイル保存しました]')
   

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
    read_csv()
    get_data()
    to_DataFrame()    
    data_save()
    upload_blob('ストレージのバケット名を指定', FILE_PATH, 'ストレージに保存するファイル名を指定')

