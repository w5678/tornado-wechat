# coding:utf-8

import tornado.web
import tornado.options
import tornado.httpserver
import tornado.ioloop
import hashlib
import xmltodict
import time
import tornado.gen
import json
import os
import re

from SqlHandler import SqlHandler

from tornado.web import RequestHandler
from tornado.options import options, define
from tornado.httpclient import AsyncHTTPClient, HTTPRequest


WECHAT_TOKEN = "wang"
WECHAT_APP_ID = "wxdd4d0a78d27aee58"
WECHAT_APP_SECRET = "1e00f6ec7a728c975c15a831e72a7e3e"

define("port", default=8000, type=int, help="")

class AccessToken(object):
    """access_token辅助类"""
    _access_token = None
    _create_time = 0
    _expires_in = 0

    @classmethod
    @tornado.gen.coroutine
    def update_access_token(cls):
        client = AsyncHTTPClient()
        url = "https://api.weixin.qq.com/cgi-bin/token?" \
        "grant_type=client_credential&appid=%s&secret=%s" % (WECHAT_APP_ID, WECHAT_APP_SECRET)
        resp = yield client.fetch(url)
        dict_data = json.loads(resp.body)

        if "errcode" in dict_data:
            raise Exception("wechat server error")
        else:
            cls._access_token = dict_data["access_token"]
            cls._expires_in = dict_data["expires_in"]
            cls._create_time = time.time()

    @classmethod
    @tornado.gen.coroutine
    def get_access_token(cls):
        if time.time() - cls._create_time > (cls._expires_in - 200):
            # 向微信服务器请求access_token
            yield cls.update_access_token()
            raise tornado.gen.Return(cls._access_token)
        else:
            raise tornado.gen.Return(cls._access_token)



class WechatHandler(RequestHandler):
    """对接微信服务器"""
    weather_list=[]
    def prepare(self):
        signature = self.get_argument("signature")
        timestamp = self.get_argument("timestamp")
        nonce = self.get_argument("nonce")
        tmp = [WECHAT_TOKEN, timestamp, nonce]
        tmp.sort()
        tmp = "".join(tmp)
        real_signature = hashlib.sha1(tmp).hexdigest()
        if signature != real_signature:
            self.send_error(403)

    def get(self):
        echostr = self.get_argument("echostr")
        self.write(echostr)

##"苏州天气" "无锡的天气"
    def get_cityname(self,text_content):
        print("get_cityname",text_content)
        city_name=None
        if(re.search(u"天气$",text_content)):
            city_name=re.split(u"天气",text_content)
            print("1",city_name)
        elif(re.search(u"的天气$",text_content)):
            city_name=re.split(u"的天气",text_content)
            print("2",city_name)
        else:
            pass
        print("city_name ret",city_name)
        return city_name[0]

    """
    在这里获取到数据库里匹配的数据，异步查询
    """
    @tornado.gen.coroutine
    def get_weather_from_name(self,city_name):
        print("get weather",city_name)
        ret_list=[]
        sql = SqlHandler()
        #sql.show_ver()
        ret_datas=sql.get_cityCode(city_name)
        print("MYSQL",ret_datas)
        sql.close()
        for city_name in ret_datas:
            temp_list=[]
        #异步查询
            client = AsyncHTTPClient()
            url = r"http://www.weather.com.cn/data/sk/%s.html"%city_name
            print(url)
            req = HTTPRequest(
                url=url,
                method="GET",
                body=None,  # json.dumps(str, ensure_ascii=False)
            )
            resp = yield client.fetch(req)
            ret_data = json.loads(resp.body)
            print(ret_data)
            print("temp",ret_data[u"weatherinfo"][u"temp"])
            if ret_data[u"weatherinfo"][u"temp"]:
                temp_list.append(ret_data[u"weatherinfo"][u"city"].encode("utf8"))
                temp_list.append(ret_data[u"weatherinfo"][u"temp"])
                ret_list.append(temp_list)
            print("ret_list",ret_list)
            WechatHandler.weather_list=ret_list
            raise tornado.gen.Return(ret_list)

# http://api.weixin.qq.com/cgi-bin/media/voice/translatecontent?access_token=ACCESS_TOKEN&lfrom=xxx&lto=xxx
    @tornado.gen.coroutine
    def get_translate_en(self,str):
        trans_ret=None
        try:
            access_token = yield AccessToken.get_access_token()
        except Exception as e:
            self.write("errmsg: %s" % e)
        else:
            client = AsyncHTTPClient()
            url = "http://api.weixin.qq.com/cgi-bin/media/voice/translatecontent?" \
                  "access_token=%s&lfrom=zh_CN&lto=en_US" % (access_token)

            req = HTTPRequest(
                url=url,
                method="POST",
                body=str  # json.dumps(str, ensure_ascii=False)
            )
            resp = yield client.fetch(req)
            ret_data = json.loads(resp.body)
            #print"translate:", ret_data
            if ret_data["to_content"] != "":
                #self.write("OK")
                trans_ret = ret_data["to_content"]
            else:
                pass
                #self.write("failed")
            raise tornado.gen.Return(trans_ret)

    @tornado.gen.coroutine
    def post(self):
        xml_data = self.request.body
        dict_data = xmltodict.parse(xml_data)
        msg_type = dict_data["xml"]["MsgType"]
        if msg_type == "text":
            content = dict_data["xml"]["Content"]
            citys=self.get_cityname(content)
            if citys:
                citys_weather=self.get_weather_from_name(citys)
                print(WechatHandler.weather_list)
                for c in WechatHandler.weather_list:
                    print("c=",c)
                    content=content+'\n'+c[0]+"="+c[1]
                print("post concent=",content)
            """
            <xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[fromUser]]></FromUserName>
<CreateTime>12345678</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[你好]]></Content>
</xml>
"""
            # trans_data=yield self.get_translate_en(content)
            # print("text psot translate:",trans_data)
            # if trans_data!="":
            #     content=trans_data
            # else:
            #     pass
            resp_data = {
                "xml":{
                    "ToUserName": dict_data["xml"]["FromUserName"],
                    "FromUserName": dict_data["xml"]["ToUserName"],
                    "CreateTime": int(time.time()),
                    "MsgType": "text",
                    "Content": content,
                }
            }
            self.write(xmltodict.unparse(resp_data))
        elif msg_type == "voice":

                content = dict_data["xml"]["Recognition"]
                """
                <xml>
    <ToUserName><![CDATA[toUser]]></ToUserName>
    <FromUserName><![CDATA[fromUser]]></FromUserName>
    <CreateTime>12345678</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[你好]]></Content>
    </xml>
    """
                trans_data = yield self.get_translate_en(content)
                if trans_data != "":
                    content = content+"\n"+trans_data
                else:
                    pass
                resp_data = {
                    "xml": {
                        "ToUserName": dict_data["xml"]["FromUserName"],
                        "FromUserName": dict_data["xml"]["ToUserName"],
                        "CreateTime": int(time.time()),
                        "MsgType": "text",
                        "Content": content,
                    }
                }
                self.write(xmltodict.unparse(resp_data))
        elif msg_type == "event":
            if dict_data["xml"]["Event"] == "subscribe":
                """用户关注的事件"""
                resp_data = {
                    "xml": {
                        "ToUserName": dict_data["xml"]["FromUserName"],
                        "FromUserName": dict_data["xml"]["ToUserName"],
                        "CreateTime": int(time.time()),
                        "MsgType": "text",
                        "Content": u"欢迎",
                    }
                }
                if "EventKey" in dict_data["xml"]:
                    event_key = dict_data["xml"]["EventKey"]
                    scene_id = event_key[8:]
                    resp_data["xml"]["Content"] = u"欢迎您 %s次" % scene_id
                self.write(xmltodict.unparse(resp_data))

            elif dict_data["xml"]["Event"] == "SCAN":
               scene_id = dict_data["xml"]["EventKey"]
               resp_data = {
                   "xml": {
                       "ToUserName": dict_data["xml"]["FromUserName"],
                       "FromUserName": dict_data["xml"]["ToUserName"],
                       "CreateTime": int(time.time()),
                       "MsgType": "text",
                       "Content": u"您扫描的是%s" % scene_id,
                   }
               }
               self.write(xmltodict.unparse(resp_data))

            # elif dict_data["xml"]["Event"] == "LOCATION":
            #    Latitude = dict_data["xml"]["Latitude"]
            #    Longitude = dict_data["xml"]["Longitude"]
            #    Precision = dict_data["xml"]["Precision"]
            #    resp_data = {
            #        "xml": {
            #            "ToUserName": dict_data["xml"]["FromUserName"],
            #            "FromUserName": dict_data["xml"]["ToUserName"],
            #            "CreateTime": int(time.time()),
            #            "MsgType": "text",
            #            "Content": u"您位置的经纬是%s %s,精度为%s" %(Longitude,Latitude,Precision),
            #        }
            #    }
            #    self.write(xmltodict.unparse(resp_data))

        else:
            resp_data = {
                "xml": {
                    "ToUserName": dict_data["xml"]["FromUserName"],
                    "FromUserName": dict_data["xml"]["ToUserName"],
                    "CreateTime": int(time.time()),
                    "MsgType": "text",
                    "Content": u"你想干啥呀",
                }
            }
            self.write(xmltodict.unparse(resp_data))


class QrcodeHandler(RequestHandler):
    """请求微信服务器生成带参数二维码返回给客户"""
    @tornado.gen.coroutine
    def get(self):
        scene_id = self.get_argument("sid")
        try:
            access_token = yield AccessToken.get_access_token()
        except Exception as e:
            self.write("errmsg: %s" % e)
        else:
            client = AsyncHTTPClient()
            url = "https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token=%s" % access_token
            req_data = {"action_name": "QR_LIMIT_SCENE", "action_info": {"scene": {"scene_id": scene_id}}}
            req = HTTPRequest(
                url=url,
                method="POST",
                body=json.dumps(req_data)
            )
            resp = yield client.fetch(req)
            dict_data = json.loads(resp.body)
            if "errcode" in dict_data:
                self.write("errmsg: get qrcode failed")
            else:
                ticket = dict_data["ticket"]
                qrcode_url = dict_data["url"]
                self.write('<img src="https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket=%s"><br/>' % ticket)
                self.write('<p>%s</p>' % qrcode_url)


class ProfileHandler(RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        code = self.get_argument("code")
        client = AsyncHTTPClient()
        url = "https://api.weixin.qq.com/sns/oauth2/access_token?" \
                "appid=%s&secret=%s&code=%s&grant_type=authorization_code" % (WECHAT_APP_ID, WECHAT_APP_SECRET, code)
        resp = yield client.fetch(url)
        dict_data = json.loads(resp.body)
        if "errcode" in dict_data:
            self.write("error occur")
        else:
            access_toke = dict_data["access_token"]
            open_id = dict_data["openid"]
            url = "https://api.weixin.qq.com/sns/userinfo?" \
                  "access_token=%s&openid=%s&lang=zh_CN" % (access_toke, open_id)
            resp = yield client.fetch(url)
            user_data = json.loads(resp.body)
            if "errcode" in user_data:
                self.write("error occur again")
            else:
                self.render("index.html", user=user_data)


"""
用户最终访问的URL
https://open.weixin.qq.com/connect/oauth2/authorize?
appid=wxdd4d0a78d27aee58&redirect_uri=http%3A//www.sccnet.top.com/wechat8000/profile&response_type=code&scope=snsapi_userinfo
&state=1#wechat_redirect
"""


class MenuHandler(RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        try:
            access_token = yield AccessToken.get_access_token()
        except Exception as e:
            self.write("errmsg: %s" % e)
        else:
            print("access_token:",access_token)
            client = AsyncHTTPClient()
            url = "https://api.weixin.qq.com/cgi-bin/menu/create?access_token=%s" % access_token
            menu = {
                "button": [
                    {
                        "type": "view",
                        "name": "王的主页",
                        "url":"http://www.soso.com/",
                        #"url": "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxdd4d0a78d27aee58&redirect_uri=http%3A//www.sccnet.top/wechat8000/profile&response_type=code&scope=snsapi_userinfo&state=1&connect_redirect=1#wechat_redirect"
                    },
                    # {
                    #     "name": "菜单",
                    #     "sub_button": [
                    #         {
                    #             "type": "view",
                    #             "name": "搜索",
                    #             "url": "http://www.soso.com/"
                    #         },
                    #         {
                    #             "type": "view",
                    #             "name": "视频",
                    #             "url": "http://v.qq.com/"
                    #         },
                    #         {
                    #             "type": "click",
                    #             "name": "赞一下我们",
                    #             "key": "V1001_GOOD"
                    #         }]
                    # }
                ]
            }
            req = HTTPRequest(
                url=url,
                method="POST",
                body=json.dumps(menu, ensure_ascii=False)
            )
            print("menu url="+req.url)
            print("menu body=" + req.body)
            resp = yield client.fetch(req)
            dict_data = json.loads(resp.body)
            print(dict_data["errcode"])
	    if dict_data["errcode"] == 0:
                self.write("OK")
            else:
                self.write("failed")


def main():
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        [
            (r"/wechat8000", WechatHandler),
            (r"/qrcode", QrcodeHandler),
            (r"/wechat8000/profile", ProfileHandler),
            (r"/wechat8000/menu", MenuHandler),
        ],
        template_path=os.path.join(os.path.dirname(__file__), "template")
    )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
