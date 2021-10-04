# twitter-data-analysis
Show figures and charts of CSV data getting from Twitter API.
For analysis, you can save tweets and followers data to Google Cloud Storage every day.

Twitter APIから取得したcsvデータを分析してグラフ表示します。

## tweet_data_save.py
Twitter APIからツイートに関するデータを分析用に取得して、定期的にcsvファイルに保存します。
（「日時」「テキスト」「文字数」「いいね数」「リツイート数」）
[Google Cloud Platform]の[Cloud Functions]にデプロイして、[Cloud Scheduler]で定期実行します。
[Storge]にcsvを更新して保存します。
※Twitterアカウント名, TwitterAPIのキーが必要ですので、必要に応じて書き換えてください。

## followers_data_save.py
Twitter APIからフォロワーに関するデータを分析用に取得して、定期的にcsvファイルに保存します。
（ID、スクリーン名、フォロワー数、フォロー数、ユーザー名、場所、URL、プロフィール）
[Google Cloud Platform]の[Cloud Functions]にデプロイして、[Cloud Scheduler]で定期実行します。
[Storge]にcsvを更新して保存します。
※Twitterアカウント名, TwitterAPIのキーが必要ですので、必要に応じて書き換えてください。

## twitter_analysis_streamlit.py
Twitter APIから取得したcsvデータから分析。
フォロワー数、いいね数、リツイート数などをグラフ表示。
streamlitを使ったwebアプリです。
※パスワードやcsvファイルのパスはstreamlitのシークレットに保存する必要があります。

## requirement.txt
twitter_analysis_streamlit.pyファイルのみデプロイ用に作成しています。
tweet_data_save.py, followers_data_save.pyのデプロイ時には、tweepyを追加する必要があります。
