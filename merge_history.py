# _*_ coding:utf-8 _*_
# FileName: merge_history.py
# IDE: PyCharm

def merge_history_to_gw(uid):
    ys_dir = 'ys'
    history = {'result': []}
    filename = f'gacha-list-{uid}.json'
    for gacha_type in ['301', '302', '200', '100']:
        file = f'{uid}_{gacha_type}.json'
        if os.path.isfile(f'{ys_dir}//{file}'):
            l = []
            h = json.load(open(f'{ys_dir}//{file}', 'r', encoding='utf-8'))
            for hh in h:
                hh['rank_type'] = int(hh['rank_type'])
                l.append([hh[t] for t in ['time', 'name', 'item_type', 'rank_type', 'gacha_type', 'id']])
            history['result'].append([file.split('.')[0].split('_')[-1], l])
    history.update({'time': int(time.time() * 1000), 'typeMap': [['301', '角色活动祈愿与角色活动祈愿-2'], ['302', '武器活动祈愿'], ['200', '常驻许愿'], ['100', '新手许愿']], 'uid': uid, 'lang': 'zh-cn'})
    open(filename, 'w', encoding='utf-8').write(json.dumps(history, indent=2, ensure_ascii=False))


def write_history_table(uid):
    filename = f'gacha-list-{uid}.json'
    if not os.path.isfile(filename):
        raise FileNotFoundError(f'uid {uid} 对应的文件不存在！')
    title = ['时间', '名称', '类别', '星级', '总次数', '保底内', '备注']
    data = json.loads(open(filename, 'r', encoding='utf-8').read())['result']
    app = xlwings.App(visible=True, add_book=False)
    book = app.books.add()
    for gacha_type, d in zip(['角色活动祈愿与角色活动祈愿-2', '武器活动祈愿', '常驻许愿', '新手许愿'], data):
        all_index = 1
        five_index = 1
        sheet = book.sheets.add(gacha_type)
        sheet.range('A2').select()
        app.api.ActiveWindow.FreezePanes = True
        title_range = sheet.range((1, 1), (1, 7))
        data_range = sheet.range((2, 1), (len(d[1]) + 1, 7))
        all_range = sheet.range((1, 1), (len(d[1]) + 1, 7))
        title_range.api.NumberFormat = '@'
        title_range.font.name = '微软雅黑'
        title_range.font.bold = True
        title_range.color = (219, 215, 211)
        title_range.font.color = (117, 117, 117)
        data_range.api.NumberFormat = '@'
        data_range.font.name = '微软雅黑'
        sheet.range('A:C').api.HorizontalAlignment = -4131
        sheet.range('D:G').api.HorizontalAlignment = -4152
        title_range.api.HorizontalAlignment = -4131
        all_range.api.VerticalAlignment = -4108
        data_range.color = (235, 235, 235)
        for border in range(7, 13):  # 左、上、下、右、内纵、内横
            bor = all_range.api.Borders(border)
            bor.Color = 1
            bor.Weight = 2
            bor.LineStyle = 1
        for n, (ti, width) in enumerate(zip(title, [23.38, 13.38, 7.38, 7.38, 7.38, 7.38, 7.38])):
            col = sheet.range(1, n + 1)
            col.column_width = width
            col.value = ti
        for r, dd in enumerate(d[1]):
            dd[4] = all_index
            dd[5] = five_index
            row_range = sheet.range((r + 2, 1), (r + 2, 7))
            row_range.select()
            if dd[3] == 3:
                row_range.font.color = (142, 142, 142)
            elif dd[3] == 4:
                row_range.font.color = (162, 86, 225)
                row_range.font.bold = True
            elif dd[3] == 5:
                row_range.font.color = (189, 105, 50)
                row_range.font.bold = True
            row_range.value = dd
            all_index += 1
            five_index += 1
            if dd[3] == 5:
                five_index = 1
    for s in [_.name for _ in book.sheets]:
        if s in ['Sheet1', 'Sheet2', 'Sheet3']:
            book.sheets[s].delete()
    book.save(f'原神祈愿记录_{time.strftime("%Y%m%d", time.localtime(time.time()))}_{time.strftime("%H%M%S", time.localtime(time.time()))}.xlsx')
    book.close()
    app.quit()