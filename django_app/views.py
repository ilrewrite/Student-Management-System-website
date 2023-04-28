from django.shortcuts import render, redirect
from django.http import HttpResponse
# Create your views here.
# import os,django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_name.settings")
# django.setup()

import pymysql

#数据库名，正式运行是需要修改
db_name = 'test'
#以下记录每个表对应操作的格式化sql语句
#参考写法          cursor.execute("INSERT INTO sims_student (student_no,student_name)
#                                   values (%s,%s)", [student_no, student_name])
# key_select_sql_list = {
#     's': "select Sno from S where Sno=%s",
#     'sp': "select Sno, Pno from SP where Sno=%s and Pno=%s",
#     'c': "select Cno from C where Cno=%s",
#     'd': "select Dno from D where Dno=%s",
#     'p': "select Sno from S where Sno=%s",
# }

add_sql_list = {
    's': "insert into S values (%s,%s,%s,%s,%s)",
    'sp': "insert into SP(Sno,Pno) values (%s,%s)",
    'c': "insert into C values (%s,%s,%s,%s,%s)",
    'd': "insert into D values (%s,%s,%s,%s,%s)",
    'p': "insert into P values (%s,%s,%s,%s)"
}
delete_sql_list = {
    's': """delete from S where Sno = %s""",
    'sp': """delete from SP where Sno = %s and Sno=%s""",
    'c': "delete from C where Cno=%s",
    'd': "delete from D where Dno=%s",
    'p': "delete from P where Pno=%s"
}
update_sql_list = {
    's': """update S set 
                 Sno=%s, Sname=%s, Sex=%s, Age=%s, Cno=%s 
                 where Sno=%s""",
    'sp': """update SP set Pno=%s , Sno=%s
                 where Sno=%s and Pno=%s""",
    'c': """update C set 
                 Cno=%s, MName=%s, CYear=%s, CNum=%s, Dno=%s
                 where Cno=%s""",
    'd': """update D set 
                Dno=%s, DName=%s, Office=%s, DNum=%s, Apart=%s
                 where Dno=%s""",
    'p': """update P set 
                 Pno=%s, PYear=%s,PName=%s, PAdd=%s 
                 where Pno=%s"""
}
#每个表的表名到主键名列表的映射
primary_key_list = {'s': ['Sno'], 'c': ['Cno'], 'd': ['Dno'], 'p': ['Pno'], 'sp': ['Sno', 'Pno']}


def connect():
    return pymysql.connect(host='127.0.0.1', port=3306, user="root", passwd="your password", db= db_name)


#获取表对应的列名
def serch_colunm(table_name):
    db = connect()
    with db.cursor() as cursor:
        cursor.execute(f"SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '{db_name}' AND TABLE_NAME = '{table_name}';")
        return cursor.fetchall()


# def test(request):
#     return HttpResponse('hello')
#
#
# def user_list(request):
#     return render(request, 'user_list.html')
#
#
# def tpl(request):
#     name=['hhh', 'ccc', 'ddd']
#     return render(request, 'tpl_test.html', {'n1': name})


#此函数是主页面的处理函数，仅负责把所有表展示出来
def index2(request):
    db = connect()
    with db.cursor() as cursor:
        cursor.execute('show tables;')
        data = cursor.fetchall()
    return render(request, 'index2.html', {'data': data})


# def handle(request):
#
#     return render();


#此函数是查询页面的处理函数，接受一个get的输入table_name,返回对应表的数据
def check(request):
    if request.method == 'GET':
        if len(request.GET) >= 1:
            table_name = request.GET.get('table_name')
            db = connect()
            with db.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name}")
                data = cursor.fetchall()
                cols = serch_colunm(table_name)
            return render(request, 'check_student.html', {'data': data, 'cols': cols, 'table_name': table_name})


#用于给基本表添加元素,第一次进入页面需要传入表名
#由于手动动态生成sql很麻烦，所有直接对所有表手写sql，分别配备增删改函数，命名方式为'操作_表名'
#设计过程中由于大意，由于不会保持状态，又没有把所有的状态写出处理函数,导致很难把表名传入第二次访问的页面，所有使第二次访问的代码有些麻烦
def add(request):
    #如果是GET请求就说明第一次进入页面，先查询对应表的列名
    if request.method == 'GET':
        table_name = request.GET.get('table_name')
        cols = serch_colunm(table_name)
        return render(request, 'add.html', {'cols': cols, 'table_name': table_name})
    else:
        db = connect()
        with db.cursor() as cursor:
            # 下面对应执行的语句，第二个参数是格式化语句参数，类似于printf
            # print(request.POST)
            table_name = request.POST.get('table_name')
            #获取post里蕴含的参数信息
            cols = serch_colunm(table_name)
            args = []
            for col in cols:
                args.append(request.POST.get(col[0]))
            try:
                cursor.execute(add_sql_list[table_name], args)
                db.commit()
            except pymysql.Error as e:
                return render(request, 'exception.html', {'error_meg': e})
        return redirect(f'../check/?table_name={table_name}')


def delete(request):
    table_name = request.GET.get('table_name')
    #由于不知道哪一个元素是主键，所有全部都回传，类型应该后面转换为列表与失去了、语句匹配
    key = request.GET.get('key')
    cols = serch_colunm(table_name)
    full_data = eval(request.GET.get('key'))
    # cols与full_data应该是一一对应的，合并成字典
    data = dict(zip(cols, full_data))
    args=[]
    for elem in data.items():
        if elem[0][0] in primary_key_list[table_name]:
            args.append(elem[1])
    db = connect()
    with db.cursor() as cursor:
        #生成结果放在下面的第二个函数
        try:
            cursor.execute(delete_sql_list[table_name], args)
            db.commit()
        except pymysql.Error as e:
            return render(request, 'exception.html', {'error_meg': e})
    return redirect(f'../check/?table_name={table_name}')


#整体和add差不多,属于add和delete的结合体
def update(request):
    if request.method=='GET':
        #获取表名
        table_name = request.GET.get('table_name')
        #获取列名
        cols = serch_colunm(table_name)
        cols = [x[0] for x in cols]
        #获取修改前数据,eval用来把字符串数据转为元组
        full_data = eval(request.GET.get('key'))
        #cols与full_data应该是一一对应的，合并成字典
        data = dict(zip(cols, full_data))
        #获取主键的值
        key = []
        for k in data.keys():
            if k in primary_key_list[table_name]:
                key.append(k)
        return render(request, 'update.html', {'table_name': table_name,
                                               'primary': key, 'data': data})
    else:
        table_name = request.POST.get('table_name')
        args1 = []
        args2 = []
        cols = serch_colunm(table_name)
        cols = [x[0] for x in cols]
        #记录原本主键值的变量
        record = [x+'_record' for x in cols]
        for elem in request.POST.items():
            if elem[0] in record:
                args2.append(elem[1])
            if elem[0] in cols:
                args1.append(elem[1])
        args = args1+args2
        print(args)
        db = connect()
        with db.cursor() as cursor:
            #生成结果放在下面第二个参数
            try:
                cursor.execute(update_sql_list[table_name], args)
                db.commit()
            except pymysql.Error as e:
                return render(request, 'exception.html', {'error_meg': e})
    return redirect(f'../check/?table_name={table_name}')


def database_view(request):
    db = connect()
    #以字典形式拉取数据
    with db.cursor() as cursor:
        #查询视图的sql
        try:
            cursor.execute('SELECT * FROM SP_view')
            data = cursor.fetchall()
        except pymysql.Error as e:
            return render(request, 'exception.html', {'error_meg': e})
    return render(request, 'view.html', {'data': data})
