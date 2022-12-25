# _*_ coding:utf-8 _*_
# FileName: ys_history_analyze_api.py
# IDE: PyCharm

import os
import math
import json
import time
import base64
import random
import hashlib
import tkinter
import requests
from io import BytesIO
from urllib import parse
from PIL import Image, ImageTk
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

base = 'https://hk4e-api.mihoyo.com/event/gacha_info/api/getGachaLog'
gacha_type = {
    '新手许愿': '100',
    '常驻许愿': '200',
    '角色活动祈愿与角色活动祈愿-2': '301',
    '武器活动祈愿': '302'
}
headers = {
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json;charset=UTF-8',
    'Host': 'api-takumi.mihoyo.com',
    'x-rpc-app_version': '2.28.1',
    'x-rpc-client_type': '5',
    'x-rpc-device_id': 'CBEC8312-AA77-489E-AE8A-8D498DE24E90',
    'User_Agent': 'okhttp/4.10.0'
}


class ValidationGUI(tkinter.Toplevel):
    def __init__(self, url, master=None):
        super().__init__(master=master)
        self.data = {}
        self.live = True
        self.live = tkinter.BooleanVar(value=True)
        self.actions = {}
        self.title('验证码人工处理程序')
        self.nums = {1: '①', 2: '②', 3: '③', 4: '④', 5: '⑤', 6: '⑥', 7: '⑦', 8: '⑧', 9: '⑨'}
        self.img = Image.open(BytesIO(requests.get(url).content))
        self.img_tk = ImageTk.PhotoImage(self.img)
        self.canvas = tkinter.Canvas(self, width=self.img.size[0], height=self.img.size[1], bg='white')
        self.canvas.grid(column=0, row=0, sticky='WENS')
        self.canvas.create_image(self.img.size[0] / 2, self.img.size[1] / 2, image=self.img_tk)
        tkinter.Button(self, text='确认', command=self.exit).grid(column=0, row=1, sticky='WENS')
        self.geometry(f'{self.img.size[0]}x{self.img.size[1]+32}+750+450')
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.canvas.bind("<Button-1>", self.click)
        self.attributes('-topmost', True)
        self.resizable(False, False)

    def close(self):
        self.live = False
        self.destroy()

    def click(self, event):
        length = len(self.data)
        for index, site in self.data.items():
            x, y = site['X坐标值'], site['Y坐标值']
            if x - 10 < event.x < x + 10 and y - 10 < event.y < y + 10:
                for i in range(int(index[-1]), length + 1):
                    self.canvas.delete(*self.actions[f'顺序{i}'])
                    del self.data[f'顺序{i}'], self.actions[f'顺序{i}']
                break
        else:
            for i in range(1, 5):
                if f'顺序{i}' not in self.data:
                    self.data[f'顺序{i}'] = {'X坐标值': event.x, 'Y坐标值': event.y}
                    action1 = self.canvas.create_oval(event.x - 10, event.y - 10, event.x + 10, event.y + 10, fill='blue')
                    action2 = self.canvas.create_text(event.x, event.y, text=self.nums[i], font=('黑体', 18, 'bold'), fill='white')
                    self.actions[f'顺序{i}'] = (action1, action2)
                    break

    def exit(self):
        self.destroy()
        self.live = False


def get_history_from_file(uid: str, type_: str = '角色活动祈愿与角色活动祈愿-2'):
    if os.path.isfile(f'ys/{uid}_{gacha_type.get(type_, 301)}.json'):
        history = json.loads(open(f'ys/{uid}_{gacha_type.get(type_, 301)}.json', 'r', encoding='utf-8').read())
        return {'code': 0, 'msg': '', 'data': history}
    return {'code': -1, 'msg': '文件不存在！', 'data': None}


def get_history_from_authkey(authkey: str, uid: str, type_: str = '角色活动祈愿与角色活动祈愿-2'):
    params = {
        'init_type': '301',
        'size': '20',
        'authkey_ver': '1',
        'device_type': 'mobile',
        'page': '1',
        'lang': 'zh-cn',
        'plat_type': 'android',
        'gacha_type': gacha_type.get(type_, 301),
        'timestamp': '1648597985',
        'gacha_id': 'eaa07ae07196ca35c36b48213560ab6df7617e',
        'sign_type': '2',
        'game_biz': 'hk4e_cn',
        'region': 'cn_gf01',
        'end_id': '0',
        'auth_appid': 'webview_gacha',
        'authkey': parse.quote({k: v[0].replace(' ', '+') for k, v in parse.parse_qs(parse.urlsplit(authkey).query).items()}['authkey']) if authkey.strip().startswith('http') else authkey
    }
    url = base + '?' + '&'.join([f'{k}={v}' for k, v in params.items()])
    res = requests.get(url).json()
    if res['data'] and not res['retcode']:
        history = res['data']['list']
        if history:
            old = []
            ids = []
            uid = history[0]['uid']
            if os.path.exists(f'ys/{uid}_{gacha_type[type_]}.json'):
                old = json.loads(open(f'ys/{uid}_{gacha_type[type_]}.json', 'r', encoding='utf-8').read())
                ids = [o['id'] for o in old]
            while 1:
                params['page'] = str(int(params['page']) + 1)
                params['end_id'] = res['data']['list'][-1]['id']
                url = base + '?' + '&'.join([f'{k}={v}' for k, v in params.items()])
                res = requests.get(url).json()
                if res and res['data'] and res['data']['list']:
                    history += res['data']['list']
                    time.sleep(0.5)
                else:
                    break
            history = history[::-1]
            if old and ids:
                old_ = old[:]
                for h in history:
                    if h['id'] not in ids:
                        old.append(h)
                history = old
                if len(old_) != len(history):
                    open(f'ys/{uid}_{gacha_type[type_]}.json', 'w', encoding='utf-8').write(json.dumps(history, indent=4, ensure_ascii=False))
            return {'code': 0, 'msg': '', 'data': history}
        elif uid and os.path.exists(f'ys/{uid}_{gacha_type[type_]}.json'):
            return {'code': 0, 'msg': '', 'data': json.loads(open(f'ys/{uid}_{gacha_type[type_]}.json', 'r', encoding='utf-8').read())}
        else:
            return {'code': 1, 'msg': '最近180天无抽卡记录', 'data': None}
    return {'code': -1, 'msg': res['message'], 'data': None}


def get_authkey_from_cookie(cookie_dict: (str, dict), uid: str = None):
    if isinstance(cookie_dict, str):
        cookie_dict = dict([(i[0].strip(), i[1][0].strip()) for i in parse.parse_qs(cookie_dict).items()])
    if 'login_uid' in cookie_dict and 'login_ticket' in cookie_dict:
        t = int(time.time())
        cookie_dict.update({'stuid': cookie_dict["login_uid"]})
        tokens = requests.get(f'https://api-takumi.mihoyo.com/auth/api/getMultiTokenByLoginTicket?login_ticket={cookie_dict["login_ticket"]}&token_types=3&uid={cookie_dict["login_uid"]}', cookies=cookie_dict).json()['data']['list']
        user = requests.get('https://api-takumi.mihoyo.com/binding/api/getUserGameRolesByCookie?game_biz=hk4e_cn', cookies=cookie_dict).json()
        game_user = ([u for u in user['data']['list'] if u['game_uid'] == uid] or user['data']['list'])[0]
        cookie_dict.update({d['name']: d['token'] for d in tokens})
        data = {
            'auth_appid': 'webview_gacha',
            'game_biz': game_user['game_biz'],
            'game_uid': game_user['game_uid'],
            'region': game_user['region']
        }
        r = "".join(["ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"[int(math.floor(random.random() * float(0x30)))] for _ in range(6)])
        ds = hashlib.md5(f'salt=ulInCDohgEs557j0VsPDYnQaaz6KJcv5&t={t}&r={r}'.encode()).hexdigest()
        headers.update({'DS': f'{t}{chr(0x2c)}{r}{chr(0x2c)}{ds}'})
        authkey = requests.post(f'https://api-takumi.mihoyo.com/binding/api/genAuthKey', headers=headers, json=data, cookies=cookie_dict).json()
        return {'code': 0, 'msg': '', 'data': parse.quote(authkey['data']['authkey'])}
    return {'code': -1, 'msg': 'Cookie缺少必须参数“authkey”', 'data': None}


def get_cookie_from_password(username: str, password: str, predict_u: str = None, predict_p: str = None, chrome_executable_path: str = None, master=None):
    options = webdriver.ChromeOptions()
    options.headless = True
    if chrome_executable_path:
        driver = webdriver.Chrome(options=options, executable_path=chrome_executable_path)
    else:
        driver = webdriver.Chrome(options=options)
    driver.get('https://user.mihoyo.com/#/login/password')
    driver.set_page_load_timeout(3)
    for div, value in zip(driver.find_elements(by=By.CLASS_NAME, value='input-container'), (username, password)):
        div.find_element(by=By.TAG_NAME, value='input').send_keys(value)
    driver.find_element(by=By.CLASS_NAME, value='login-tip').find_element(by=By.TAG_NAME, value='div').click()
    time.sleep(0.5)
    driver.find_element(by=By.TAG_NAME, value='button').click()
    url = ''
    picture_id = None
    while not url:
        for request in driver.requests:
            if 'captcha_v3' in request.url:
                url = request.url
                break
        time.sleep(0.5)
    if predict_u and predict_p:
        data = {"username": predict_u, "password": predict_p, "ID": '44040235', "b64": base64.b64encode(requests.get(url).content).decode(), "version": "3.1.1", 'pictureID': 'need'}
        data = requests.post("http://www.tulingtech.xyz/tuling/predict", json=data).json()
        if data['code'] != 1:
            driver.close()
            return {'code': -1, 'msg': data['message'], 'data': None}
        picture_id = data['pictureID']
        data = data['data']
    else:
        validation = ValidationGUI(url=url, master=master)
        while validation.live:
            time.sleep(0.5)
        data = validation.data
        if '顺序4' not in data:
            driver.close()
            return {'code': -1, 'msg': '验证码自动操作错误，\n或用户名密码输入错误，\n请验证后重新发起请求！', 'data': None}
    element = driver.find_element(by=By.CLASS_NAME, value='geetest_big_item')
    to_element = ActionChains(driver=driver).move_to_element(element)
    to_element.move_by_offset(-150, -150).perform()
    for i in range(1, 5):
        to_element.move_by_offset(data[f'顺序{i}']['X坐标值'] / 343 * 300, data[f'顺序{i}']['Y坐标值'] / 343 * 300).click().perform()
        to_element.move_by_offset(-data[f'顺序{i}']['X坐标值'] / 343 * 300, -data[f'顺序{i}']['Y坐标值'] / 343 * 300).perform()
        time.sleep(0.5)
    driver.find_element(by=By.CLASS_NAME, value='geetest_commit_tip').click()
    time.sleep(1)
    for _ in range(5):
        if driver.current_url == 'https://user.mihoyo.com/#/account/home':
            cookie = driver.get_cookies()
            driver.close()
            cookie_dict = {}
            for c in cookie:
                cookie_dict[c['name']] = c['value']
            return {'code': 0, 'msg': '', 'data': cookie_dict}
        time.sleep(1)
    driver.close()
    if predict_u and predict_p:
        data = {"username": predict_u, "password": predict_p, 'pictureID': picture_id}
        requests.post("http://www.tulingtech.xyz/tuling/report_error", json=data)
    return {'code': -1, 'msg': '验证码自动操作错误，\n或用户名密码输入错误，\n请验证后重新发起请求！', 'data': None}