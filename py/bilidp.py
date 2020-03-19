import requests
import json
import threading
import time
import datetime
import os
import browsercookie
import webbrowser


myuid = '4273707'  # b站id
cj = browsercookie.firefox()  # 获取浏览器cookie
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'}
result_path = 'result/result.json'
json_path = 'result/follow.json'
html_path = 'result/'
follow_list = []
follow_tags = []
videos = []
result = []
progress = 0

html_format = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{0}</title>
</head>
<body>
{1}
</body>
</html>'''

table_format = '''
<table border="1">
<thead>
<tr>
{0}
</tr>
</thead>
<tbody>
{1}
</tbody>
</table>
'''

table_head = '''
<th style="width:290px;height:40px;background:#EFF0DC">cover</th>
<th style="width:102px;height:40px;background:#EFF0DC">av</th>
<th style="height:40px;background:#EFF0DC">title</th>
<th style="width:131px;height:40px;background:#EFF0DC">uhead</th>
<th style="width:150px;height:40px;background:#EFF0DC">uname</th>
<th style="width:120px;height:40px;background:#EFF0DC">type</th>
<th style="width:200px;height:40px;background:#EFF0DC">ctime</th>
<th style="width:200px;height:40px;background:#EFF0DC">time</th>
'''

table_body_line = '''
<tr>
    <td style="align:center">
        <a href="https://www.bilibili.com/video/av{1}" target="_blank"><img src="{0}" style="width:288px;height:180px;"></a>
    </td>
    <td style="text-align:center">
        <a href="https://www.bilibili.com/video/av{1}" target="_blank"> av{1} </a>
    </td>
    <td>
        {2}
    </td>
    <td>
        <a href="https://space.bilibili.com/{3}" target="_blank"><img src="{4}" style="width:130px;height:130px;"></a>
    </td>
    <td>
        <a href="https://space.bilibili.com/{3}" target="_blank"> {5} </a>
    </td>
    <td style="text-align:center">
        {6}
    </td>
    <td style="text-align:center">
        {8}
    </td>
    <td style="text-align:center">
        {7}
    </td>
</tr>
'''

dynamic_head_url = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_new?uid={0}&type_list=8"
dynamic_url = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_history?uid={0}&offset_dynamic_id={1}&type=8"
follow_tags_url = "https://api.bilibili.com/x/relation/tags?jsonp=jsonp"
follow_via_tag_url = "https://api.bilibili.com/x/relation/tag?mid={0}&tagid={1}&pn={2}&ps=50&jsonp=jsonp"


def getdaytimestamp(count=0):  # 获得今天0点的时间戳
    if count < 0:
        return time.time()
    today = datetime.date.today()
    today_time = int(time.mktime(today.timetuple()))
    return today_time-count*86400


def getjsonob(url, cookies=cj, headers=headers):  # 获取json解析对象
    res_t = requests.get(url, headers=headers, cookies=cookies).text
    res = json.loads(res_t)
    return res


def getfollowtags(myuid=myuid, cookies=cj):  # 获取关注列表与分组
    global follow_tags, follow_tags_url
    tempurl = follow_tags_url
    res = getjsonob(tempurl)
    follow_tags += res['data']


def getfollowviatags(myuid=myuid, cookies=cj):  # 通过tag获取关注列表
    global follow_tags, follow_via_tag_url
    for i in follow_tags:
        pn_max = i['count'] // 50 + 1
        fid = []
        for ii in range(1, pn_max + 1):
            tempurl = follow_via_tag_url.format(
                myuid, str(i['tagid']), str(ii))
            res = getjsonob(tempurl)
            fid += [fo['mid'] for fo in res['data']]
        i['list'] = fid
        i['videos'] = []


def getdynamic(min_timestamp=getdaytimestamp(), max_timestamp=getdaytimestamp(-1), myuid=myuid, cookies=cj):  # 获取动态
    global follow_list, dynamic_head_url, dynamic_url, follow_tags, videos, progress
    nowtime = getdaytimestamp(-1)
    progress = 0
    record_timestamp = time.time()
    error_count = 0
    temp_error_count = 0
    visit_count = 1
    tempurl = dynamic_head_url.format(myuid)
    res1 = getjsonob(tempurl)
    offset = str(res1['data']['history_offset'])
    follow_list = res1['data']['attentions']['uids']
    tempav = ""
    count = 0
    print('1\n'+tempurl+'\n')
    cards_list1 = res1['data']['cards']
    for i in cards_list1:
        if i['desc']['timestamp'] < min_timestamp:
            follow_tags += [{'tagid': -100, 'name': '全部关注',
                             'count': len(follow_list), 'list': follow_list, 'videos': videos}]
            print('Final_Time: '+time.strftime("%Y-%m-%d %H:%M:%S",
                                               time.localtime(record_timestamp)))
            return
        record_timestamp = i['desc']['timestamp']
        progress = (nowtime-record_timestamp) / \
            (nowtime - min_timestamp) * 89+10
        if i['desc']['timestamp'] <= max_timestamp:
            card_res1 = json.loads(i['card'])
            tempav1 = str(card_res1['aid'])
            if tempav1 != tempav:
                count += 1
                temp_dict = {}
                temp_dict['av'] = card_res1['aid']
                temp_dict['type'] = card_res1['tname']
                temp_dict['title'] = card_res1['title']
                temp_dict['time'] = i['desc']['timestamp']
                temp_dict['ctime'] = card_res1['ctime']
                temp_dict['length'] = card_res1['duration']
                temp_dict['p_num'] = card_res1['videos']
                temp_dict['cover_url'] = card_res1['pic']
                temp_user = {}
                temp_user['uid'] = card_res1['owner']['mid']
                temp_user['uname'] = card_res1['owner']['name']
                temp_user['face_url'] = card_res1['owner']['face']
                temp_dict['up'] = temp_user
                temp_stat = {}
                temp_stat['view'] = card_res1['stat']['view']
                temp_stat['danmuku'] = card_res1['stat']['danmaku']
                temp_stat['favorite'] = card_res1['stat']['favorite']
                temp_stat['coin'] = card_res1['stat']['coin']
                temp_stat['like'] = card_res1['stat']['like']
                temp_stat['reply'] = card_res1['stat']['reply']
                temp_stat['share'] = card_res1['stat']['share']
                temp_dict['stat'] = temp_stat
                videos += [temp_dict]
                for ii in range(len(follow_tags)):
                    if temp_dict['up']['uid'] in follow_tags[ii]['list']:
                        follow_tags[ii]['videos'] += [temp_dict]
            tempav = str(card_res1['aid'])
    tempav = ""
    while True:
        visit_count += 1
        print(str(visit_count)+'\t\t'+offset+'\t\t'+time.strftime("%Y-%m-%d %H:%M:%S",
                                                                  time.localtime(record_timestamp)))
        tempurl = dynamic_url.format(myuid, offset)
        print(tempurl+'\n')
        res = getjsonob(tempurl)
        if 'next_offset' in res['data'].keys():
            temp_error_count = 0
            offset = str(res['data']['next_offset'])
        else:
            error_count += 1
            temp_error_count += 1
            print('ERROR')
            if(temp_error_count < 10):
                continue
            else:
                follow_tags += [{'tagid': -100, 'name': '全部关注',
                                 'count': len(follow_list), 'list': follow_list, 'videos': videos}]
                print('Error_Count : '+str(error_count)+'\nFinal_Time : '+time.strftime("%Y-%m-%d %H:%M:%S",
                                                                                        time.localtime(record_timestamp))+'\n\nThe mission FAILed, but having got PART of the RESULT.')
                return
        cards_list = res['data']['cards']
        for i in cards_list:
            if i['desc']['timestamp'] < min_timestamp:
                follow_tags += [{'tagid': -100, 'name': '全部关注',
                                 'count': len(follow_list), 'list': follow_list, 'videos': videos}]
                print('Error_Count : '+str(error_count) + '\nFinal_Time : ' +
                      time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record_timestamp)))
                return
            record_timestamp = i['desc']['timestamp']
            progress = (nowtime-record_timestamp) / \
                (nowtime - min_timestamp) * 89+10
            if i['desc']['timestamp'] <= max_timestamp:
                card_res = json.loads(i['card'])
                tempav1 = str(card_res['aid'])
                if tempav1 != tempav:
                    count += 1
                    temp_dict = {}
                    temp_dict['av'] = card_res['aid']
                    temp_dict['type'] = card_res['tname']
                    temp_dict['title'] = card_res['title']
                    temp_dict['time'] = i['desc']['timestamp']
                    temp_dict['ctime'] = card_res['ctime']
                    temp_dict['length'] = card_res['duration']
                    temp_dict['p_num'] = card_res['videos']
                    temp_dict['cover_url'] = card_res['pic']
                    temp_user = {}
                    temp_user['uid'] = card_res['owner']['mid']
                    temp_user['uname'] = card_res['owner']['name']
                    temp_user['face_url'] = card_res['owner']['face']
                    temp_dict['up'] = temp_user
                    temp_stat = {}
                    temp_stat['view'] = card_res['stat']['view']
                    temp_stat['danmuku'] = card_res['stat']['danmaku']
                    temp_stat['favorite'] = card_res['stat']['favorite']
                    temp_stat['coin'] = card_res['stat']['coin']
                    temp_stat['like'] = card_res['stat']['like']
                    temp_stat['reply'] = card_res['stat']['reply']
                    temp_stat['share'] = card_res['stat']['share']
                    temp_dict['stat'] = temp_stat
                    videos += [temp_dict]
                    for ii in range(len(follow_tags)):
                        if temp_dict['up']['uid'] in follow_tags[ii]['list']:
                            follow_tags[ii]['videos'] += [temp_dict]
                tempav = str(card_res['aid'])


def updatefollowjson(json_path=json_path):  # 更新follow.json
    global follow_tags
    getfollowtags()
    getfollowviatags()
    fp = open(json_path, "w", encoding="UTF-8")
    fp.write(json.dumps(follow_tags, ensure_ascii=False))
    fp.close()


def readfollowjson(json_path=json_path):  # 读取follow.json
    global follow_tags
    fp = open(json_path, encoding='utf-8')
    follow_tags = json.load(fp)
    fp.close()


def writeresultjson(result_path=result_path):
    global follow_tags, progress  # 写入文件
    fp = open(result_path, "w", encoding="UTF-8")
    fp.write(json.dumps(follow_tags, ensure_ascii=False))
    fp.close()
    progress = 100


def dynamic(day1=0, day2=-1):  # 封装好的动态获取函数
    global json_path, progress
    progress = 0
    if not os.path.exists(json_path):
        updatefollowjson()
    else:
        readfollowjson()
    getdynamic(getdaytimestamp(day1), getdaytimestamp(day2))
    writeresultjson()


def readresult(result_path=result_path):  # 都结果json
    global result
    fp = open(result_path, encoding='utf-8')
    result = json.load(fp)
    fp.close()


def showresult():  # 简单显示result
    global result, html_format, table_format, table_head, table_body_line, html_path
    temp_str = ' '
    for i in result:
        fp = open(html_path+i['name'] + '.html', 'w', encoding='utf-8')
        temp_body = ''
        temp_body += '<h2>' + i['name'] + ':' + '</h2><br>'
        temp_table_body = ''
        for ii in i['videos']:
            temp_table_body += table_body_line.format(
                ii['cover_url'], str(ii['av']), ii['title'], str(ii['up']['uid']), ii['up']['face_url'], ii['up']['uname'], ii['type'], time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ii['time'])), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ii['ctime'])))
        temp_table = table_format.format(table_head, temp_table_body)
        temp_body += temp_table
        fp.write(html_format.format(i['name'], temp_body))
        fp.close()
        temp_str += '<a href='+html_path+i['name']+'.html >' + \
            i['name'] + '('+str(i['count']) + ')' + '</a> : ' + \
            str(len(i['videos'])) + '<br>\n'
    fp1 = open('index.html', 'w', encoding='utf-8')
    fp1.write(html_format.format('index', temp_str))
    fp1.close()
    webbrowser.open('index.html')


class ResultThread(threading.Thread):
    time1 = 0
    time2 = -1

    def __init__(self, threadID, name, counter, time1=0, time2=-1):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.time1 = time1
        self.time2 = time2

    def run(self):
        print("开始线程：" + self.name)
        dynamic(self.time1, self.time2)
        print("退出线程：" + self.name)


class FollowThread(threading.Thread):

    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def run(self):
        print("开始线程：" + self.name)
        updatefollowjson()
        print("退出线程：" + self.name)
