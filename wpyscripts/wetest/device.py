# -*- coding: UTF-8 -*-
"""
Tencent is pleased to support the open source community by making GAutomator available.
Copyright (C) 2016 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at
http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.


    un-Thread-safe

    Service use libaray https://github.com/xiaocong/uiautomator

    Mobile feature use uiautomator service,so maybe confict with other process which also use uiautomator serice,such as Monkeyrunner,AccessibilityService
"""

__author__ = 'minhuaxu wukenaihesos@gmail.com'

import re
import traceback
import os
import logging

from wpyscripts.common.adb_process import excute_adb
from wpyscripts.common.wetest_exceptions import (WeTestRuntimeError, UIAutomatorError, WeTestInvaildArg, LoginError)
from wpyscripts.httptools.exceptions import ConnectionException
from wpyscripts.common.adb_process import AdbTool
import wpyscripts.common.platform_helper as platform
from functools import wraps

logger = logging.getLogger("wetest")


class DisplaySize(object):
    """
        Mobile Screen resolution
    Attributes:
        width: width px
        height:height px
    """

    def __init__(self, width, height):
        self.__width = width
        self.__height = height

    @property
    def width(self):
        return self.__width

    @property
    def height(self):
        return self.__height

    def __str__(self):
        return "width = {0},height = {1}".format(self.width, self.height)


class TopActivity(object):
    """
        Mobile current foreground activity and package name.activity is None,when android version > 5.0
    Attributes:
        activity:top Activity
        package_name:forceground package name
    """

    def __init__(self, _activity, _package):
        self.activity = _activity
        self.package_name = _package

    def __str__(self):
        return "package name = {0},activity = {1}".format(self.package_name, self.activity)


def exception_call_super(fn):
    """
        Decorate function

        CloudDevice call function use wetest platorm http service,when raise exception,try to call parent class method
        很多方法请求平台时，有可能出现问题。请求平台出现问题时，可以直接尝试使用本地方法。
        CloudDevice调用失败时，直接调用Device里面相同名称的方法
    :param fn:
    :return:
    """

    @wraps(fn)
    def wrap_function(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (WeTestRuntimeError, ConnectionException):
            logger.warn("call cloud function {0} error".format(fn.__name__))
            return getattr(super(CloudDevice, args[0]), fn.__name__)(*args[1:], **kwargs)

    return wrap_function


class Device(object):
    """"Base Mobile Related operations"""

    def __init__(self, serial, package, ui_device):
        super(Device, self).__init__()
        self.serial = serial
        self.package = package
        self.ui_device = ui_device
        self._adb = AdbTool()  # serial, os.environ.get("PLATFORM_IP", "127.0.0.1")

    @property
    def adb(self):
        return self._adb

    def get_rotation(self):
        """
            get mobile current rotation
            orienting the devie to left/right or natural.
            left/l:       rotation=90 , displayRotation=1
            right/r:      rotation=270, displayRotation=3
            natural/n:    rotation=0  , displayRotation=0
            upsidedown/u: rotation=180, displayRotation=2
        :return: 0,90,180 or 270
        """
        rotation = self.ui_device.info["displayRotation"]
        return rotation * 90

    def get_display_size(self):
        """
            Get mobile screen resolution
        :Usage:
            >>> import wpyscripts.manager as manager
            >>> device=manager.get_device()
            >>> display=device.get_display_size()
        :return:
            a instance of DisplaySize
        :rtype: DisplaySize
        """
        try:
            return DisplaySize(self.ui_device.info["displayWidth"], self.ui_device.info["displayHeight"])
        except:
            stack = traceback.format_exc()
            logger.warn(stack)

        result = self.adb.cmd_wait("shell", "dumpsys", "window", "displays")

        if result:
            pattern = re.compile(r'cur=(\d+)x(\d+)')
            line = result.readline()
            while line:
                match = pattern.search(line)
                if match:
                    dispaly_size = DisplaySize(int(match.group(1)), int(match.group(2)))
                    return dispaly_size
                line = result.readline()

    def get_top_package_activity(self):
        """
            get the current foreground activity
        :Usage:
            >>> import wpyscripts.manager as manager
            >>> device=manager.get_device()
            >>> display=device.get_top_package_activity()
        :return:
            a instance of TopActivity
        :rtype: TopActivity
        """

        try:
            return TopActivity("", self.ui_device.info["currentPackageName"])
        except:
            stack = traceback.format_exc()
            logger.warn(stack)

    def _is_package_live(self, package=None):
        logger.warn("_is_package_live unimplement")

    def back(self):
        """
            Click back button

            When your game not force,you call engine api may catch timeout exception.At this time you can call back
        :Usage:
            >>> import wpyscripts.manager as manager
            >>> device=manager.get_device()
            >>> display=device.back()
        :return:
        """
        try:
            self.ui_device.press("back")
        except Exception as e:
            raise UIAutomatorError(e.message)

    def launch_app(self, package, activity="android.intent.category.LAUNCHER"):
        """
        启动游戏，游戏启动后返回。返回启动后的Pid和拉起时间，device实例会保存Pid的值
        :param package:
        :return:(234,2341)分别代表打起后的pid和拉起时间
        """
        result = self.adb.cmd_wait("shell", "monkey", "-p", package, "-c", activity, "1")
        if result:
            content = result
            logger.debug(content)
        result = excute_adb("shell ps")

        if result:
            pattern_str = r"(?P<user>\S+)\s+(?P<pid>\d+)\s+(?P<ppid>\d+)\s.*{0}\s+".format(package)
            pattern = re.compile(pattern_str)
            line = result.readline()
            while line:
                match = pattern.search(line)
                if match:
                    pid = match.groupdict().get("pid")
                    pid = int(pid)
                    return pid, 0
                line = result.readline()

    def clear_data(self, package=None):
        """
            Adb shell pm clear package,clear app data
        :param package:
        :return:
        """
        if package is None:
            raise WeTestInvaildArg("Error,No app packagename")
        result = self.adb.cmd_wait("shell", "pm", "clear", package)
        if result:
            content = result.read()
            logger.debug(content)

    def _clear_qq_account(self):
        logger.debug("adb shell pm clear com.tencent.mobileqq")
        try:
            result = self.adb.cmd_wait("shell", "pm", "clear", "com.tencent.mobileqq")
            if result:
                content = result.read()
                logger.debug(content)
        except:
            stack = traceback.format_exc()
            logger.warn(stack)

        logger.debug("adb shell pm clear com.tencent.mm")
        try:
            result = self.adb.cmd_wait("shell", "pm", "clear", "com.tencent.mm")
            if result:
                content = result.read()
                logger.debug(content)
        except:
            stack = traceback.format_exc()
            logger.warn(stack)

    def _clear_user_info(self, package):
        if package == None:
            raise WeTestInvaildArg("Package Name can't be none")
        logger.debug("adb shell pm clear {0}".format(package))
        result = excute_adb("shell pm clear {0}".format(package))
        if result:
            content = result.read()
            logger.debug(content)

    def excute_adb(self, cmd):
        """
            Open a pipe to/from a adb command returning a file object,when command is end

            if testcat is run on wetest platorm,you can put your file to UPLOADDIR,and download from reporter
        :Usage:
            >>> import wpyscripts.manager as manager
            >>> device=manager.get_device()
            >>> device.excute_adb_shell("pull /data/local/tmp {0}/perform.txt".format(os.environ.get("UPLOADDIR",".")))
        :param cmd: adb command
        :return:a file object
        """
        return excute_adb(cmd)

    def get_current_package(self):
        return self.ui_device.info["currentPackageName"]

    def login_qq_wechat_wait(self, timeout=60):
        """
            如果是在QQ或者微信登陆界面调用该函数，则会尝试登陆。在本地运行时，请在main.py进行开头或者命令行设置。在wetest平台运行时，每部手机会下发不同的账号，自定义
            账号保存在OTHERNAME和OTHERPWD。
            :usage:

        :param timeout:登陆超时时间，秒
        :return 登陆packagename退出，则认为登陆成功True。超时还没登陆，则返回False
        """
        import wpyscripts.uiautomator.login_tencent as login
        _current_pkgname = self.get_current_package()
        logger.info("Current Pkgname: " + _current_pkgname)
        if _current_pkgname == "com.tencent.mobileqq":
            account = os.environ.get("OTHERNAME") or os.environ.get("QQNAME")
            pwd = os.environ.get("OTHERPWD") or os.environ.get("QQPWD")
            if not account or not pwd:
                raise LoginError("no account or pwd,please check OTHERNAME or QQNAME environment")
        elif _current_pkgname == "com.tencent.mm":
            account = os.environ.get("OTHERNAME") or os.environ.get("WECHATNAME")
            pwd = os.environ.get("OTHERPWD") or os.environ.get("WECHATPWD")
            if not account or not pwd:
                raise LoginError("no account or pwd,please check OTHERNAME or WECHATNAME environment")
        else:
            account = os.environ.get("WECHATNAME")
            pwd = os.environ.get("WECHATPWD")
            if not account or not pwd:
                raise LoginError("no account or pwd,please check OTHERNAME or WECHATNAME environment")
        return login.login_tencent(account, pwd, timeout)

    def qq_account(self):
        """
            Get qq acount and password,when run wetest platorm，each mobile will allocate a account
        :return:tuple QQ account and password
        """
        qq_account = os.environ.get("QQNAME")
        qq_pwd = os.environ.get("QQPWD")
        return qq_account, qq_pwd

    def wx_account(self):
        """
            Get wechat acount and password,when run wetest platorm，each mobile will allocate a account
        :return:tuple of wechat account and password
        """
        weixin_account = os.environ.get("WECHATNAME")
        weixin_pwd = os.environ.get("WECHATPWD")
        return weixin_account, weixin_pwd

    def self_define_account(self):
        """
            Get self define account,your uploaded accounts will allocate to mobile
        :return: tupe of self define account and password
        """
        account = os.environ.get("OTHERNAME")
        pwd = os.environ.get("OTHERPWD")
        return account, pwd

    def start_handle_popbox(self, handle_package_pattern=None, handle_text_pattern=None):
        pass

    def stop_handle_popbox(self):
        pass


class CloudDevice(Device):
    """
        wetest平台运行时会创建该实现类
    """
    from libs.uiauto.uiautomator import AutomatorDevice

    def __init__(self, serial, _package_name, _activity, ui_device=AutomatorDevice()):
        super(CloudDevice, self).__init__(serial, _package_name, ui_device)
        self.package_name = _package_name
        self.launch_activity = _activity
        self.pid = None
        self.timeout = 3000
        self.platform_client = platform.get_platform_client()

    @exception_call_super
    def get_display_size(self):
        """
            返回屏幕长宽
        :Usage:
            device=manage.get_device()
            display=device.get_display_size()
        :return:
            a instance of DisplaySize
        :rtype: DisplaySize
        :raise: WeTestPlatormError
        """
        response = self.platform_client.get_display_size()
        self.width = response["width"]
        self.height = response["height"]
        return DisplaySize(response["width"], response["height"])

    def get_top_package_activity(self):
        """
            获取当前手机的顶层的Activity名称和package名称
        :Usage:
            device=manage.get_device()
            activity=device.get_top_package_activity()
        :return:
            a instance of TopActivity
        :rtype: TopActivity
        :raise: WeTestPlatormError
        """
        return TopActivity("", self.ui_device.info["currentPackageName"])

    def launch_app(self, package=None, activity=None):
        """
        启动游戏，游戏启动后返回。返回启动后的Pid和拉起时间，device实例会保存Pid的值
        :param package:
            None的情况下会拉起，当前测试app
        :Usage:
            >>> import wpyscripts.manager as manager
            >>> device=manager.get_device()
            >>> device.launch_app()
        :return:(234,2341)分别代表打起后的pid和拉起时间
        :rtype tuple,
        """
        if package is not None:
            package_name = package
        elif self.package_name is not None:
            package_name = self.package_name
        else:
            raise WeTestInvaildArg("Error,Unknow app packagename")

        if activity is not None:
            launcher = activity
        elif self.launch_activity is not None:
            launcher = self.launch_activity
        else:
            launcher = "android.intent.category.LAUNCHER"

        if len(package_name) >= 128:
            raise WeTestInvaildArg("Error,Package name {0} length more than 128")

        logger.debug("Launch app {0}".format(package_name))

        response = self.platform_client.launch_app(package_name, launcher)
        return response

    @exception_call_super
    def get_rotation(self):
        """
            get mobile current rotation
            orienting the devie to left/right or natural.
            left/l:       rotation=90 , displayRotation=1
            right/r:      rotation=270, displayRotation=3
            natural/n:    rotation=0  , displayRotation=0
            upsidedown/u: rotation=180, displayRotation=2
        :return: 0,90,180 or 270
        """
        response = self.platform_client.get_rotation()
        return response["rotation"]

    @exception_call_super
    def clear_data(self, package=None):
        if package is None:
            raise WeTestInvaildArg("Error,No app packagename")
        response = self.platform_client.clear_app_data(package)
        if response:
            return response

    @exception_call_super
    def _clear_qq_account(self):
        self.clear_data("com.tencent.mobileqq")
        self.clear_data("com.tencent.mm")

    @exception_call_super
    def _clear_user_info(self, package=None):
        if package is not None:
            package_name = package
        elif self.package_name is not None:
            package_name = self.package_name
        else:
            raise WeTestInvaildArg("Error,Unknow app packagename")

        if len(package_name) >= 128:
            raise WeTestInvaildArg("Error,Package name {0} length more than 128")

        self.clear_data(package_name)


class NativeDevice(Device):
    """
        在本地运行调试时，会创建
    """

    def __init__(self, serial, ui_device):
        super(NativeDevice, self).__init__(serial, None, ui_device)
        """
            main.py中可以进行全局本地测试时的配置，但是测试的时候不一定会从main运行，这个时候就需要在这个地方配置账号和密码
        """
        if not os.environ.get("QQNAME"):
            os.environ["QQNAME"] = "3235641945"
            os.environ["QQPWD"] = "iTOP1234567890"
        # account 3235641945
        # pwd iTOP1234567890
        if not os.environ.get("WECHATNAME"):
            os.environ["WECHATNAME"] = "ceshihaoabcd"
            os.environ["WECHATPWD"] = "tencent1234"

    def start_handle_popbox(self, handle_package_pattern=None, handle_text_pattern=None):
        if not handle_package_pattern:
            handle_package_pattern = u"^(?!(com.tencent.mm|com.tencent.mqq|com.tencent.mobileqq|com.android.contacts|com.android.mms|com.yulong.android.contacts|com.android.dialer|com.android.keyguard|com.tencent.mm.coolassist|com.example.test.wegame.TestMainPanel|cn.uc.gamesdk.account)$).*"

        if not handle_text_pattern:
            handle_text_pattern = u"(^(完成|关闭|关闭应用|好|好的|确定|确认|安装|下次再说|知道了)$|(.*(?<!不)(忽略|允(\s){0,2}许|同意)|继续|清理|稍后|暂不|强制|下一步).*)"

        logger.debug(u"monitor package pattern {0}".format(handle_package_pattern))
        logger.debug(u"monitor click text {0}".format(handle_text_pattern))
        self.ui_device.start_pop_monitor(handle_package_pattern, handle_text_pattern)

    def stop_handle_popbox(self):
        logger.debug("close pop box handler")
        self.ui_device.stop_pop_monitor()
