# _*_ coding:utf-8 _*_
# FileName: ys_history_analyze_gui.py
# IDE: PyCharm

import os
import ctypes
import tkinter.ttk
import configparser
from threading import Thread
from tkinter.messagebox import showinfo, showerror, askyesno
from ys_history_analyze_api import gacha_type, get_history_from_authkey, get_authkey_from_cookie, get_cookie_from_password


def write(self, fp, space_around_delimiters=True, section_annotate=None):
    # 添加 section 注释 - start
    assert not section_annotate or isinstance(section_annotate, dict), 'section_annotate 类型错误！'
    if not section_annotate:
        section_annotate = {'DEFAULT': '# 这是全局参数', 'GJJ': '; 这是用户参数', 'LJL': '; 这是用户参数'}
    # 添加 section 注释 - over
    if space_around_delimiters:
        d = " {} ".format(self._delimiters[0])
    else:
        d = self._delimiters[0]
    if self._defaults:
        if section_annotate and section_annotate.get(self.default_section, False):
            # 添加 section 注释
            self._write_section(fp, (self.default_section, section_annotate[self.default_section]), self._defaults.items(), d)
        else:
            self._write_section(fp, self.default_section, self._defaults.items(), d)
    for section in self._sections:
        if section_annotate and section_annotate.get(section, False):
            # 添加 section 注释
            self._write_section(fp, (section, section_annotate[section]), self._sections[section].items(), d)
        else:
            self._write_section(fp, section, self._sections[section].items(), d)


def _write_section(self, fp, section_name, section_items, delimiter):
    if isinstance(section_name, str):
        fp.write("[{}]\n".format(section_name))
    else:
        fp.write("[{}]\n{}\n".format(*section_name))  # 添加 section 注释
    for key, value in section_items:
        value = self._interpolation.before_write(self, section_name, key, value)
        if value is not None or not self._allow_no_value:
            value = delimiter + str(value).replace('\n', '\n\t')
        else:
            value = ""
        fp.write("{}{}\n".format(key, value))
    fp.write("\n")


# 重写写入函数
configparser.RawConfigParser.write = write
configparser.RawConfigParser._write_section = _write_section


class Settings:
    def __init__(self, user=None):
        self.user = ''
        self.__global_settings = ['predict_u', 'predict_p', 'headless', 'chrome_executable_path']
        self.__settings = {
            'uid': '',
            'cookie': '',
            'authkey': '',
            'username': '',
            'password': '',
            'predict_u': '',
            'predict_p': '',
            'chrome_executable_path': '',
            'headless': True
        }
        self.__config = configparser.RawConfigParser(allow_no_value=True)
        if not os.path.isdir('ys'):
            os.mkdir('ys')
        if os.path.isfile('yuanshen.ini'):
            try:
                self.__config.read('yuanshen.ini', encoding='utf-8')
                self.change_user(user=user)
                with open('yuanshen.ini', 'w', encoding='utf-8') as fp:
                    self.__config.write(fp=fp)
            except configparser.MissingSectionHeaderError:
                self.__config['DEFAULT'] = {setting: self.__settings[setting] for setting in self.__settings if setting in self.__global_settings}
                if self.user:
                    self.__config[self.user] = {setting: self.__settings[setting] for setting in self.__settings if setting not in self.__global_settings}
                with open('yuanshen.ini', 'w', encoding='utf-8') as fp:
                    self.__config.write(fp=fp)
        else:
            self.__config['DEFAULT'] = {setting: self.__settings[setting] for setting in self.__settings if setting in self.__global_settings}
            if self.user:
                self.__config[self.user] = {setting: self.__settings[setting] for setting in self.__settings if setting not in self.__global_settings}
            with open('yuanshen.ini', 'w', encoding='utf-8') as fp:
                self.__config.write(fp=fp)

    def change_user(self, user):
        if user:
            self.user = user
            if user not in self.__config.sections():
                self.__config.add_section(self.user)
            for setting in self.__settings:
                if setting in self.__global_settings:
                    try:
                        if setting == 'headless':
                            self.__settings['headless'] = self.__config['DEFAULT'].getboolean('headless')
                        else:
                            self.__settings[setting] = self.__config['DEFAULT'][setting]
                    except KeyError:
                        self.__config['DEFAULT'][setting] = self.__settings[setting]
                else:
                    try:
                        self.__settings[setting] = self.__config[self.user][setting]
                    except KeyError:
                        self.__config[self.user][setting] = self.__settings[setting]

    def users(self):
        return self.__config.sections()

    def load_from_tk_var(self, setting_dict):
        for setting in setting_dict:
            if setting == 'headless':
                self.__settings[setting] = setting_dict[setting].get()
            else:
                self.__settings[setting] = setting_dict[setting].get().strip()

    def save(self):
        self.__config['DEFAULT'] = {setting: self.__settings[setting] for setting in self.__settings if setting in self.__global_settings}
        self.__config[self.user] = {setting: self.__settings[setting] for setting in self.__settings if setting not in self.__global_settings}
        with open('yuanshen.ini', 'w', encoding='utf-8') as fp:
            self.__config.write(fp=fp)

    @property
    def settings(self):
        return self.__settings


class YuanShenHistoryGUI(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.width = 640
        self.height = 320
        self.thread_id = None
        self.settings = Settings()
        self.entry_dict = {setting: None for setting in self.settings.settings}
        self.values_dict = {setting: tkinter.StringVar(value=self.settings.settings[setting]) for setting in self.settings.settings}
        self.values_dict['headless'] = tkinter.BooleanVar(value=self.settings.settings['headless'])
        self.title('原神历史记录处理程序')
        self.top = tkinter.IntVar(value=1)
        self.artificial = tkinter.BooleanVar(value=False)
        self.log = tkinter.StringVar(value='等待完成设置...')
        self.tip = tkinter.Button(self, text='使用说明', command=lambda: showinfo(title='使用说明', message='可以使用uid+cookie/uid+authkey/uid+username+password三种组合\n'
                                                                                                    'predict_u和predict_p为tulingtech.xyz的账号密码，否则将进行手动识别\n'
                                                                                                    'chrome_executable_path为谷歌浏览器驱动chromedriver.exe文件位置\n'
                                                                                                    '通过米游社账号密码必须有谷歌浏览器和驱动，注意浏览器驱动版本\n'
                                                                                                    '所有下载下来的原神历史抽卡将保存在当前目录的 ys 下\n'
                                                                                                    '通过米游社账号密码登录会比较慢，请耐心等待\n'
                                                                                                    '如果使用uid+username+password方式长时间没有反应请清理或重启重试\n'
                                                                                                    '保持人工验证将完全无视自动验证的账号密码'))
        self.tip.grid(column=0, row=0, sticky=tkinter.NSEW)
        self.about = tkinter.Button(self, text='关于我', command=lambda: showinfo(title='关于我', message='作者：GJJ\n'
                                                                                                    '完成日期：2022年12月31日\n'
                                                                                                    '参考对象：yuanshenlink（逆向APK）'))
        self.about.grid(column=1, row=0, sticky=tkinter.NSEW)
        self.top_button = tkinter.Checkbutton(self, text='窗口置顶', offvalue=0, onvalue=1, variable=self.top, command=lambda: self.attributes('-topmost', self.top.get()))
        self.top_button.grid(column=2, row=0)
        self.top_button = tkinter.Checkbutton(self, text='保持人工验证', offvalue=False, onvalue=True, variable=self.artificial)
        self.top_button.grid(column=3, row=0)
        self.setting_frame = tkinter.LabelFrame(self, text='参数设置', borderwidth=4)
        self.setting_frame.grid(column=0, row=2, sticky=tkinter.NSEW, columnspan=2)
        tkinter.Label(self.setting_frame, text='账户', anchor=tkinter.NW).grid(column=0, row=0)
        self.setting_user = tkinter.ttk.Combobox(self.setting_frame, values=self.settings.users(), state='normal')
        self.setting_user.grid(column=1, row=0, sticky=tkinter.NSEW, columnspan=2)
        self.setting_user.bind('<<ComboboxSelected>>', self.change_user)
        if self.settings.users():
            self.setting_user.current(0)
            self.change_user(0)
        else:
            showinfo(title='注意', message='当前配置文件中无任何用户，在下拉框中输入名称，并填写相关输入框，保存参数即可写入文件！')
        for index, entry in enumerate(self.entry_dict):
            tkinter.Label(self.setting_frame, text=entry, anchor=tkinter.NW).grid(column=0, row=index + 1)
            if entry == 'headless':
                self.entry_dict[entry] = tkinter.Checkbutton(self.setting_frame, text='隐藏浏览器界面', offvalue=False, onvalue=True, variable=self.values_dict[entry])
            else:
                self.entry_dict[entry] = tkinter.Entry(self.setting_frame, textvariable=self.values_dict[entry])
            self.entry_dict[entry].grid(column=1, row=index + 1, sticky=tkinter.NSEW)
        self.save_button = tkinter.Button(self, text='保存参数', command=self.save)
        self.save_button.grid(column=0, row=3, sticky=tkinter.NSEW)
        self.start = tkinter.Button(self, text='开始爬取', command=self.start_)
        self.start.grid(column=1, row=3, sticky=tkinter.NSEW)
        self.log_frame = tkinter.LabelFrame(self, text='日志输出', borderwidth=4)
        self.log_frame.grid(column=2, row=1, sticky=tkinter.NSEW, rowspan=3, columnspan=2)
        self.log_label = tkinter.Label(self.log_frame, textvariable=self.log, anchor=tkinter.W)
        self.log_label.grid(column=0, row=0, sticky=tkinter.NSEW)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=3)
        self.columnconfigure(2, weight=2)
        self.columnconfigure(3, weight=2)
        self.setting_frame.columnconfigure(1, weight=1)
        self.attributes('-topmost', self.top.get())
        self.resizable(False, False)
        self.geometry(f'{self.width}x{self.height}+{int((self.winfo_screenwidth()-self.width-16)/2)}+{int((self.winfo_screenheight()-self.height-32)/2)}')
        self.protocol("WM_DELETE_WINDOW", lambda: self.destroy())
        self.mainloop()

    def change_user(self, *args):
        if args:
            self.settings.change_user(self.setting_user.get())
            for setting in self.settings.settings:
                self.values_dict[setting].set(self.settings.settings[setting])

    def save(self):
        self.settings.change_user(self.setting_user.get())
        self.settings.load_from_tk_var(self.values_dict)
        self.settings.save()
        showinfo(title='消息', message='参数设置成功！')

    def start_(self):
        self.thread_id = Thread(target=self.check_and_analyze, daemon=True)
        self.thread_id.start()

    def stop(self):
        if askyesno(title='警告', message='此操作将会强制关闭所有谷歌浏览器和浏览器驱动，是否继续'):
            os.system('taskkill /F /IM chromedriver.exe')
            os.system('taskkill /F /IM chrome.exe')
            self.label_text('所有谷歌浏览器和浏览器驱动已强制关闭！')
            self.start.configure(text='开始爬取', command=self.start_, state='normal')
            if self.thread_id:
                tid = ctypes.c_long(self.thread_id.ident)
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(SystemExit))
                if res != 1:
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
                    raise Exception('线程终止')
                elif res:
                    return
            else:
                raise Exception('线程终止')

    def label_text(self, text, no_enter=False):
        logs = self.log.get().split('\n')
        logs.extend(text.split('\n'))
        if len(logs) > 15:
            logs = logs[len(logs) - 15:]
        if no_enter:
            self.log.set('\n'.join(logs).replace(f'\n{text}', text))
        else:
            self.log.set('\n'.join(logs))

    def check_and_analyze(self):
        index = 0
        if self.settings.settings['uid'] and (self.settings.settings['authkey'] or self.settings.settings['cookie'] or (self.settings.settings['username'] and self.settings.settings['password'])):
            self.label_text(f"爬虫线程启动...【UID：{self.settings.settings['uid']}】")
        else:
            self.label_text('参数只能是：\nuid+cookie\nuid+authkey\nuid+username+password\n三种组合中的一种！')
            showerror(title='异常', message='参数只能是\nuid+cookie\nuid+authkey\nuid+username+password\n三种组合中的一种！')
        self.start.configure(state='disabled')
        self.save_button.configure(state='disabled')
        self.setting_user.configure(state='disabled')
        if self.settings.settings['uid'] and self.settings.settings['authkey']:
            self.label_text('已选择 uid+authkey 方式')
            for type_ in gacha_type:
                self.label_text(f'{type_[:6]}：')
                res = get_history_from_authkey(authkey=self.settings.settings['authkey'], uid=self.settings.settings['uid'], type_=type_)
                if res['code']:
                    self.label_text(res['msg'], no_enter=True)
                else:
                    self.label_text(f'抽卡 {len(res["data"])} 次', no_enter=True)
                    index += len(res["data"])
            if index > 0:
                self.setting_user.configure(state='normal')
                self.save_button.configure(state='normal')
                self.label_text(f'总计抽卡 {index} 次')
                self.start.configure(state='normal')
                self.label_text('爬虫结束')
                return
        if self.settings.settings['uid'] and self.settings.settings['cookie']:
            self.label_text('已选择 uid+cookie 方式')
            res = get_authkey_from_cookie(cookie_dict=self.settings.settings['cookie'], uid=self.settings.settings['uid'])
            if res['code']:
                self.label_text(res['msg'])
            else:
                authkey = res["data"]
                self.settings.settings['authkey'] = authkey
                self.values_dict['authkey'].set(authkey)
                self.settings.save()
                for type_ in gacha_type:
                    self.label_text(f'{type_[:6]}：')
                    res = get_history_from_authkey(authkey=authkey, uid=self.settings.settings['uid'], type_=type_)
                    if res['code']:
                        self.label_text(res['msg'], no_enter=True)
                    else:
                        self.label_text(f'抽卡 {len(res["data"])} 次', no_enter=True)
                        index += len(res["data"])
                if index > 0:
                    self.setting_user.configure(state='normal')
                    self.save_button.configure(state='normal')
                    self.label_text(f'总计抽卡 {index} 次')
                    self.start.configure(state='normal')
                    self.label_text('爬虫结束')
                    return
        if self.settings.settings['uid'] and self.settings.settings['username'] and self.settings.settings['password']:
            self.label_text('已选择 uid+username+password 方式')
            self.start.configure(text='强制关闭浏览器', command=self.stop, state='normal')
            if self.artificial.get():
                res = get_cookie_from_password(**{k: v for k, v in self.settings.settings.items() if k not in ['uid', 'cookie', 'authkey', 'predict_u', 'predict_p']}, master=self)
            else:
                res = get_cookie_from_password(**{k: v for k, v in self.settings.settings.items() if k not in ['uid', 'cookie', 'authkey']}, master=self)
            self.start.configure(text='开始爬取', command=self.start_, state='disabled')
            if res['code']:
                self.label_text(res['msg'])
                self.start.configure(state='normal')
                self.save_button.configure(state='normal')
                self.setting_user.configure(state='normal')
                return
            else:
                cookie_dict = res["data"]
                self.settings.settings['cookie'] = ' ;'.join([f'{k}={v}' for k, v in cookie_dict.items()])
                self.values_dict['cookie'].set(self.settings.settings['cookie'])
                self.settings.save()
                res = get_authkey_from_cookie(cookie_dict=cookie_dict, uid=self.settings.settings['uid'])
                if res['code']:
                    self.label_text(res['msg'])
                    self.start.configure(state='normal')
                    self.save_button.configure(state='normal')
                    self.setting_user.configure(state='normal')
                    return
                else:
                    authkey = res["data"]
                    self.settings.settings['authkey'] = authkey
                    self.values_dict['authkey'].set(authkey)
                    self.settings.save()
                    for type_ in gacha_type:
                        self.label_text(f'{type_[:6]}：')
                        res = get_history_from_authkey(authkey=authkey, uid=self.settings.settings['uid'], type_=type_)
                        if res['code']:
                            self.label_text(res['msg'], no_enter=True)
                        else:
                            self.label_text(f'抽卡 {len(res["data"])} 次', no_enter=True)
                            index += len(res["data"])
                    if index > 0:
                        self.setting_user.configure(state='normal')
                        self.save_button.configure(state='normal')
                        self.label_text(f'总计抽卡 {index} 次')
                        self.start.configure(state='normal')
                        self.label_text('爬虫结束')
                        return
        self.label_text('爬虫结束')
        self.start.configure(state='normal')
        self.save_button.configure(state='normal')
        self.setting_user.configure(state='normal')


if __name__ == '__main__':
    g = YuanShenHistoryGUI()