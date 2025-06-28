import liqi
from mitmproxy import http, ctx
from .plugin import mod
from ruamel.yaml import YAML
from .plugin import update_liqi
from common.log_helper import LOGGER

VERSION = '20241202'

DEFAULT_CONFIG = """
# 插件配置，true为开启，false为关闭
plugin_enable:
  mod: false  # mod用于解锁全部角色、皮肤、装扮等
# liqi用于解析雀魂消息
liqi:
  auto_update: false  # 是否自动更新
"""

yaml = YAML()
SETTINGS = yaml.load(DEFAULT_CONFIG)

CONFIG_FILE_PATH = './mjmax/config/settings.yaml'

try:
    with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
        SETTINGS.update(yaml.load(f))
except Exception as e:
    LOGGER.error("加载皮肤插件配置异常,使用默认配置", e, exc_info=True)

if SETTINGS['liqi']['auto_update']:
    LOGGER.info('正在检测liqi文件更新，请稍候……')
    try:
        SETTINGS['liqi']['liqi_version'] = update_liqi.update(SETTINGS['liqi']['liqi_version'])
    except Exception as e:
        LOGGER.error('liqi文件更新失败！可能会导致部分消息无法解析！', e, exc_info=True)

with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
    yaml.dump(SETTINGS, f)

MOD_ENABLE = SETTINGS['plugin_enable']['mod']
LOGGER.info(
    f'''已载入配置：\n
    启用mod: {MOD_ENABLE}
    ''')
if MOD_ENABLE:
    mod_plugin = mod.mod(VERSION)
liqi_proto = liqi.LiqiProto()


class ModAddon:
    def websocket_message(self, flow: http.HTTPFlow):
        # 在捕获到WebSocket消息时触发
        assert flow.websocket is not None  # make type checker happy
        message = flow.websocket.messages[-1]
        # 不解析ob消息
        if flow.request.path == '/ob':
            if message.from_client is False:
                LOGGER.debug(f'接收到（未解析）：{message.content}')
            else:
                LOGGER.debug(f'已发送（未解析）：{message.content}')
            return
        # 解析proto消息
        if MOD_ENABLE:
            # 如果启用mod，就把消息丢进mod里
            if not message.injected:
                modify, drop, msg, inject, inject_msg = mod_plugin.main(message, liqi_proto)
                if drop:
                    message.drop()
                if inject:
                    ctx.master.commands.call(
                        "inject.websocket", flow, True, inject_msg, False)
                if modify:
                    # 如果被mod修改就同步变更
                    message.content = msg
        try:
            result = liqi_proto.parse(message)
        except Exception as e:
            if message.from_client is False:
                LOGGER.error(f'接收到(error):{message.content}', e, exc_info=True)
            else:
                LOGGER.error(f'已发送(error):{message.content}')
        else:
            if message.from_client is False:
                if message.injected:
                    LOGGER.success(f'接收到(injected)：{result}')
                elif MOD_ENABLE and modify:
                    LOGGER.success(f'接收到(modify)：{result}')
                elif MOD_ENABLE and drop:
                    LOGGER.success(f'接收到(drop)：{result}')
                else:
                    LOGGER.info(f'接收到：{result}')
            else:
                if MOD_ENABLE and modify:
                    LOGGER.success(f'已发送(modify)：{result}')
                else:
                    LOGGER.info(f'已发送：{result}')
