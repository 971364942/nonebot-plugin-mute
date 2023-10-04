# src/plugins/mute_plugin/mute_plugin.py

import time
from datetime import datetime, timedelta
import random
from nonebot import on_endswith, on_notice, on_keyword
from nonebot.rule import is_type
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, GROUP_ADMIN, GROUP_OWNER, GroupIncreaseNoticeEvent, Message, MessageSegment
from nonebot.typing import T_State
import re

# 存储被@的人和@他的人
at_dict = {}

# 存储每个人上次发送口他的时间
cd_dict = {}

matcher = on_keyword('口他')
@matcher.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):

    # 获取被@的人的QQ号
    message = event.raw_message
    qq_match = re.search(r'\[CQ:at,qq=(\d+)\]', message)

    if qq_match:
        at_qq = qq_match.group(1)
    else:
        return 

    # @了bot
    if f"{at_qq}" == f"{event.self_id}":
        if event.sender.role == "owner" or event.sender.role == "admin":
            await matcher.finish(Message("嘤嘤嘤不要欺负我了"))
        else:
            mute_time = random.randint(60, 600)
            await bot.set_group_ban(group_id=event.group_id, user_id=event.user_id, duration=mute_time)
            await matcher.finish(Message("谁给你的勇气口我的！"))

    # @了管理员或者群主    
    member_info = await bot.get_group_member_info(group_id=event.group_id, user_id=at_qq)
    if member_info['role'] == "owner" or member_info['role'] == "admin":
        await matcher.finish(Message("这位可口不得"))

    # 获取当前时间
    now_time = time.time()
    
    # 检查是否在冷却时间内
    if now_time - cd_dict.get(event.user_id, 0) < 300:
        await matcher.finish(Message("你口太快了！"), reply_message=True)
    
    # 更新冷却时间
    cd_dict[event.user_id] = now_time
    
    # 更新被@的人的记录
    if at_qq not in at_dict or len(at_dict[at_qq]) == 0 or now_time - at_dict[at_qq][0][1] > 300:
        at_dict[at_qq] = [(event.user_id, now_time)]
    else:
        at_dict[at_qq].append((event.user_id, now_time))
    
    # 检查是否有3个不同的人在5分钟内@了他
    if len(set([x[0] for x in at_dict[at_qq]])) >= 3:
        mute_time = random.randint(60, 600)
        await bot.set_group_ban(group_id=event.group_id, user_id=at_qq, duration=mute_time)

        at_dict.pop(at_qq, None)

        msg = MessageSegment(type='at', data={'qq': at_qq}) + f"被口了 {mute_time//60} 分钟！"
        await matcher.finish(Message(msg))
    else:
        msg = MessageSegment(type='at', data={'qq': at_qq}) + f"当前已被投{len(at_dict[at_qq])}票，5分钟内超过3票将会被禁言1-10分钟。"
        await matcher.finish(Message(msg))

