# encoding:utf-8

import MySQLdb
import re
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
        print("Database version : %s " % data)
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

    def get_cityCode(self,cityname):
        """使用mysql里面的模糊查询 like %XXX%
            %需要转义时候一个% 转为后变成%%
            将模糊查询到的一个键值对，变为字典
        """
        self.select_cmd=u"select cityName,cityCode from weather where cityName like '%%%s%%';"%cityname
        #self.select_cmd=u"select cityName,cityCode from weather where cityName like "+"%%"+cityname+"%%;"
        print(self.select_cmd)
        datas=self.read_mysql(self.select_cmd.encode("utf8"))
        print("1",datas)
        dict_datas=[]
        for i  in datas:
            print("2",i[0],i[1])
            dict_datas.append(i[1])
        print(dict_datas)
        return dict_datas


    # 关闭数据库连接
    def close(self):
        self.db.close()



if __name__=="__main__":
    sql=SqlHandler()
    sql.show_ver()
    sql.get_cityCode(u"\u82cf\u5dde")
    sql.close()