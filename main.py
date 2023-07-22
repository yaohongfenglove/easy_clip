import datetime
import itertools
import os.path
import random
from typing import List

import pandas

try:
    from conf.config import BASE_DIR, config, logger
    from utils.audio_generation import text2audio, Subtitle
    from utils.video_generation import generate_video, combining_video
except ModuleNotFoundError:
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # 离开IDE也能正常导入自己定义的包
    from conf.config import BASE_DIR, config, logger
    from utils.audio_generation import text2audio, Subtitle
    from utils.video_generation import generate_video, combining_video


def get_subtitles_list(subtitles: List):
    """
    获取字幕的组合列表
    首段和尾段固定，中间的段进行全排列
    :param subtitles: 原始字幕
    :return:
    """
    first_paragraph = subtitles[0]
    middle_paragraphs = subtitles[1:-1]
    last_paragraph = subtitles[-1]

    permutations = itertools.permutations(middle_paragraphs, len(middle_paragraphs))
    permutations = [list(p) for p in permutations]

    text_list = list()
    for permutation in permutations:
        text_list.append([first_paragraph] + permutation + [last_paragraph])

    return text_list


def subtitles2video(video_script_path: str, shuffle_subtitles: bool = False):
    """
    字幕文件转视频文件
    :param video_script_path: 视频脚本文件的路径，.xlsx文件
    :param shuffle_subtitles: 是否要打乱字幕顺序
    :return:
    """

    # 读取视频脚本文件
    rows = pandas.read_excel(video_script_path, header=0)
    rows = list(rows.values)

    subtitles = [Subtitle(text=row[0], metadata={"media_path": row[1]}) for row in rows]

    # 封面路径
    cover_path = os.path.join(config["media_root_path"], rows[0][2])
    cover_path = random.choice(
        [os.path.join(cover_path, filename) for filename in os.listdir(cover_path) if not filename.startswith('.')])
    logger.info(f"选择的封面：{cover_path}")

    # BGM路径
    bgm_path = os.path.join(config["media_root_path"], rows[0][3])
    bgm_path = random.choice(
        [os.path.join(bgm_path, filename) for filename in os.listdir(bgm_path) if not filename.startswith('.')])
    logger.info(f"选择的bgm：{bgm_path}")

    if shuffle_subtitles:
        subtitles_list = get_subtitles_list(subtitles)
    else:
        subtitles_list = [subtitles, ]

    for subtitles in subtitles_list:
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        os.makedirs(os.path.join(BASE_DIR, f"output/{now}"))  # 文件输出路径

        # 随机选一个字幕配音人
        subtitle_voice = config["SUPPORTED_VOICES"][random.choice(list(config["SUPPORTED_VOICES"].keys()))]
        logger.info(f"选择的字幕配音人：{subtitle_voice}")

        video_path_list = list()
        audio_path_list = list()
        subtitle_path_list = list()
        for index, subtitle in enumerate(subtitles):
            # 生成音频（附带字幕文件）
            audio_output_path = os.path.join(BASE_DIR, f"output/{now}/{index+1}.mp3")
            subtitle_output_path = os.path.join(BASE_DIR, f"output/{now}/{index+1}.srt")
            audio_path_list.append(audio_output_path)
            subtitle_path_list.append(subtitle_output_path)
            text2audio(text=subtitle.text, subtitle_voice=subtitle_voice, audio_output_path=audio_output_path,
                       subtitle_output_path=subtitle_output_path)
            # 生成视频文件
            video_output_path = os.path.join(BASE_DIR, f"output/{now}/{index+1}.mp4")
            video_path_list.append(video_output_path)
            generate_video(subtitle=subtitle, audio_path=audio_output_path, subtitle_path=subtitle_output_path,
                           video_output_path=video_output_path)

        # 组合片段，生成最终视频
        video_output_final_path = os.path.join(BASE_DIR, f"output/{now}/{now}.mp4")
        combining_video(video_path_list=video_path_list, audio_path_list=audio_path_list, subtitle_path_list=subtitle_path_list,
                        cover_path=cover_path, bgm_path=bgm_path,
                        video_output_path=video_output_final_path)


def main():
    video_script_path = os.path.join(BASE_DIR, '视频脚本文件.xlsx')
    videos_per_subtitles = config["videos_per_subtitles"]  # 一个字幕要生成几个视频

    for i in range(videos_per_subtitles):
        subtitles2video(
            video_script_path=video_script_path,
            shuffle_subtitles=False
        )


if __name__ == '__main__':
    main()
