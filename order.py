#####################################################################################################################
## Part 1.相关依赖库

# 时间
import time
import datetime

# 导入json库
import json

# 随机数
import random

# 基础数据科学运算库
import pandas as pd
import numpy as np

# 可视化
import streamlit_echarts
from pyecharts.charts import Line
from pyecharts.charts import Pie
from pyecharts.charts import Bar
from pyecharts.charts import Scatter
from pyecharts import options as opts
from pyecharts.charts import Map, Geo
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType
from pyecharts.charts import Funnel
from pyecharts.charts import WordCloud  # 词云图
import streamlit.components.v1 as components  # 显示map

# streamlit
import streamlit as st

# 图片库
from PIL import Image

# jieba库
import jieba

# 统计
from collections import Counter

#####################################################################################################################
## Part 2.侧边栏

# 设置网页id和icon
st.set_page_config(page_title="Tmall订单数据", page_icon=":sunny:", layout="wide")


# 获取时间
def get_time():
    now_time = datetime.datetime.now()
    ymd = now_time.strftime('%Y-%m-%d')
    return ymd


# 显示当前日期
st.sidebar.header(f"当前日期：{get_time()}")

# bgm曲目功能
music = st.sidebar.radio('选择你喜欢的曲目', ['卡农', 'Summer'], index=random.choice(range(2)))
st.sidebar.write(f'正在播放 {music}... :musical_note:')


@st.cache
def get_audio_bytes(music):
    audio_file = open(f'weather-music/{music}.mp3', 'rb')
    audio_bytes = audio_file.read()
    audio_file.close()
    return audio_bytes


audio_bytes = get_audio_bytes(music)
st.sidebar.audio(audio_bytes, format='audio/mp3')

#####################################################################################################################
## Part 3.主界面

# 标题
st.title(":sunny: 小蒋带你看订单数据")
st.write('项目Github地址：https://github.com/jyw2000-jyw/OrderData-visualization-base-on-streamlit')
st.write('数据来源：天猫 https://www.tmall.com/')
st.write('时间跨度：2020-2-1至2020-2-29')
st.markdown("###")


#########################################################################
## Part 3.1 数据读取与清洗

# 读取订单数据
def get_data_from_csv():
    df = pd.read_csv('tmall_order_report.csv', encoding='utf')
    return df


df = get_data_from_csv()

# 将字段名称中空格去掉，规范字段名称 & 修改部分名称
df = df.rename(columns={'收货地址 ': '收货地址',
                        '订单付款时间 ': '订单付款时间',
                        '总金额': '订单金额',
                        '买家实际支付金额': '实付金额'})

# 修改type
df['订单创建时间'] = df['订单创建时间'].astype('datetime64')
df['订单付款时间'] = df['订单付款时间'].astype('datetime64')

# 根据日期，增加星期列
df['星期'] = df['订单创建时间'].dt.dayofweek + 1

# 创建字典
dict_convs = dict()

dict_convs['总订单数'] = len(df)

df_payed = df[df['订单付款时间'].notnull()]
dict_convs['付款订单数'] = len(df_payed)

df_trans = df_payed[df_payed['实付金额'] != 0]
dict_convs['到款订单数'] = len(df_trans)

df_trans_full = df_payed[df_payed['退款金额'] == 0]
dict_convs['全额到款订单数'] = len(df_trans_full)

df_convs = pd.Series(dict_convs, name='订单数').to_frame()

# 添加总体转化率,每个环节除以总订单数
total_convs = df_convs['订单数'] / df_convs.loc['总订单数', '订单数'] * 100
df_convs['总体转化率'] = total_convs.apply(lambda x: round(x, 0))

# 添加单一环节转化率,每个环节除以上一环节
single_convs = df_convs['订单数'].shift()
df_convs['单一环节转化率'] = single_convs.fillna(df_convs.loc['总订单数', '订单数'])
df_convs['单一环节转化率'] = round((df_convs['订单数'] / df_convs['单一环节转化率'] * 100), 0)

# 小时
hours = ['0a/12p', '1a', '2a', '3a', '4a', '5a', '6a', '7a', '8a', '9a', '10a', '11a',
         '12a/0p', '1p', '2p', '3p', '4p', '5p', '6p', '7p', '8p', '9p', '10p', '11p']
weeks = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

week_hour_group = df.groupby([df['星期'], df['订单创建时间'].dt.hour])['订单创建时间'].count().to_frame('数量')
count_values = list(week_hour_group['数量'].values)
allinfo = []
for idx, dt in enumerate(week_hour_group.index.to_list()):
    info = [dt[0], dt[1], count_values[idx]]
    allinfo.append(info)

# 地图
se_trans_map = df_trans.groupby('收货地址')['收货地址'].count().sort_values(ascending=False)


# 为了保持由于下面的地理分布图使用的省份名称一致，定义一个处理自治区的函数
def strip_region(iterable):
    result = []
    for i in iterable:
        if i.endswith('自治区'):
            if i == '内蒙古自治区':
                i = i[:3]
                result.append(i)
            else:
                result.append(i[:2])
        else:
            result.append(i)
    return result


# 处理自治区
se_trans_map.index = strip_region(se_trans_map.index)

# 去掉末位‘省’字
se_trans_map.index = se_trans_map.index.str.strip('省')


# 读取评论数据
def get_data_from_csv():
    data = pd.read_csv("earphone_sentiment.csv", encoding="gbk")
    return data


data = get_data_from_csv()

#########################################################################
## Part 3.2 栏目一

# 成交额
max_order = df['订单金额'].max()
min_order = df['订单金额'].min()
mean_order = round(df['订单金额'].mean(), 1)
rate = ((df['订单金额'].count() - len(df[df['实付金额'] == 0.0])) / df['订单金额'].count()) * 100

# 4列布局
col1, col2, col3, col4 = st.columns(4)

# 添加相关信息
with col1:
    st.subheader(f"{max_order}RMB")
    st.caption("最大成交额")
with col2:
    st.subheader(f"{min_order}RMB")
    st.caption("最小成交额")
with col3:
    st.subheader(f"{mean_order}RMB")
    st.caption("平均成交额")
with col4:
    st.subheader(f"{round(rate, 1)}%")
    st.caption("交易成功率")

st.markdown("""---""")  # 分隔符

#########################################################################
## Part 3.3 漏斗图

# 2列布局
col1, col2 = st.columns(2)

# 添加相关信息
with col1:
    # 总体转化率
    st.markdown(f'##### 总体转化率')
    st.text('每个环节除以总订单数')

    funnel = (
        Funnel()
        .add(series_name='总体转化率',
             data_pair=[list(z) for z in zip(df_convs.index, df_convs['总体转化率'])],
             is_selected=True,
             label_opts=opts.LabelOpts(position='inside'))
        .set_series_opts(tooltip_opts=opts.TooltipOpts(formatter='{a}<br/>{b}:{c}%'))
    )

    streamlit_echarts.st_pyecharts(funnel)

with col2:
    # 单一环节转化率
    st.markdown(f'##### 单一环节转化率')
    st.text('每个环节除以上一环节')

    funnel = (
        Funnel()
        .add(series_name='单一环节转化率',
             data_pair=[list(z) for z in zip(df_convs.index, df_convs['单一环节转化率'])],
             is_selected=True,
             label_opts=opts.LabelOpts(position='inside'))
        .set_series_opts(tooltip_opts=opts.TooltipOpts(formatter='{a}<br/>{b}:{c}%'))
    )

    streamlit_echarts.st_pyecharts(funnel)

st.markdown("""---""")  # 分隔符

#########################################################################
## Part 3.3 散点图

st.markdown(f'##### 一周每天各时段订单数量散点图')

single_axis, titles = [], []
scatter = Scatter(init_opts=opts.InitOpts(width='1000px',
                                          height='800px',
                                          theme='light',
                                          bg_color=''))
for idx, day in enumerate(weeks[::-1]):
    scatter.add_xaxis(xaxis_data=hours)
    # 单轴配置
    single_axis.append({'left': 100,
                        'nameGap': 20,
                        'nameLocation': 'start',
                        'type': 'category',
                        'boundaryGap': False,
                        'data': hours,
                        'top': '{}%'.format(idx * 100 / 7 + 5),
                        'height': '{}%'.format(100 / 7 - 10),
                        'gridIndex': idx,
                        'axisLabel': {'interval': 2, 'color': ''},
                        })
    titles.append(dict(text=day, top='{}%'.format(idx * 100 / 7 + 6), left='2%',
                       textStyle=dict(color='')))
    scatter.add_yaxis('',
                      y_axis=[int(item[2]) for item in allinfo if item[0] == 7 - idx],
                      symbol_size=JsCode('function(p) { return p[1] * 0.15;}'),
                      label_opts=opts.LabelOpts(is_show=False),
                      )
    scatter.options['series'][idx]['coordinateSystem'] = 'singleAxis'
    scatter.options['series'][idx]['singleAxisIndex'] = idx

# 多标题配置
scatter.options['singleAxis'] = single_axis
scatter.set_global_opts(
    xaxis_opts=opts.AxisOpts(is_show=False),
    yaxis_opts=opts.AxisOpts(is_show=False),
    title_opts=titles
)

streamlit_echarts.st_pyecharts(scatter, width="", height=500)

st.write('分析：周二至周五的成交订单较周一和周日的订单量要明显的多；一天中上午9点-12点和晚上8点-10点这两个时段的订单量较其他时段更多，尤其是晚上8点-10点时段。')

st.markdown("""---""")  # 分隔符

#########################################################################
## Part 3.4 饼图

week = df.groupby(df['星期'])['订单创建时间'].count()
week_group = week.to_dict()
week_groupList = list(zip(week_group.keys(), week_group.values()))

a = df_trans['实付金额'].to_list()
sections = [0, 50, 100, 300, 500, 1000, 5000, 20000]
group_names = ['0-50', '50-100', '100-300', '300-500', '500-1000', "1000-5000", "5000-20000"]
cuts = pd.cut(np.array(a), sections, labels=group_names)
counts = pd.value_counts(cuts)
priceDict = counts.to_dict()
priceList = list(zip(priceDict.keys(), priceDict.values()))

col1, col2 = st.columns(2)

with col1:
    st.markdown('##### 一周订单占比')

    pie = Pie(
        init_opts=opts.InitOpts(
            theme='white',
            width='1000px',
            height='500px'
        ))
    pie.add(
        "",
        week_groupList,
        radius=["30%", "50%"],
        # center=["25%", "50%"],
        # rosetype="area",
        label_opts=opts.LabelOpts(is_show=True, formatter='{b}:{d}%')
    )
    streamlit_echarts.st_pyecharts(pie)

with col2:
    st.markdown('##### 订单额度区间')

    bar = (
        Bar()
        .add_xaxis(list(priceDict.keys())
        )
        .add_yaxis("成交数",
                   list(priceDict.values())
        )
        .set_global_opts(toolbox_opts=opts.ToolboxOpts())
    )

    streamlit_echarts.st_pyecharts(bar)

st.write('分析：周二和周五的成交订单均接近5000单，占总订单量的35%左右；周一和周日大家的购物欲比较低，各有2500单左右，占总订单量的9%左右；单笔成交订单额度方面，大多数用户消费金额为1-300元内')

#########################################################################
## Part 3.4 折线图

st.markdown(f'##### 每日订单数折线图')

df_trans = df_trans.set_index('订单创建时间')
se_trans_month = df_trans.resample('D')['订单编号'].count()

name = '订单数'
line = (
    Line()
        .add_xaxis(xaxis_data=list(se_trans_month.index.day.map(str)))
        .add_yaxis(series_name=name,
                   y_axis=se_trans_month
                   )
        .set_global_opts(yaxis_opts=opts.AxisOpts(splitline_opts=opts.SplitLineOpts(is_show=True)))
)

streamlit_echarts.st_pyecharts(line, height=400)

st.write('分析：2月上半个月，企业多数未复工，快递停运，无法发货；下半个月，随着企业复工逐渐增多，订单数开始上涨')

st.markdown("""---""")  # 分隔符

#########################################################################
## Part 3.5 地图

# 地图
st.markdown(f'##### 订单全国地图分布')

# 地理分布图
name = '订单数'
map = (
    Map()
        .add(
        series_name=name,
        data_pair=[list(i) for i in se_trans_map.items()]
    )
        .set_global_opts(title_opts=opts.TitleOpts(title=""),
                         visualmap_opts=opts.VisualMapOpts(max_=max(se_trans_map) * 0.6))
        .render_embed()
)

# streamlit_echarts.st_pyecharts(c, map=map, height=500) 对于map此方法不可用
components.html(map, width=1500, height=550)  # 不设置长宽的话默认情况恐怕无法显示完全

st.markdown("""---""")  # 分隔符

#########################################################################
## Part 3.5 栏目四

# 对列表中每条评论数据进行处理，去掉停用词和符号
from string import punctuation

add_punc = '，。、【 】 “”：；（）《》‘’{}？！⑦()、%^>℃：.”“^-——=&#@￥'
stop_words = {'你', '我', '的', '了', '人', '都', '和', '在', '不', '比', '就', '但', '也', '是', '有', '吧', '很', '还', '啊', '个', '说',
              '会', '去', '用', '这', '就是', '但是', '还是', '还有', '不是', '现在', '的话', '觉得', '不过', '只是', '因为', '什么', '如果', '而且',
              '森林', '看看', '没有', '等', '没', '要', '那', '所以', '自己', '看过', '这个', '知道', '一个', '或者', '后', '吗', '看'}
stop = add_punc + punctuation + str(stop_words)
list = data["content"].tolist()
ls = []
for i in list:
    words = jieba.lcut(i)
    for s in words:
        if s.strip() in stop:
            pass
        else:
            ls.append(s.strip())

wordscount = Counter(ls).most_common(30)

col1, col2 = st.columns(2)

with col1:
    st.markdown('##### 评论词云图')

    wc = (WordCloud().add("", wordscount))

    streamlit_echarts.st_pyecharts(wc)

with col2:
    st.markdown('##### 评论等级')

    data['sentiment_value'].replace(1, "好评", inplace=True)
    data['sentiment_value'].replace(-1, "差评", inplace=True)
    data['sentiment_value'].replace(0, "未填写或中评", inplace=True)
    commentDict = data['sentiment_value'].value_counts().to_dict()

    commentRank = []
    commentCount = []
    for k, v in commentDict.items():
        commentRank.append(k)
        commentCount.append(v)

    bar = Bar()
    bar.add_xaxis(commentRank).add_yaxis("数量", commentCount).set_global_opts(toolbox_opts=opts.ToolboxOpts())

    streamlit_echarts.st_pyecharts(bar)

st.markdown("""---""")  # 分隔符


#########################################################################
## Part 3.6 栏目五

# 图片模块
@st.cache
def get_pictures(picture):
    picture_file = open(f'company/{picture}.png', 'rb')
    p = picture_file.read()
    picture_file.close()
    return p


pic1, pic2, pic3, pic4 = st.columns(4)

with pic1:
    st.markdown('##### 阿里巴巴')
    picture1 = get_pictures('阿里巴巴')
    st.image(picture1, caption='中国杭州')

with pic2:
    st.markdown('##### 腾讯')
    picture2 = get_pictures('腾讯')
    st.image(picture2, caption='中国深圳')

with pic3:
    st.markdown('##### 谷歌')
    picture3 = get_pictures('谷歌')
    st.image(picture3, caption='美国加州')

with pic4:
    st.markdown('##### 微软')
    picture4 = get_pictures('微软')
    st.image(picture4, caption='美国华盛顿州')

st.markdown("""---""")  # 分隔符

#########################################################################
## Part 3.7 栏目六

# 视频模块
st.markdown('##### 一些视频')


@st.cache
def get_video_bytes(video):
    video_file = open(f'commerce-video/{video}.mp4', 'rb')
    video_bytes = video_file.read()
    video_file.close()
    return video_bytes


v1, v2 = st.columns(2)  # 分两列

with v1:
    video1 = get_video_bytes('Digital')
    v1.video(video1, format='video/mp4')
    st.caption("数字社会")

with v2:
    video2 = get_video_bytes('GDP')
    v2.video(video2, format='video/mp4')
    st.caption("什么是GDP？")

#####################################################################################################################
## Part 4.其他

# 隐藏streamlit默认格式信息
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 好看的气球动画
st.balloons()
