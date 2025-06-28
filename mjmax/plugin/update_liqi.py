import requests
from common.log_helper import LOGGER


def get_version():
    req = requests.get('https://game.maj-soul.com/1/version.json', timeout=10)
    return req.json()['version']


def get_prefix(version):
    req = requests.get(f'https://game.maj-soul.com/1/resversion{version}.json', timeout=10)
    return req.json()['res']['res/proto/liqi.json']['prefix']


def update(version):
    new_version = 'v' + get_version()
    if new_version == version:
        LOGGER.info(f'liqi文件无需更新，当前版本：{new_version}')
        return new_version
    else:
        req = requests.get(f'https://api.github.com/repos/Avenshy/AutoLiqi/releases/latest', timeout=10)
        if req.headers['X-RateLimit-Remaining'] == '0':
            LOGGER.error("无法更新liqi文件,请稍后再试")
            return version
        liqi = req.json()
        if liqi['tag_name'][:len(new_version)] != new_version:
            LOGGER.error('liqi文件需要更新，但AutoLiqi项目还未更新，晚点再来试试吧！')
            LOGGER.error('详细信息请看 https://github.com/Avenshy/AutoLiqi')
            return version
        else:
            for item in liqi['assets']:
                match item['name']:
                    case 'liqi.json' | 'liqi.proto' | 'liqi_pb2.py':
                        LOGGER.info(f'下载 {item["name"]} 中……')
                        req = requests.get(item['browser_download_url'], timeout=10)
                        with open(f'./mjmax/proto/{item["name"]}', 'w') as f:
                            f.write(req.text)
                        LOGGER.info(f'下载 {item["name"]} 成功！')
            LOGGER.info(f'liqi文件更新成功：{new_version}')
            return new_version
