# _*_ coding:utf-8 _*_
# FileName: ys_history_analyze_gui.py
# IDE: PyCharm

import os
# import json
import tkinter
import configparser
from threading import Thread
from tkinter.messagebox import showinfo, showerror
from ys_history_analyze_api import gacha_type, get_history_from_authkey, get_authkey_from_cookie, get_cookie_from_password


class Settings:
    def __init__(self):
        self.__settings = {
            'uid': '',
            'cookie': '',
            'authkey': '',
            'username': '',
            'password': '',
            'predict_u': '',
            'predict_p': '',
            'chrome_executable_path': ''
        }
        self.__config = configparser.ConfigParser()
        if not os.path.isdir('ys'):
            os.mkdir('ys')
        if os.path.isfile('yuanshen.ini'):
            try:
                self.__config.read('yuanshen.ini', encoding='utf-8')
                if tuple(self.__settings) != tuple(self.__config['DEFAULT']):
                    for setting in self.__settings:
                        try:
                            self.__settings[setting] = self.__config['DEFAULT'][setting]
                        except KeyError:
                            self.__config['DEFAULT'][setting] = ''
                    with open('yuanshen.ini', 'w', encoding='utf-8') as fp:
                        self.__config.write(fp=fp)
                else:
                    self.__settings = dict(self.__config['DEFAULT'])
            except configparser.MissingSectionHeaderError:
                self.__config['DEFAULT'] = self.__settings
                with open('yuanshen.ini', 'w', encoding='utf-8') as fp:
                    self.__config.write(fp=fp)
        else:
            self.__config['DEFAULT'] = self.__settings
            with open('yuanshen.ini', 'w', encoding='utf-8') as fp:
                self.__config.write(fp=fp)

    def load_from_tk_var(self, setting_dict):
        for setting in setting_dict:
            self.__settings[setting] = setting_dict[setting].get()

    def save(self):
        self.__config['DEFAULT'] = self.__settings
        with open('yuanshen.ini', 'w', encoding='utf-8') as fp:
            self.__config.write(fp=fp)

    @property
    def settings(self):
        return self.__settings


class YuanShenHistoryGUI(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.width = 600
        self.height = 300
        self.settings = Settings()
        self.entry_dict = {setting: None for setting in self.settings.settings}
        self.values_dict = {setting: tkinter.StringVar(value=self.settings.settings[setting]) for setting in self.settings.settings}
        self.title('原神历史记录处理程序')
        self.top = tkinter.IntVar(value=1)
        self.log = tkinter.StringVar(value='等待完成设置...')
        self.tip = tkinter.Button(self, text='使用说明', command=lambda: showinfo(title='使用说明', message='可以使用uid+cookie/uid+authkey/uid+username+password三种组合\n'
                                                                                                    'predict_u和predict_p为tulingtech.xyz的账号密码，否则将进行手动识别\n'
                                                                                                    'chrome_executable_path为谷歌浏览器驱动chromedriver.exe文件位置\n'
                                                                                                    '通过米游社账号密码必须有谷歌浏览器和驱动，注意浏览器驱动版本\n'
                                                                                                    '所有下载下来的原神历史抽卡将保存在当前目录的 ys 下\n'
                                                                                                    '通过米游社账号密码登录会比较慢，请耐心等待'))
        self.tip.grid(column=0, row=0, sticky=tkinter.NSEW)
        self.about = tkinter.Button(self, text='关于我', command=lambda: showinfo(title='关于我', message='作者：GJJ\n'
                                                                                                    '完成日期：2022年12月23日\n'
                                                                                                    '参考对象：yuanshenlink（逆向APK）'))
        self.about.grid(column=1, row=0, sticky=tkinter.NSEW)
        self.top_button = tkinter.Checkbutton(self, text='窗口置顶', offvalue=0, onvalue=1, variable=self.top, command=lambda: self.attributes('-topmost', self.top.get()))
        self.top_button.grid(column=2, row=0)
        self.setting_frame = tkinter.LabelFrame(self, text='参数设置', borderwidth=4)
        self.setting_frame.grid(column=0, row=1, sticky=tkinter.NSEW, columnspan=2)
        for index, entry in enumerate(self.entry_dict):
            tkinter.Label(self.setting_frame, text=entry, anchor=tkinter.NW).grid(column=0, row=index)
            self.entry_dict[entry] = tkinter.Entry(self.setting_frame, textvariable=self.values_dict[entry])
            self.entry_dict[entry].grid(column=1, row=index, sticky=tkinter.NSEW)
        self.save_button = tkinter.Button(self, text='保存参数', command=self.save)
        self.save_button.grid(column=0, row=2, sticky=tkinter.NSEW)
        self.start = tkinter.Button(self, text='开始爬取', command=lambda: Thread(target=self.check_and_analyze, daemon=True).start())
        self.start.grid(column=1, row=2, sticky=tkinter.NSEW)
        self.log_frame = tkinter.LabelFrame(self, text='日志输出', borderwidth=4)
        self.log_frame.grid(column=2, row=1, sticky=tkinter.NSEW, rowspan=2)
        self.log_label = tkinter.Label(self.log_frame, textvariable=self.log, anchor=tkinter.NW)
        self.log_label.grid(column=0, row=0, sticky=tkinter.NSEW)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=3)
        self.columnconfigure(2, weight=4)
        self.setting_frame.columnconfigure(1, weight=1)
        self.attributes('-topmost', self.top.get())
        self.resizable(False, False)
        self.geometry(f'{self.width}x{self.height}+{int((self.winfo_screenwidth()-self.width-16)/2)}+{int((self.winfo_screenheight()-self.height-32)/2)}')
        self.protocol("WM_DELETE_WINDOW", lambda: self.destroy())
        self.mainloop()

    def save(self):
        self.settings.load_from_tk_var(self.values_dict)
        self.settings.save()
        self.log.set('参数设置成功！')

    def check_and_analyze(self):
        index = 0
        self.log.set('爬虫线程启动...')
        if self.settings.settings['uid'] and self.settings.settings['authkey']:
            self.log.set(self.log.get() + '\n已选择 uid+cookie 方式')
            for type_ in gacha_type:
                self.log.set(self.log.get() + f'\n{type_}：')
                res = get_history_from_authkey(authkey=self.settings.settings['authkey'], uid=self.settings.settings['uid'], type_=type_)
                if res['code']:
                    self.log.set(self.log.get() + res['msg'])
                    # showerror(title='异常', message=res['msg'])
                else:
                    # open(f"ys/{self.settings.settings['uid']}_{gacha_type[type_]}.json", 'w', encoding='utf-8').write(json.dumps(res["data"], indent=4, ensure_ascii=False))
                    self.log.set(self.log.get() + f'抽卡 {len(res["data"])} 次')
                    index += len(res["data"])
            self.log.set(self.log.get() + f'\n总计抽卡 {index} 次')
        elif self.settings.settings['uid'] and self.settings.settings['cookie']:
            self.log.set(self.log.get() + '\n已选择 uid+authkey 方式')
            res = get_authkey_from_cookie(cookie_dict=self.settings.settings['cookie'], uid=self.settings.settings['uid'])
            if res['code']:
                self.log.set(self.log.get() + f"\n{res['msg']}")
                showerror(title='异常', message=res['msg'])
            else:
                authkey = res["data"]
                for type_ in gacha_type:
                    self.log.set(self.log.get() + f'\n{type_}：')
                    res = get_history_from_authkey(authkey=authkey, uid=self.settings.settings['uid'], type_=type_)
                    if res['code']:
                        self.log.set(self.log.get() + res['msg'])
                        # showerror(title='异常', message=res['msg'])
                    else:
                        # open(f"ys/{self.settings.settings['uid']}_{gacha_type[type_]}.json", 'w', encoding='utf-8').write(json.dumps(res["data"], indent=4, ensure_ascii=False))
                        self.log.set(self.log.get() + f'抽卡 {len(res["data"])} 次')
                        index += len(res["data"])
                self.log.set(self.log.get() + f'\n总计抽卡 {index} 次')
        elif self.settings.settings['uid'] and self.settings.settings['username'] and self.settings.settings['password']:
            self.log.set(self.log.get() + '\n已选择 uid+username+password 方式')
            res = get_cookie_from_password(username=self.settings.settings['username'], password=self.settings.settings['password'],
                                           predict_u=self.settings.settings['predict_u'], predict_p=self.settings.settings['predict_p'],
                                           chrome_executable_path=self.settings.settings['chrome_executable_path'], master=self)
            if res['code']:
                self.log.set(self.log.get() + f"\n{res['msg']}")
                showerror(title='异常', message=res['msg'])
            else:
                cookie_dict = res["data"]
                res = get_authkey_from_cookie(cookie_dict=cookie_dict, uid=self.settings.settings['uid'])
                if res['code']:
                    self.log.set(self.log.get() + f"\n{res['msg']}")
                    showerror(title='异常', message=res['msg'])
                else:
                    authkey = res["data"]
                    for type_ in gacha_type:
                        self.log.set(self.log.get() + f'\n{type_}：')
                        res = get_history_from_authkey(authkey=authkey, uid=self.settings.settings['uid'], type_=type_)
                        if res['code']:
                            self.log.set(self.log.get() + res['msg'])
                            # showerror(title='异常', message=res['msg'])
                        else:
                            # open(f"ys/{self.settings.settings['uid']}_{gacha_type[type_]}.json", 'w', encoding='utf-8').write(json.dumps(res["data"], indent=4, ensure_ascii=False))
                            self.log.set(self.log.get() + f'抽卡 {len(res["data"])} 次')
                            index += len(res["data"])
                    self.log.set(self.log.get() + f'\n总计抽卡 {index} 次')
        else:
            self.log.set(self.log.get() + '\n参数只能是：\nuid+cookie\nuid+authkey\nuid+username+password\n三种组合中的一种！')
            showerror(title='异常', message='参数只能是\nuid+cookie\nuid+authkey\nuid+username+password\n三种组合中的一种！')
        self.log.set(self.log.get() + '\n爬虫结束。')


if __name__ == '__main__':
    g = YuanShenHistoryGUI()