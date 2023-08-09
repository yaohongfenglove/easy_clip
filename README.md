# 简介

> 高效剪辑工具

### 示例视频：

[示例1](https://gitee.com/yao-hongfeng/videos/raw/master/示例1.mp4)

[示例2](https://gitee.com/yao-hongfeng/videos/raw/master/示例2.mp4)

[不透明度变换](https://gitee.com/yao-hongfeng/videos/raw/master/不透明度变换.mp4)

[位置变换](https://gitee.com/yao-hongfeng/videos/raw/master/位置变换.mp4)

[旋转变换](https://gitee.com/yao-hongfeng/videos/raw/master/旋转变换.mp4)

[大小变换](https://gitee.com/yao-hongfeng/videos/raw/master/大小变换.mp4)

# 快速开始

### 一.运行环境

支持各主流操作系统

先安装 `Python`
> 建议Python版本3.8.x，尤其是需要进行exe打包时（3.8为win7上可运行的最后一个python版本）。

创建虚拟环境后，安装所需核心依赖：

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 二.相关配置
```bash
远程媒体路径: \\192.168.100.199\video_share
```

```bash
视频脚本结构: 视频脚本文件-template.xlsx
```

```bash
配置文件config.json内容示例
{
    "environment": "debug",  # 开发、测试、正式环境
    "SUPPORTED_VOICES": {  # 配音人
        "1": "zh-CN-XiaoxiaoNeural",  # 推荐
        "2": "zh-CN-XiaoyiNeural",
        "3": "zh-CN-YunjianNeural",  # 推荐
        "4": "zh-CN-YunxiNeural",  # 推荐
        "5": "zh-CN-YunxiaNeural",
        "6": "zh-CN-YunyangNeural",  # 推荐
        "7": "zh-CN-liaoning-XiaobeiNeural",
        "8": "zh-CN-shaanxi-XiaoniNeural",
        "9": "zh-HK-HiuGaaiNeural",
        "10": "zh-HK-HiuMaanNeural",
        "11": "zh-HK-WanLungNeural",
        "12": "zh-TW-HsiaoChenNeural",
        "13": "zh-TW-HsiaoYuNeural",
        "14": "zh-TW-YunJheNeural"
    },
    "compose_params": {  # 音视频合成参数
        "media_root_path": "D:/data/program/easy_clip/media",  # 媒体素材根路径
        "videos_per_subtitles": 20,  # 每个字幕合成几个视频
        "subtitle_length_limit": 15,  # 字幕长度限制
        "background_width": 1080,  # 背景素材的宽
        "background_height": 1920,  # 背景素材的高
        "horizontal_material_width": 1080,  # 横向素材的宽
        "horizontal_material_height": 608,  # 横向素材的高
        "cross_fade_duration": 0.5,  # 交叉淡化时长
        "bgm_volume": 0.3,  # 背景音乐音量百分比
        "bgm_target_dbfs_limit": -10,  # 背景音乐目标分贝值限制
        "bgm_fadeout_duration": 2,  # 背景音乐淡出时长
        "image_duration": {  # 图片时长限制
            "min": 1,
            "max": 1.5
        },
        "subtitles": {  # 字幕参数
            "font_filename": "SourceHanSansSC-Heavy.otf",  # ！！！注意：使用自定义字体时，字体文件必须
                                                           # 放在main.py这个启动文件的同级目录，否则字体文件可能读取不到，导致异常。
            "fontsize": 50,
            "color": "white",
            "stroke_color": "black",  # 字幕内描边的颜色
            "stroke_width": 3,  # 字幕内描边的宽度
            "margin": {  
                "bottom": 676  # 字幕的下边距
            }
        }
    }
}
```

### 三.运行
**本地运行，** 直接在项目根目录下执行：
```bash
python main.py
```
