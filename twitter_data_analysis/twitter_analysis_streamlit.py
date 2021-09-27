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
from bokeh.models import DataSource, RangeTool, HoverTool, DatetimeTickFormatter
import bokeh.palettes as bp
from datetime import datetime, timedelta
import os

# 現在時刻
now_time = datetime.now() + timedelta(hours=9)

# tツイートごとAPIデータへのファイルのパス
FILE_PATH_1 = st.secrets['file_path']

st.title('Twitterデータ分析')

# クリアをチェックするとキャッシュをクリア
st.write('最新データに更新したい場合は「clear」をチェック。更新後はチェックを外してください。')
if st.checkbox('clear'):
    caching.clear_cache()


# csvファイルをpandasで読み取り
@st.cache
def load_data():
    df = pd.read_csv(FILE_PATH_1)
    df['save_time'] = pd.to_datetime(df['save_time'])
    df['created_at'] = pd.to_datetime(df['created_at'])
    return df

# データ読取実行
data_load_state = st.text('Loading data...')
df = load_data()
data_load_state.text('Loading data...Done!')

st.write('ツイートごとのデータ (2017/4～最新更新)')

st.dataframe(df.sort_index(ascending=False), width=1000, height=200)

# 保存時間でグループ分け
df_save_time = df.groupby('save_time').mean()

# フォロワー数グラフを表示
figure1 = plt.figure()
plt.title('Followers Count')
plt.plot(df_save_time.index, df_save_time['followers'], color='green', label='followers', marker='o', lw=2)
plt.gcf().autofmt_xdate() 
plt.legend()
plt.show()

st.pyplot(figure1)


# フォロワー数グラフ作成用の辞書
x = df_save_time.index
y = df_save_time['followers']
date = x.strftime('%Y-%m-%d %H:%M:%S')
source = ColumnDataSource(data = dict(x = x, y = y, date=date))

# tooltips設定
hover_tool = HoverTool(tooltips = [('date and time', '@date'), ('followers', '@y')], mode='mouse')

# グラフ全体の設定
fig1 = figure(tools=[hover_tool], title='最新フォロワー数 (「サタデーステーション」公式Twitter)', plot_width=800, plot_height=400, 
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

firure2 = plt.figure(figsize=(20, 10))
plt.title('Reactions of Tweets')
plt.plot(df_created_at.index, df_created_at['favorited'], color='blue', label='favorited')
plt.plot(df_created_at.index, df_created_at['retweeted'], color='red', label='retweeted')
plt.gcf().autofmt_xdate() 
plt.legend()
plt.show()

st.pyplot(firure2)


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
p.star('x', 'y', size=10, fill_alpha=0.5, source=source, color='yellow')

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

firure3 = plt.figure(figsize=(20, 10))
plt.title('Tweet Engagement Data(averege)  by Hour')
plt.bar(df_hour.index, df_hour['favorited'], color='blue', label='favorited')
plt.bar(df_hour.index, df_hour['retweeted'], color='red', label='retweeted')
plt.legend()
plt.show()

st.pyplot(firure3)

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

st.bokeh_chart(fig3, use_container_width=True)

st.write('いいね数の平均', df_created_at['favorited'].mean()) 
st.write('いいね数の中央値', df_created_at['favorited'].median())
st.write('リツイート数の平均', df_created_at['retweeted'].mean()) 
st.write('リツイート数の中央値', df_created_at['retweeted'].median())
