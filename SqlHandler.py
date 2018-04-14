# encoding:utf-8

import MySQLdb
from config import DB_ADDR,DB_DATABASE,DB_USER,DB_PWD



class SqlHandler(object):
    # 打开数据库连接
    def __init__(self):
        self.db = MySQLdb.connect(DB_ADDR, DB_USER, DB_PWD, DB_DATABASE, charset='utf8')
    #显示版本
    def show_ver(self):
        # 使用cursor()方法获取操作游标
        cursor = self.db.cursor()
        # 使用execute方法执行SQL语句
        cursor.execute("SELECT VERSION()")
        # 使用 fetchone() 方法获取一条数据
        data = cursor.fetchone()
        print "Database version : %s " % data
    def write_mysql(self,cmd_str):
        # 使用cursor()方法获取操作游标
        cursor = self.db.cursor()
        cursor.execute(cmd_str)
        self.db.commit()

    def read_mysql(self,cmd_str):
        # 使用cursor()方法获取操作游标
        cursor = self.db.cursor()
        cursor.execute(cmd_str)
        datas = cursor.fetchall()
        return datas


    # 关闭数据库连接
    def close(self):
        self.db.close()


sql=SqlHandler()
sql.show_ver()
sql.close()