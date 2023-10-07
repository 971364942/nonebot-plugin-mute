# src/plugins/mute_plugin/mute_plugin.py
# bot.send(event, message)

import time
import random
from nonebot import on_message, on_startswith
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, Message, MessageSegment
from nonebot.typing import T_State
import re
import json

# 存储被@的人和@他的人
at_dict = {}

# 存储每个人上次发送口他的时间
cd_dict = {}

CommandsFile = 'data/mute_commands.json'

group_commands_config = {}

# 读取分群口令指令文件
try:
    with open(CommandsFile, 'r', encoding='utf-8') as file:
        group_commands_config = json.load(file)
except FileNotFoundError:
    with open(CommandsFile, 'w', encoding='utf-8') as file:
        json.dump({}, file, ensure_ascii=False, indent=4)
    group_commands_config = {} 

matcher = on_message()
@matcher.handle()
async def check_password(bot: Bot, event: GroupMessageEvent, state: T_State):

    message = event.raw_message
    group_id = event.group_id

    # 获取群号对应的口令列表
    group_commands = group_commands_config.get(str(group_id), [])
    if "口他" not in group_commands:
        group_commands.append("口他")

    # 检查消息是否是口令a
    for command in group_commands:
        if command in message:
            break
    else:
        return

    user_id = event.user_id

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
            await bot.set_group_ban(group_id=group_id, user_id=user_id, duration=mute_time)
            await matcher.finish(Message("谁给你的勇气口我的！"))

    # @了管理员或者群主  
    member_info =  await bot.get_group_member_info(group_id=group_id, user_id=at_qq)
    if member_info['role'] == "owner" or member_info['role'] == "admin":  
        await matcher.finish(Message("这位可口不得"))

    # 获取当前时间
    now_time = time.time()

    # 获取用户在该群的上次发送口他的时间
    last_time = cd_dict.get((user_id, group_id), 0)
    
    # 检查是否在冷却时间内且不是管理员
    if now_time - last_time < 300 and not (event.sender.role == "owner" or event.sender.role == "admin"):
        await matcher.finish(Message("你口太快了！"), reply_message=True)
    
    # 更新冷却时间
    cd_dict[(user_id, group_id)] = now_time
    
    # 更新被@的人的记录
    if at_qq not in at_dict or len(at_dict[at_qq]) == 0 or now_time - at_dict[at_qq][0][1] > 300:
        at_dict[at_qq] = [(user_id, now_time)]
    else:
        at_dict[at_qq].append((user_id, now_time))
    
    # 检查是否有3个不同的人在5分钟内@了他
    if len([x[0] for x in at_dict[at_qq]]) >= 3:
        mute_time = random.randint(60, 600)
        await bot.set_group_ban(group_id=group_id, user_id=at_qq, duration=mute_time)

        at_dict.pop(at_qq, None)

        msg = MessageSegment(type='at', data={'qq': at_qq}) + f"被口了 {mute_time//60} 分钟！"
        await matcher.finish(Message(msg))
    else:
        msg = MessageSegment(type='at', data={'qq': at_qq}) + f"当前已被投{len(at_dict[at_qq])}票，5分钟内超过3票将会被禁言1-10分钟。"
        await matcher.finish(Message(msg))
    
# 增加指令
matcher2 = on_startswith(("增加指令", "添加指令"))
@matcher2.handle()
async def add_command_handler(bot: Bot, event: GroupMessageEvent, state: T_State):
    # 从消息中提取新指令
    new_command = event.raw_message.lstrip("增加指令").lstrip("添加指令").strip()


    if not new_command:
        await matcher2.finish("新指令不能为空哦！")

    # 调用添加指令的函数
    add_command(event.group_id, new_command)

    # 发送消息通知添加成功
    await matcher2.finish(f"成功添加指令：{new_command}")
    
# 写入新指令
def add_command(group_id, new_command):

    global group_commands_config

    add_group_commands = []

    # 获取群号对应的指令列表
    add_group_commands = group_commands_config.get(str(group_id), [])
    
    # 添加新的口他指令
    add_group_commands.append(new_command)
    if "口他" in add_group_commands:
        add_group_commands.remove("口他")

    # 更新配置文件
    group_commands_config[str(group_id)] = add_group_commands
    with open(CommandsFile, 'w', encoding='utf-8') as file:
        json.dump(group_commands_config, file, ensure_ascii=False, indent=4)    
