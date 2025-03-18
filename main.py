from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
import os
import json
from datetime import datetime

@register("group_monitor", "您的名字", "监听指定群消息的插件", "1.0.0", "https://github.com/yourusername/astrbot_plugin_group_monitor")
class GroupMonitorPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 配置文件路径
        self.config_path = os.path.join(os.path.dirname(__file__), "config.json")
        # 读取配置
        self.config = self.load_config()
        # 日志文件路径
        self.log_path = os.path.join(os.path.dirname(__file__), "message_log.txt")
        
    def load_config(self):
        """加载配置文件，如果不存在则创建默认配置"""
        default_config = {
            "monitor_groups": [],  # 要监听的群ID列表
            "enable_log": True,    # 是否启用日志记录
            "print_console": True  # 是否在控制台打印消息
        }
        
        if not os.path.exists(self.config_path):
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, ensure_ascii=False, indent=4)
            return default_config
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"读取配置文件失败: {e}")
            return default_config
    
    def save_config(self):
        """保存配置到文件"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)
    
    def log_message(self, group_id, sender_name, sender_id, message):
        """记录消息到日志文件"""
        if not self.config.get("enable_log", True):
            return
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] 群:{group_id} | 发送人:{sender_name}({sender_id}) | 消息:{message}\n"
        
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            self.logger.error(f"写入日志失败: {e}")
    
    # 监听所有群消息
    @filter.group_message()
    async def monitor_group_message(self, event: AstrMessageEvent):
        """监听群消息"""
        # 获取群ID
        group_id = event.group_id
        
        # 检查是否是需要监听的群
        if self.config["monitor_groups"] and group_id not in self.config["monitor_groups"]:
            return
        
        # 获取发送人信息
        sender_name = event.get_sender_name()
        sender_id = event.sender.uid
        
        # 获取消息内容
        message = event.message_str
        
        # 在控制台打印
        if self.config.get("print_console", True):
            print(f"群:{group_id} | 发送人:{sender_name}({sender_id}) | 消息:{message}")
        
        # 记录到日志文件
        self.log_message(group_id, sender_name, sender_id, message)
        
        # 这个事件处理完毕，不需要回复
        return None
    
    # 添加群监听指令
    @filter.command("add_monitor")
    async def add_monitor_group(self, event: AstrMessageEvent):
        """添加要监听的群，格式：/add_monitor 群号"""
        # 仅允许超级用户使用此命令
        if not await self.context.check_superuser(event.sender.uid):
            yield event.plain_result("权限不足，仅超级用户可以使用此命令")
            return
            
        # 解析参数
        args = event.message_str.split()
        if len(args) < 2:
            yield event.plain_result("请提供要监听的群号，格式：/add_monitor 群号")
            return
            
        group_id = args[1]
        
        # 添加到监听列表
        if group_id not in self.config["monitor_groups"]:
            self.config["monitor_groups"].append(group_id)
            self.save_config()
            yield event.plain_result(f"已添加群 {group_id} 到监听列表")
        else:
            yield event.plain_result(f"群 {group_id} 已在监听列表中")
    
    # 移除群监听指令
    @filter.command("remove_monitor")
    async def remove_monitor_group(self, event: AstrMessageEvent):
        """移除监听的群，格式：/remove_monitor 群号"""
        # 仅允许超级用户使用此命令
        if not await self.context.check_superuser(event.sender.uid):
            yield event.plain_result("权限不足，仅超级用户可以使用此命令")
            return
            
        # 解析参数
        args = event.message_str.split()
        if len(args) < 2:
            yield event.plain_result("请提供要移除的群号，格式：/remove_monitor 群号")
            return
            
        group_id = args[1]
        
        # 从监听列表中移除
        if group_id in self.config["monitor_groups"]:
            self.config["monitor_groups"].remove(group_id)
            self.save_config()
            yield event.plain_result(f"已从监听列表中移除群 {group_id}")
        else:
            yield event.plain_result(f"群 {group_id} 不在监听列表中")
    
    # 列出所有监听的群
    @filter.command("list_monitors")
    async def list_monitor_groups(self, event: AstrMessageEvent):
        """列出所有监听的群"""
        # 仅允许超级用户使用此命令
        if not await self.context.check_superuser(event.sender.uid):
            yield event.plain_result("权限不足，仅超级用户可以使用此命令")
            return
            
        if not self.config["monitor_groups"]:
            yield event.plain_result("监听列表为空")
        else:
            groups = "\n".join(self.config["monitor_groups"])
            yield event.plain_result(f"当前监听的群列表:\n{groups}")
    
    async def terminate(self):
        """插件被卸载时的清理工作"""
        self.logger.info("群消息监听插件已卸载")
