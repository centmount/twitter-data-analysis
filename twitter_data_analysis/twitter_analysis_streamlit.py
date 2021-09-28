#!/usr/bin/env python3

"""
Twitter APIから取得したcsvデータから分析。
フォロワー数、いいね数、リツイート数をグラフ表示。
streamlitを使ったwebアプリです。
"""

# 必要なモジュールのインストール
import streamlit as st
from streamlit import caching
from matplotlib import pyplot as plt
import matplotlib.dates as mdates

import pandas as pd
from bokeh.io import show
from bokeh.plotting import figure, ColumnDataSource, output_file, show, reset_output
from bokeh.layouts import column, gridplot
from bokeh.models import DataSource, RangeTool, HoverTool, DatetimeTickFormatter, Range1d
import bokeh.palettes as bp
from datetime import datetime, timedelta
import os

# パスワードでログイン
def login():
    value = st.text_input('パスワードを入力してください:', type='password')
    while value != st.secrets['password'] :
        print('正しいパスワードを入力してください')
    st.text('正しいパスワードが入力されました')

login()

# 現在時刻
now_time = datetime.now() + timedelta(hours=9)

# ツイートごとAPIデータへのファイルのパス
FILE_PATH_1 = st.secrets['file_path']

# フォロワー詳細データファイル読み込み
FILE_PATH_2 = st.secrets['file_path_2']

# Twitterアナリティクスの月ごとデータ(2017/04-2021/09)
FILE_PATH_3 = st.secrets['file_path_3']

# Twitterアナリティクスのツイートごとデータ(2020/10-2021/09)
FILE_PATH_4 = st.secrets['file_path_4']


st.title('Twitterデータ分析')

# csvファイルをpandasで読み取り
@st.cache
def load_data():
    df = pd.read_csv(FILE_PATH_1)
    df['save_time'] = pd.to_datetime(df['save_time'])
    df['created_at'] = pd.to_datetime(df['created_at'])
    return df

@st.cache
def load_data2():
    df_followers = pd.read_csv(FILE_PATH_2)
    return df_followers

@st.cache
def load_data3():
    df_month = pd.read_csv(FILE_PATH_3)
    df_month['日時'] = pd.to_datetime(df_month['日時'])
    df_month = df_month.set_index('日時')
    return df_month

@st.cache
def load_data4():
    tweets_df = pd.read_csv(FILE_PATH_4)
    tweets_df['時間'] = pd.to_datetime(tweets_df['時間'])
    return tweets_df

# データ読取実行
data_load_state = st.text('Loading data...')
df = load_data()
df_followers = load_data2()
df_month = load_data3()
tweets_df = load_data4()
data_load_state.text('Loading data...Done!')

st.write('ツイートごとのデータ (2017/4～最新更新)')

st.dataframe(df.sort_index(ascending=False), width=1000, height=200)

# 保存時間でグループ分け
df_save_time = df.groupby('save_time').mean()

# フォロワー数グラフ作成用の辞書
x = df_save_time.index
y = df_save_time['followers']
date = x.strftime('%Y-%m-%d %H:%M:%S')
source = ColumnDataSource(data = dict(x = x, y = y, date=date))

# tooltips設定
hover_tool = HoverTool(tooltips = [('date and time', '@date'), ('followers', '@y')], mode='mouse')

# グラフ全体の設定
fig1 = figure(tools=[hover_tool], title='最新フォロワー数', plot_width=800, plot_height=400, 
           x_axis_label='date', y_axis_label='followers', x_axis_type='datetime', background_fill_color='DarkGreen')

# X軸の設定
x_format = "%m/%d"
fig1.xaxis.formatter = DatetimeTickFormatter(days=[x_format], months=[x_format], years=[x_format])

# 折れ線図
fig1.line('x', 'y', line_width=3, legend_label='フォロワー数', source=source, color='Aqua')

# 散布図
fig1.circle('x', 'y', size=15, fill_alpha=0.5, source=source, color='Aqua')

# 凡例の位置
fig1.legend.location = 'top_left'

# 描画
# output_file('followers.html')
show(fig1, use_container_width=True)

st.bokeh_chart(fig1)

# ツイート時間でグループ分け
df_created_at = df.groupby('created_at').mean()

# ツイートごと「いいね数」グラフ作成用の辞書
x = df_created_at.index
y = df_created_at['favorited'].astype(int)
date = x.astype(str)
source = ColumnDataSource(data = dict(x=x, y=y, date=date))

# tooltips設定
hover_tool = HoverTool(tooltips = [('ツイート日時', '@date'), ('いいね数', '@y')], mode='mouse')

# グラフ全体の設定
p = figure(tools=[hover_tool], title='ツイートごとの「いいね数」 (2017/4～最新更新)', plot_width=1200, plot_height=400,
           x_range = [x[0], x[-1]], x_axis_label='ツイート日時', y_axis_label='favorited', x_axis_type='datetime', background_fill_color='DarkGreen')

# X軸の設定
x_format = "%Y/%m/%d"
p.xaxis.formatter = DatetimeTickFormatter(days=[x_format], months=[x_format], years=[x_format])

# 折れ線図
p.line('x', 'y', legend_label='「いいね」数', source=source, color='yellow')

# 散布図
p.asterisk('x', 'y', size=10, fill_alpha=0.5, source=source, color='yellow')

# 凡例の位置
p.legend.location = 'top_left'

# rangetoolの作成
# rangetoolは、グラフの描画範囲をスライダーで変更することができます。
# rangetool用のグラフの設定を追加
select = figure(title="上段のグラフの表示範囲をスライダーで指定",
                plot_height=130, plot_width=1200, y_range=p.y_range,
                x_axis_type="datetime", y_axis_type=None,
                tools="", toolbar_location=None, background_fill_color="#efefef")

# Rangetoolの設定
range_rool = RangeTool(x_range=p.x_range) # Rangetoolのx_rangeの範囲を設定（p.x_range)
range_rool.overlay.fill_color = "navy"    # overlay.fill_colorはスライダーの色を指定
range_rool.overlay.fill_alpha = 0.2       # 透明度の指定

select.line(x=x, y=y) # p.lineと同様にx軸とy軸の設定
select.ygrid.grid_line_color = None
select.add_tools(range_rool) # range_roolを追加
select.toolbar.active_multi = range_rool

# 描画
# output_file('favorited.html')
fig2 = column(p,select)
show(fig2, use_container_width=True)

st.bokeh_chart(fig2)

# 時刻でグループ分け
df_created_at['hour'] = df_created_at.index.hour
df_hour = df_created_at.groupby('hour').mean()

# 時刻ごとグラフ作成用の辞書
x = df_hour.index
y = df_hour['favorited'].astype(int)
y2 = df_hour['retweeted'].astype(int)

source = ColumnDataSource(data = dict(x = x, y = y, y2=y2))

# tooltips設定
hover_tool_1 = HoverTool(tooltips = [('時刻', '@x'), ('いいね数', '@y')], mode='mouse')
hover_tool_2 = HoverTool(tooltips = [('時刻', '@x'), ('リツイート数', '@y2')], mode='mouse')

# グラフ全体の設定
p1 = figure(tools=[hover_tool_1], title='いいね数 (時刻ごと平均)  2017年4月～最新更新',
            plot_width=800, plot_height=400, x_axis_label='hour', y_axis_label='いいね数',
            background_fill_color='DarkGreen')

p2 = figure(tools=[hover_tool_2], title='リツイート数 (時刻ごと平均)  2017年4月～最新更新',
            plot_width=800, plot_height=400, x_axis_label='hour', y_axis_label='リツイート数',
            background_fill_color='DarkGreen')

# 棒グラフ
p1.vbar(x='x', width=0.5, top='y', legend_label='いいね数(平均)', source=source, color='Lime')
p2.vbar(x='x', width=0.5, top='y2', legend_label='リツイート数(平均)', source=source, color='Magenta')

# 凡例の位置
p1.legend.location = 'top_left'
p2.legend.location = 'top_left'

# 描画
# output_file('hours_data.html')
fig3 = gridplot([[p1], [p2]])
show(fig3)

st.bokeh_chart(fig3, use_container_width=False)

st.write('いいね数の平均', df_created_at['favorited'].mean()) 
st.write('いいね数の中央値', df_created_at['favorited'].median())
st.write('リツイート数の平均', df_created_at['retweeted'].mean()) 
st.write('リツイート数の中央値', df_created_at['retweeted'].median())


st.write('フォロワーに関するデータ (2017/4～最新更新)')

st.dataframe(df_followers.sort_index(ascending=False), width=1000, height=200)

df_followers_mean = df_followers.groupby('user_id').mean()

# 「フォロワー数」と「フォロー数」グラフ作成用の辞書
x = df_followers_mean['folowers_count']
y = df_followers_mean['friends_count']

source = ColumnDataSource(data = dict(x = x, y = y))

# tooltips設定
hover_tool_1 = HoverTool(tooltips = [('フォロワー数', '@x'), ('フォロー数', '@y')], mode='mouse')

# グラフ全体の設定
fig4 = figure(tools=[hover_tool_1], title='フォロワーごとの「フォロワー数」「フォロー数」(2017/4～最新更新)',
            plot_width=800, plot_height=400, x_axis_label='フォロワー数', y_axis_label='フォロー数',
            background_fill_color='Darkgreen')

# 散布図
fig4.circle('x', 'y', size=15, fill_alpha=0.7, source=source, color='Aqua', legend_label='「フォロワー数」と「フォロー数」')

# 凡例の位置
fig4.legend.location = 'top_left'

# 描画
#output_file('tweet_data.html')
show(fig4)

st.bokeh_chart(fig4)


# Twitterアナリティクスの月ごとデータ(2017/04-2021/09)
st.write('Twitterアナリティクスの月ごとデータ(2017/04-2021/09)')

st.dataframe(df_month, width=1000, height=200)

# 過去のグラフ作成用の辞書
x = df_month.index
y = df_month['フォロワー数']
y2 = df_month['インプレッション数']
y3 = df_month['ツイート数']
y4 = df_month['プロフィールアクセス']

date = x.astype(str)
date2 = x.strftime('%Y-%m')
source = ColumnDataSource(data = dict(x = x, y = y, y2=y2, y3=y3, y4=y4, date=date, date2=date2))

# tooltips設定
hover_tool_1 = HoverTool(tooltips = [('date', '@date'), ('followers', '@y')], mode='mouse')
hover_tool_2 = HoverTool(tooltips = [('date', '@date2'), ('Impression', '@y2')], mode='mouse')
hover_tool_3 = HoverTool(tooltips = [('date', '@date2'), ('Tweets', '@y3')], mode='mouse')
hover_tool_4 = HoverTool(tooltips = [('date', '@date2'), ('Profile Access', '@y4')], mode='mouse')

# グラフ全体の設定
p1 = figure(tools=[hover_tool_1], title='月ごとフォロワー数(2017/4-2021/9)', plot_width=800, plot_height=400, 
           x_axis_label='date', y_axis_label='followers', x_axis_type='datetime',
           background_fill_color='Navy')

p2 = figure(tools=[hover_tool_2], title='月間インプレッション数(2017/4-2021/9 Monthly)', plot_width=800, plot_height=400, 
           x_axis_label='date', y_axis_label='Impression', x_axis_type='datetime',
           background_fill_color='Navy')

p3 = figure(tools=[hover_tool_3], title='月間ツイート数(2017/4-2021/9 Monthly)', plot_width=800, plot_height=400, 
           x_axis_label='date', y_axis_label='Tweets', x_axis_type='datetime',
           background_fill_color='Navy')

p4 = figure(tools=[hover_tool_4], title='月間プロフィールアクセス数(2017/4-2021/9 Monthly)', plot_width=800, plot_height=400, 
           x_axis_label='date', y_axis_label='Profile Access', x_axis_type='datetime',
           background_fill_color='Navy')


# X軸の設定
x_format = "%Y/%m"
p1.xaxis.formatter = DatetimeTickFormatter(months=[x_format], years=[x_format])
p2.xaxis.formatter = DatetimeTickFormatter(months=[x_format], years=[x_format])
p3.xaxis.formatter = DatetimeTickFormatter(months=[x_format], years=[x_format])
p4.xaxis.formatter = DatetimeTickFormatter(months=[x_format], years=[x_format])

# y軸の設定
p2.y_range=Range1d(start=0,end=1000000)

# 折れ線図
p1.line('x', 'y', legend_label='フォロワー数', source=source, color='Aqua')

# 棒グラフ
p2.vbar(x=x, width=0.5, bottom=0, top=y2, color='Lime', legend_label='インプレッション数')
p3.vbar(x=x, width=0.5, bottom=0, top=y3, color='Yellow', legend_label='ツイート数')
p4.vbar(x=x, width=0.5, bottom=0, top=y4, color='Magenta', legend_label='プロフィールアクセス数')

# 散布図
p1.circle('x', 'y', size=10, fill_alpha=0.5, source=source, color='Aqua')
p2.cross('x', 'y2', size=10, fill_alpha=0.5, source=source, color='Lime')
p3.asterisk('x', 'y3', size=10, fill_alpha=0.5, source=source, color='Yellow')
p4.square('x', 'y4', size=10, fill_alpha=0.5, source=source, color='Magenta')


# 凡例の位置
p1.legend.location = 'top_left'
p2.legend.location = 'top_left'
p3.legend.location = 'top_left'
p4.legend.location = 'top_left'


# 描画
#output_file('tweet_month_data.html')
fig5 = gridplot([[p1, p2], [p3, p4]])
show(fig5)

st.bokeh_chart(fig5)


# Twitterアナリティクスのtツイートごとデータ(2020/10-2021/09)
st.write('Twitterアナリティクスのツイートごとデータ(2020/10-2021/09)')

time_index_df = tweets_df.sort_values(by='時間').set_index('時間')
time_index_df = time_index_df.drop('Unnamed: 0', axis=1)
st.dataframe(time_index_df, width=1000, height=200)

# グラフ作成用の辞書
x = time_index_df.index
date = x.strftime('%Y-%m-%d %H:%M:%S')
y = time_index_df['インプレッション']
y2 = time_index_df['エンゲージメント']

source = ColumnDataSource(data = dict(x = x, y = y, y2=y2, date=date))

# tooltips設定
hover_tool_1 = HoverTool(tooltips = [('date', '@date'), ('Impressiion', '@y')], mode='mouse')
hover_tool_2 = HoverTool(tooltips = [('date', '@date'), ('Engagement', '@y2')], mode='mouse')

# グラフ全体の設定
p1 = figure(tools=[hover_tool_1, hover_tool_2], title='インプレッション数とエンゲージメント数 (1ツイートあたり)  2020年10月～2021年9月',
            plot_width=1200, plot_height=400, x_axis_label='date', y_axis_label='Impression', x_axis_type='datetime',
           x_range = [x[0], x[-1]], y_range= [0, 100000], background_fill_color='Navy')

# X軸の設定
x_format = "%Y/%m"
p1.xaxis.formatter = DatetimeTickFormatter(months=[x_format], years=[x_format])

# 折れ線図
p1.vbar(x='x', top='y', legend_label='インプレッション数', source=source, color='Lime')
p1.vbar(x='x', top='y2', legend_label='エンゲージメント数', source=source, color='Magenta')

# 散布図
p1.asterisk('x', 'y', size=10, fill_alpha=0.5, source=source, color='Lime')
p1.asterisk('x', 'y2', size=10, fill_alpha=0.5, source=source, color='Magenta')


# 凡例の位置
p1.legend.location = 'top_left'

# rangetoolの作成
# rangetoolは、グラフの描画範囲をスライダーで変更することができます。
# rangetool用のグラフの設定を追加
select1 = figure(title="上段のグラフの表示範囲をスライダーで指定",
                plot_height=130, plot_width=1200, y_range= [0, 500000],
                x_axis_type="datetime", y_axis_type=None,
                tools="", toolbar_location=None, background_fill_color="#efefef")

# Rangetoolの設定
range_tool = RangeTool(x_range=p1.x_range) # Rangetoolのx_rangeの範囲を設定
range_tool.overlay.fill_color = "Navy"    # overlay.fill_colorはスライダーの色を指定
range_tool.overlay.fill_alpha = 0.2       # 透明度の指定

select1.line(x=x, y=y) # p.lineと同様にx軸とy軸の設定
select1.ygrid.grid_line_color = None
select1.add_tools(range_tool) # range_roolを追加
select1.toolbar.active_multi = range_tool


# 描画
#output_file('tweet_data.html')
fig6 = gridplot([[p1], [select1]])
show(fig6)

st.bokeh_chart(fig6)

# Twitterアナリティクスのツイートデータ(ツイート時刻ごと)(2020/10-2021/09)
st.write('Twitterアナリティクスのツイートデータ(ツイート時刻ごと)(2020/10-2021/09)')
time_df = tweets_df[["時刻", "ツイート本文", "インプレッション", "エンゲージメント", "ユーザープロフィールクリック"]]

st.dataframe(time_df, width=1000, height=200)

# 1パーセンタイル、99パーセンタイルを指定
q_min = time_df['インプレッション'].quantile(0.01) 
q_max = time_df['インプレッション'].quantile(0.99)

# 1パーセンタイル以下、99パーセンタイル以上の外れ値を除去
new_time_df = time_df.query('@q_min < インプレッション < @q_max')

# 時刻ごとのツイート数
df_count = new_time_df.groupby(["時刻"]).count()

# 時刻ごとの平均インプレッション数
df_mean = new_time_df.groupby(["時刻"]).mean()

st.write('Twitterアナリティクスのツイートデータ(時刻ごと平均)(2020/10-2021/09)')
st.dataframe(df_mean, width=1000, height=200)

# グラフ作成用の辞書
x = df_mean.index
y = df_mean['インプレッション'].astype(int)
y2 = df_mean['エンゲージメント'].astype(int)
y3 = df_mean['ユーザープロフィールクリック'].astype(int)
x4 = df_count.index
y4 = df_count['インプレッション']

source = ColumnDataSource(data = dict(x = x, x4=x4, y = y, y2=y2, y3=y3, y4=y4))

# tooltips設定
hover_tool_1 = HoverTool(tooltips = [('hour', '@x'), ('Impressiion', '@y')], mode='mouse')
hover_tool_2 = HoverTool(tooltips = [('hour', '@x'), ('Engagement', '@y2')], mode='mouse')
hover_tool_3 = HoverTool(tooltips = [('hour', '@x'), ('Profile Access', '@y3')], mode='mouse')
hover_tool_4 = HoverTool(tooltips = [('hour', '@x4'), ('Tweet', '@y4')], mode='mouse')

# グラフ全体の設定
p1 = figure(tools=[hover_tool_1], title='インプレッション数 (時刻ごと平均)  2020年10月～2021年9月 ※外れ値を処理',
            plot_width=800, plot_height=400, x_axis_label='hour', y_axis_label='Impression',
            background_fill_color='Navy')

p2 = figure(tools=[hover_tool_2], title='エンゲージメント数 (時刻ごと平均)  2020年10月～2021年9月 ※外れ値を処理',
            plot_width=800, plot_height=400, x_axis_label='hour', y_axis_label='Engagement',
            background_fill_color='Navy')

p3 = figure(tools=[hover_tool_3], title='プロフィールアクセス数 (時刻ごと平均)  2020年10月～2021年9月 ※外れ値を処理',
            plot_width=800, plot_height=400, x_axis_label='hour', y_axis_label='Profile Access',
            background_fill_color='Navy')

p4 = figure(tools=[hover_tool_4], title='ツイート数 (時刻ごと平均)  2020年10月～2021年9月 ※外れ値を処理',
            plot_width=800, plot_height=400, x_axis_label='hour', y_axis_label='Tweet',
            background_fill_color='Navy')


# 棒グラフ
p1.vbar(x='x', width=0.5, top='y', legend_label='インプレッション数(平均)', source=source, color='Lime')
p2.vbar(x='x', width=0.5, top='y2', legend_label='エンゲージメント数(平均)', source=source, color='Magenta')
p3.vbar(x='x', width=0.5, top='y3', legend_label='プロフィールアクセス数(平均)', source=source, color='OrangeRed')
p4.vbar(x='x4', width=0.5, top='y4', legend_label='ツイート数', source=source, color='AquaMarine')

# 凡例の位置
p1.legend.location = 'top_left'
p2.legend.location = 'top_left'
p3.legend.location = 'top_left'
p4.legend.location = 'top_left'

# 描画
#output_file('tweet_data.html')
fig7 = gridplot([[p1, p2], [p3, p4]])
show(fig7)

st.bokeh_chart(fig7)

