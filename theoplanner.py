import json, os, re, sys, zipfile, csv, html
from pathlib import Path
from datetime import date, timedelta
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = 'TheoPlanner'
BASE_DIR = Path(os.getenv('APPDATA') or Path.home()) / APP_NAME
BASE_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = BASE_DIR / 'data.json'

DEFAULT = {'persons': [], 'meetings': [], 'assignments': [], 'imports': []}

def load_data():
    try:
        d = json.loads(DATA_FILE.read_text(encoding='utf-8'))
        return {**DEFAULT, **d}
    except Exception:
        return dict(DEFAULT)

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def clean_text(s):
    s = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', s, flags=re.I|re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s)
    return re.sub(r'\s+', ' ', s).strip()

def read_epub(path):
    texts=[]
    with zipfile.ZipFile(path) as z:
        names=[n for n in z.namelist() if n.lower().endswith(('.xhtml','.html','.htm'))]
        for n in names:
            try:
                raw=z.read(n).decode('utf-8', errors='ignore')
                t=clean_text(raw)
                if t: texts.append(t)
            except Exception: pass
    return '\n\n'.join(texts)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('TheoPlanner — расписание встреч')
        self.geometry('1120x720'); self.minsize(900,580)
        self.configure(bg='#f3f5f8')
        self.data=load_data()
        self.style=ttk.Style(self); self.style.theme_use('clam')
        self.style.configure('TNotebook', background='#f3f5f8', borderwidth=0)
        self.style.configure('TNotebook.Tab', padding=(16,9), font=('Segoe UI',10))
        self.style.configure('Treeview', rowheight=29, font=('Segoe UI',10))
        self.style.configure('Treeview.Heading', font=('Segoe UI',10,'bold'))
        self.build(); self.refresh_all()

    def build(self):
        header=tk.Frame(self,bg='#172b4d',height=76); header.pack(fill='x')
        tk.Label(header,text='TheoPlanner',font=('Segoe UI',22,'bold'),fg='white',bg='#172b4d').pack(side='left',padx=24,pady=16)
        tk.Label(header,text='Личное приложение для планирования встреч',font=('Segoe UI',10),fg='#dbe6f5',bg='#172b4d').pack(side='left',padx=8,pady=24)
        self.status=tk.StringVar(value='Данные сохраняются на этом компьютере')
        tk.Label(self,textvariable=self.status,anchor='w',bg='#e8edf4',fg='#334155',padx=14,pady=7).pack(side='bottom',fill='x')
        self.nb=ttk.Notebook(self); self.nb.pack(fill='both',expand=True,padx=18,pady=16)
        self.tab_meet=ttk.Frame(self.nb,padding=14); self.tab_people=ttk.Frame(self.nb,padding=14); self.tab_assign=ttk.Frame(self.nb,padding=14); self.tab_import=ttk.Frame(self.nb,padding=14)
        self.nb.add(self.tab_meet,text='Расписание встреч'); self.nb.add(self.tab_people,text='Участники'); self.nb.add(self.tab_assign,text='Задания'); self.nb.add(self.tab_import,text='Импорт материалов')
        self.build_meetings(); self.build_people(); self.build_assignments(); self.build_import()

    def tree(self,parent,cols,heads):
        frame=ttk.Frame(parent); frame.pack(fill='both',expand=True,pady=(8,0))
        tr=ttk.Treeview(frame,columns=cols,show='headings',selectmode='browse')
        for c,h in zip(cols,heads): tr.heading(c,text=h); tr.column(c,width=150,anchor='w')
        sy=ttk.Scrollbar(frame,orient='vertical',command=tr.yview); tr.configure(yscrollcommand=sy.set)
        tr.pack(side='left',fill='both',expand=True); sy.pack(side='right',fill='y')
        return tr

    def build_meetings(self):
        tk.Label(self.tab_meet,text='Расписание встреч',font=('Segoe UI',18,'bold')).pack(anchor='w')
        tk.Label(self.tab_meet,text='Добавляй даты и тип встречи. Подробности можно менять в любое время.',fg='#64748b').pack(anchor='w',pady=(2,8))
        bar=ttk.Frame(self.tab_meet); bar.pack(fill='x')
        ttk.Button(bar,text='＋ Добавить встречу',command=self.add_meeting).pack(side='left')
        ttk.Button(bar,text='Изменить выбранную',command=self.edit_meeting).pack(side='left',padx=7)
        ttk.Button(bar,text='Удалить',command=self.delete_meeting).pack(side='left')
        ttk.Button(bar,text='Экспорт CSV',command=self.export_meetings).pack(side='right')
        self.meet_tree=self.tree(self.tab_meet,('date','type','title','notes'),('Дата','Тип встречи','Тема / описание','Заметки'))
        self.meet_tree.column('date',width=115); self.meet_tree.column('type',width=190); self.meet_tree.column('title',width=300); self.meet_tree.column('notes',width=300)

    def build_people(self):
        tk.Label(self.tab_people,text='Участники',font=('Segoe UI',18,'bold')).pack(anchor='w')
        tk.Label(self.tab_people,text='Локальный список участников. Добавляй только те данные, которые нужны тебе.',fg='#64748b').pack(anchor='w',pady=(2,8))
        bar=ttk.Frame(self.tab_people); bar.pack(fill='x')
        ttk.Button(bar,text='＋ Добавить участника',command=self.add_person).pack(side='left')
        ttk.Button(bar,text='Изменить',command=self.edit_person).pack(side='left',padx=7)
        ttk.Button(bar,text='Удалить',command=self.delete_person).pack(side='left')
        self.people_tree=self.tree(self.tab_people,('name','role','contact','notes'),('Имя','Роль / доступность','Контакт (необязательно)','Заметки'))

    def build_assignments(self):
        tk.Label(self.tab_assign,text='Задания',font=('Segoe UI',18,'bold')).pack(anchor='w')
        tk.Label(self.tab_assign,text='Назначай участника на часть встречи. Это базовая версия — автоматическое распределение добавим позже.',fg='#64748b').pack(anchor='w',pady=(2,8))
        bar=ttk.Frame(self.tab_assign); bar.pack(fill='x')
        ttk.Button(bar,text='＋ Добавить задание',command=self.add_assignment).pack(side='left')
        ttk.Button(bar,text='Изменить',command=self.edit_assignment).pack(side='left',padx=7)
        ttk.Button(bar,text='Удалить',command=self.delete_assignment).pack(side='left')
        ttk.Button(bar,text='Экспорт CSV',command=self.export_assignments).pack(side='right')
        self.assign_tree=self.tree(self.tab_assign,('date','part','person','notes'),('Дата встречи','Задание','Участник','Заметки'))

    def build_import(self):
        tk.Label(self.tab_import,text='Импорт материалов',font=('Segoe UI',18,'bold')).pack(anchor='w')
        tk.Label(self.tab_import,text='Выбери файл EPUB с рабочей тетрадью. Приложение извлечёт текст и сохранит его для просмотра.',fg='#64748b').pack(anchor='w',pady=(2,12))
        bar=ttk.Frame(self.tab_import); bar.pack(fill='x')
        ttk.Button(bar,text='Открыть файл EPUB…',command=self.import_epub).pack(side='left')
        ttk.Button(bar,text='Открыть файл PUB…',command=self.import_pub).pack(side='left',padx=8)
        ttk.Button(bar,text='Удалить выбранный импорт',command=self.delete_import).pack(side='left')
        self.import_tree=self.tree(self.tab_import,('filename','date','status'),('Файл','Дата импорта','Результат'))
        self.import_tree.bind('<<TreeviewSelect>>',self.show_import)
        self.preview=tk.Text(self.tab_import,height=10,wrap='word',font=('Segoe UI',10),bg='white',relief='solid',bd=1)
        self.preview.pack(fill='both',expand=False,pady=(10,0)); self.preview.insert('1.0','Здесь появится извлечённый текст из выбранного EPUB-файла.'); self.preview.configure(state='disabled')
        note='Важно: .PUB — не универсальный формат рабочей тетради и может быть зашифрован/неподдерживаем. Сейчас EPUB импортируется как текст; автоматическое распознавание и раскладывание пунктов по неделям потребует проверки на реальном файле.'
        tk.Label(self.tab_import,text=note,wraplength=980,justify='left',fg='#9a3412').pack(anchor='w',pady=(10,0))

    def dialog(self,title,fields,initial=None):
        win=tk.Toplevel(self); win.title(title); win.transient(self); win.grab_set(); win.resizable(False,False)
        entries={}; initial=initial or {}
        for i,(key,label) in enumerate(fields):
            tk.Label(win,text=label,anchor='w').grid(row=i,column=0,sticky='w',padx=14,pady=7)
            e=ttk.Entry(win,width=54); e.grid(row=i,column=1,padx=14,pady=7); e.insert(0,initial.get(key,'')); entries[key]=e
        result={}
        def ok():
            result.update({k:e.get().strip() for k,e in entries.items()}); win.destroy()
        buttons=ttk.Frame(win); buttons.grid(row=len(fields),column=0,columnspan=2,pady=12)
        ttk.Button(buttons,text='Сохранить',command=ok).pack(side='left',padx=5); ttk.Button(buttons,text='Отмена',command=win.destroy).pack(side='left',padx=5)
        win.wait_window(); return result if result else None

    def selected_index(self,tree):
        sel=tree.selection()
        if not sel: return None
        return int(sel[0])
    def add_meeting(self):
        d=self.dialog('Новая встреча',[('date','Дата (ГГГГ-ММ-ДД)'),('type','Тип встречи'),('title','Тема / описание'),('notes','Заметки')],{'date':date.today().isoformat(),'type':'Встреча в середине недели'})
        if d and d['date']:
            self.data['meetings'].append(d); self.changed('Встреча добавлена')
    def edit_meeting(self):
        i=self.selected_index(self.meet_tree)
        if i is None: return messagebox.showinfo('Выбор','Сначала выбери встречу.')
        d=self.dialog('Изменить встречу',[('date','Дата'),('type','Тип встречи'),('title','Тема / описание'),('notes','Заметки')],self.data['meetings'][i])
        if d: self.data['meetings'][i]=d; self.changed('Изменения сохранены')
    def delete_meeting(self):
        i=self.selected_index(self.meet_tree)
        if i is not None and messagebox.askyesno('Удалить','Удалить выбранную встречу?'):
            self.data['meetings'].pop(i); self.changed('Встреча удалена')
    def add_person(self):
        d=self.dialog('Новый участник',[('name','Имя'),('role','Роль / доступность'),('contact','Контакт (необязательно)'),('notes','Заметки')])
        if d and d['name']: self.data['persons'].append(d); self.changed('Участник добавлен')
    def edit_person(self):
        i=self.selected_index(self.people_tree)
        if i is None: return messagebox.showinfo('Выбор','Сначала выбери участника.')
        d=self.dialog('Изменить участника',[('name','Имя'),('role','Роль / доступность'),('contact','Контакт'),('notes','Заметки')],self.data['persons'][i])
        if d: self.data['persons'][i]=d; self.changed('Изменения сохранены')
    def delete_person(self):
        i=self.selected_index(self.people_tree)
        if i is not None and messagebox.askyesno('Удалить','Удалить выбранного участника?'):
            self.data['persons'].pop(i); self.changed('Участник удалён')
    def add_assignment(self):
        people=[p.get('name','') for p in self.data['persons']]
        d=self.dialog('Новое задание',[('date','Дата встречи'),('part','Название задания'),('person','Участник (имя из списка)'),('notes','Заметки')],{'date':date.today().isoformat(),'person':people[0] if people else ''})
        if d and d['part']: self.data['assignments'].append(d); self.changed('Задание добавлено')
    def edit_assignment(self):
        i=self.selected_index(self.assign_tree)
        if i is None: return messagebox.showinfo('Выбор','Сначала выбери задание.')
        d=self.dialog('Изменить задание',[('date','Дата встречи'),('part','Название задания'),('person','Участник'),('notes','Заметки')],self.data['assignments'][i])
        if d: self.data['assignments'][i]=d; self.changed('Изменения сохранены')
    def delete_assignment(self):
        i=self.selected_index(self.assign_tree)
        if i is not None and messagebox.askyesno('Удалить','Удалить выбранное задание?'):
            self.data['assignments'].pop(i); self.changed('Задание удалено')
    def import_epub(self):
        path=filedialog.askopenfilename(title='Выбери EPUB',filetypes=[('EPUB files','*.epub'),('All files','*.*')])
        if not path: return
        try:
            text=read_epub(path)
            if not text: raise ValueError('В файле не удалось найти читаемый текст.')
            self.data['imports'].append({'filename':Path(path).name,'date':date.today().isoformat(),'status':f'Текст извлечён ({len(text)} символов)','text':text,'path':path})
            self.changed('EPUB импортирован'); self.status.set(f'Импортировано: {Path(path).name}'); self.preview_text(text)
            messagebox.showinfo('Импорт завершён',f'Текст извлечён: {len(text):,} символов.\nПока он сохраняется для просмотра, но не распределяется автоматически по расписанию.')
        except Exception as e: messagebox.showerror('Ошибка импорта',f'Не удалось прочитать EPUB.\n{e}')
    def import_pub(self):
        path=filedialog.askopenfilename(title='Выбери PUB',filetypes=[('PUB files','*.pub'),('All files','*.*')])
        if not path: return
        messagebox.showwarning('Формат PUB','Файл выбран, но надёжный импорт формата .PUB пока не реализован. Если это публикация JW Library, попробуем добавить поддержку после проверки конкретного файла. Для расписания встреч TheocBase обычно импортирует рабочую тетрадь в формате EPUB.')
    def show_import(self,event=None):
        i=self.selected_index(self.import_tree)
        if i is not None: self.preview_text(self.data['imports'][i].get('text','Для этого импорта нет извлечённого текста.'))
    def preview_text(self,text):
        self.preview.configure(state='normal'); self.preview.delete('1.0','end'); self.preview.insert('1.0',text[:100000]); self.preview.configure(state='disabled')
    def delete_import(self):
        i=self.selected_index(self.import_tree)
        if i is not None and messagebox.askyesno('Удалить','Удалить запись импорта?'):
            self.data['imports'].pop(i); self.changed('Запись импорта удалена'); self.preview_text('Выбери импорт, чтобы посмотреть его содержимое.')
    def export_meetings(self): self.export_csv('meetings',[('date','Дата'),('type','Тип'),('title','Тема'),('notes','Заметки')],'raspisanie_vstrech.csv')
    def export_assignments(self): self.export_csv('assignments',[('date','Дата'),('part','Задание'),('person','Участник'),('notes','Заметки')],'zadaniya.csv')
    def export_csv(self,key,fields,default):
        path=filedialog.asksaveasfilename(defaultextension='.csv',initialfile=default,filetypes=[('CSV','*.csv')])
        if not path:return
        with open(path,'w',newline='',encoding='utf-8-sig') as f:
            w=csv.writer(f,delimiter=';'); w.writerow([x[1] for x in fields])
            for item in self.data[key]: w.writerow([item.get(x[0],'') for x in fields])
        messagebox.showinfo('Экспорт',f'Файл сохранён:\n{path}')
    def changed(self,msg): save_data(self.data); self.refresh_all(); self.status.set(msg+' · данные сохранены локально')
    def refresh_all(self):
        for tree in (getattr(self,'meet_tree',None),getattr(self,'people_tree',None),getattr(self,'assign_tree',None),getattr(self,'import_tree',None)):
            if tree:
                for x in tree.get_children(): tree.delete(x)
        if hasattr(self,'meet_tree'):
            for i,m in enumerate(sorted(self.data['meetings'],key=lambda x:x.get('date',''))): self.meet_tree.insert('', 'end',iid=str(self.data['meetings'].index(m)),values=(m.get('date',''),m.get('type',''),m.get('title',''),m.get('notes','')))
            for i,p in enumerate(self.data['persons']): self.people_tree.insert('', 'end',iid=str(i),values=(p.get('name',''),p.get('role',''),p.get('contact',''),p.get('notes','')))
            for i,a in enumerate(sorted(self.data['assignments'],key=lambda x:x.get('date',''))): self.assign_tree.insert('', 'end',iid=str(self.data['assignments'].index(a)),values=(a.get('date',''),a.get('part',''),a.get('person',''),a.get('notes','')))
            for i,x in enumerate(self.data['imports']): self.import_tree.insert('', 'end',iid=str(i),values=(x.get('filename',''),x.get('date',''),x.get('status','')))

if __name__=='__main__':
    App().mainloop()
