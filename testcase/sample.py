# -*- coding: UTF-8 -*-
#import lib path,only use in this demo
#import sys,os
#sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..\\")))

import wpyscripts.manager as manager
import time
import traceback
import re
import logging
import wpyscripts.uiautomator.uiautomator_manager as m

from wpyscripts.common.wetest_exceptions import *
import wpyscripts.manager as manager

engine = manager.get_engine()
logger = manager.get_logger()
device = manager.get_device()
reporter = manager.get_reporter()
uiauto = m.get_uiautomator()


def back():
    back_button = engine.find_element("/Canvas/Common/TopBar/Button")
    logger.debug(back_button)
    engine.click(back_button)
    time.sleep(1)


def find_element_wait(name, max_count=10, sleeptime=3):
    element = None
    for i in range(max_count):
        try:
            element = engine.find_element(name)
        except WeTestRuntimeError as e:
            logger.warn(e)
            time.sleep(sleeptime)
        if element:
            return element
        else:
            time.sleep(sleeptime)


def click_button(path, text=None):
    logger.debug("screen_shot_click")
    if text:
        results = engine.find_elements_path((path + "{txt=" + text + "}").lstrip())
        if len(results) > 0:
            element = results[0]
    else:
        element = engine.find_element(path)
    if element is None:
        return
    bound = engine.get_element_bound(element)
    logger.debug(bound)
    pos_x = bound.x + bound.width / 2
    pos_y = bound.y + bound.height / 2
    reporter.capture_and_mark(pos_x, pos_y, locator_name=element.object_name)
    engine.click_position(pos_x, pos_y)
    time.sleep(1)


def login(channel):
    if cmp(channel, "QQ") == 0:
        click_button("/Canvas/Contents/ChannelDropdown/Button")
        QQ = engine.find_elements_path("/Canvas/Contents/ChannelDropdown/Dropdown/List/tmp(Clone){txt=QQ(2)}")
        if len(QQ) > 0:
            engine.click(QQ[0])

    if cmp(channel, "WeChat") == 0:
        click_button("/Canvas/Contents/ChannelDropdown/Button")
        WeChat = engine.find_elements_path("/Canvas/Contents/ChannelDropdown/Dropdown/List/tmp(Clone){txt=WeChat(1)}")
        if len(WeChat) > 0:
            engine.click(WeChat[0])

    click_button("/Canvas/Contents/Login")
    if cmp(channel, "QQ") == 0:
        wait_for_package("com.tencent.mobileqq")
    if cmp(channel, "WeChat") == 0:
        wait_for_package("com.tencent.mm")
    device.login_qq_wechat_wait(120)
    time.sleep(10)


def judge_ret(m_id, test_case_name):
    message = engine.find_element("/Canvas/Panel/Panel/Contents/Scroller/Text")
    text = engine.get_element_text(message)
    ret_code = re.findall('RetCode:(.*?),', text)[0]
    method_id = re.findall('MethodNameId:(.*?),', text)[0]
    open_id = re.findall('OpenId:(.*?),', text)
    third_code=re.findall('ThirdCode:(.*?),', text)[0]

    if(cmp(ret_code.lstrip(), "9999") == 0):
        reporter.report(cmp(ret_code.lstrip(), "0") == 0, test_case_name+"  ThirdCode:"+third_code, u"Error")
    else:
        reporter.report(cmp(ret_code.lstrip(), "0") == 0, test_case_name, u"Success")

    #reporter.report(cmp(method_id.lstrip(), "0") == 0, test_case_name, u"Success")
    #assert cmp(method_id.lstrip(), m_id) == 0
    #assert cmp(ret_code.lstrip(), "0") == 0
    #if open_id:
        #assert len(open_id[0]) > 5


def wait_for_package(name):
    """
    :param name:
    :return:
    """
    top_package_activity = None
    for i in range(20):
        try:
            top_package_activity = device.get_top_package_activity()
        except Exception as e:
            stack = traceback.format_exc()
            logger.error(stack)
        if top_package_activity == None:
            time.sleep(1)
            continue
        if top_package_activity.package_name == name:
            logger.debug("Find pakcage {0}".format(top_package_activity.package_name))
            return True
        time.sleep(1)


def wait_for_scene(name, max_count=20, sleeptime=2):
    scene = None
    for i in range(max_count):
        try:
            scene = engine.get_scene()
        except Exception as e:
            logger.error(e)
            time.sleep(sleeptime)
        if scene == name:
            global game_package, game_activity
            package_activity = device.get_top_package_activity()
            game_package = package_activity.package_name
            game_activity = package_activity.activity
            logger.debug("Save Game Package {0}".format(game_package))
            return True
        time.sleep(sleeptime)
    return False


def test():
    version = engine.get_sdk_version()

    logger.debug("Version Information : {0}".format(version))

    #Domestic Login
    wait_for_scene("RegionScene")
    click_button("/Canvas/Contents/TypeDropdown/Button")
    click_button("/Canvas/Contents/TypeDropdown/Dropdown/List/tmp(Clone)", "Domestic")
    click_button("/Canvas/Contents/Enter")
    click_button("/Canvas/Contents/Login")
    ok_return_button = "/Canvas/Panel/Panel/Button"
    return_message = "/Canvas/Panel/Panel/Contents/Scroller"
    reporter.add_start_scene_tag("QQTest")
    # QQ Login
    login("QQ")
    wait_btn = find_element_wait(return_message)
    judge_ret("112", u"QQ Login")
    click_button(ok_return_button)
    back()
    click_button("/Canvas/Contents/Friend")
    click_button("/Canvas/Contents/Share")

    wait_for_package("com.tencent.mobileqq")
    uiauto(text=u'发表', className=u'android.widget.TextView').click()
    # # #
    # # # Get LoginRet
    # click_button("/Canvas/Contents/Get LoginRet")
    # wait_btn = find_element_wait(return_message)
    # judge_ret("114", u"QQ Get LoginRet")
    # click_button(ok_return_button)
    # # #
    # # # # Query UserInfo
    # click_button("/Canvas/Contents/Query UserInfo")
    # wait_btn = find_element_wait(return_message)
    # judge_ret("116", u"QQ Query UserInfo")
    # click_button(ok_return_button)
    # # #
    # # # # Auto Login
    # click_button("/Canvas/Contents/Auto Login")
    # wait_btn = find_element_wait(return_message)
    # judge_ret("111", u"QQ Auto Login")
    # click_button(ok_return_button)
    # # #
    # # Logout
    # click_button("/Canvas/Contents/Logout")
    # wait_btn = find_element_wait(return_message)
    # judge_ret("117", u"QQ Logout")
    # click_button(ok_return_button)
    # reporter.add_end_scene_tag("QQTest")
    #
    # reporter.add_start_scene_tag("WeChatTest")
    # # # WeChat Login
    # login("WeChat")
    # wait_btn = find_element_wait(return_message)
    # judge_ret("112", u"WeChat Login")
    # click_button(ok_return_button)
    #
    # # # Get LoginRet
    # click_button("/Canvas/Contents/Get LoginRet")
    # wait_btn = find_element_wait(return_message)
    # judge_ret("114", u"WeChat Get LoginRet")
    # click_button(ok_return_button)
    # #
    # # # Query UserInfo
    # click_button("/Canvas/Contents/Query UserInfo")
    # wait_btn = find_element_wait(return_message)
    # judge_ret("116", u"WeChat Query UserInfo")
    # click_button(ok_return_button)
    # #
    # # # Auto Login
    # click_button("/Canvas/Contents/Auto Login")
    # wait_btn = find_element_wait(return_message)
    # judge_ret("111", u"WeChat Auto Login")
    # click_button(ok_return_button)
    # #
    # # # Logout
    # click_button("/Canvas/Contents/Logout")
    # wait_btn = find_element_wait(return_message)
    # judge_ret("117", u"WeChat Logout")
    # click_button(ok_return_button)
    # reporter.add_end_scene_tag("WeChatTest")
    # back()
    #
    #
    # #Push Test
    # reporter.add_start_scene_tag("PushTest")
    # click_button("/Canvas/Contents/Push")
    # click_button("/Canvas/Contents/Register")
    # click_button("/Canvas/InputPanel/Panel/Button")
    # find_element_wait("Canvas/Panel/Panel/Contents/Scroller")
    # judge_ret("511", u"Register")
    # click_button(ok_return_button)
    #
    #
    # click_button("/Canvas/Contents/UnRegister")
    # find_element_wait("Canvas/Panel/Panel/Contents/Scroller")
    # judge_ret("512", u"UnRegister")
    # click_button(ok_return_button)
    #
    #
    # click_button("/Canvas/Contents/Set Tag")
    # click_button("/Canvas/InputPanel/Panel/Button")
    # find_element_wait("Canvas/Panel/Panel/Contents/Scroller")
    # judge_ret("513" ,u"SetTag")
    # click_button(ok_return_button)
    #
    # click_button("/Canvas/Contents/Delete Tag")
    # click_button("/Canvas/InputPanel/Panel/Button")
    # find_element_wait("Canvas/Panel/Panel/Contents/Scroller")
    # judge_ret("514", u"DeleteTag")
    # click_button(ok_return_button)
    #
    # click_button("/Canvas/Contents/Add Local Notify")
    # find_element_wait("Canvas/Panel/Panel/Contents/Scroller")
    # judge_ret("518", u"AddLocalNotify")
    # click_button(ok_return_button)
    # reporter.add_end_scene_tag("PushTest")
    # click_button("/Canvas/Contents/WebView")
    # click_button("/Canvas/Contents/openUrl")
    #
    # uiauto.press("back")