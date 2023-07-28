import datetime
import itertools
import os.path
import pickle
import random
from typing import List, Dict

import pandas

try:
    import conf
    from conf.config import BASE_DIR, config, logger
    from utils.audio_generation import text2audio, Subtitle
    from utils.video_generation import generate_video, combining_video
except ModuleNotFoundError:
    import os
    import sys
    import conf
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
    cover_path = os.path.join(config["compose_params"]["media_root_path"], rows[0][2])
    cover_path = random.choice(
        [os.path.join(cover_path, filename) for filename in os.listdir(cover_path) if not filename.startswith(('.', 'Thumbs.db'))])
    logger.info(f"选择的封面：{cover_path}")

    # BGM路径
    bgm_path = os.path.join(config["compose_params"]["media_root_path"], rows[0][3])
    bgm_path = random.choice(
        [os.path.join(bgm_path, filename) for filename in os.listdir(bgm_path) if not filename.startswith(('.', 'Thumbs.db'))])
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

        # 封面决定取横向还是竖向的素材
        material_direction: str = "vertical" if "_vertical" in cover_path else "horizontal"

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
                           material_direction=material_direction, video_output_path=video_output_path)

        # 组合片段，生成最终视频
        video_output_final_path = os.path.join(BASE_DIR, f"output/{now}/{now}.mp4")
        combining_video(video_path_list=video_path_list, audio_path_list=audio_path_list, subtitle_path_list=subtitle_path_list,
                        cover_path=cover_path, bgm_path=bgm_path,
                        video_output_path=video_output_final_path)


def main():

    # 读取所有视频脚本文件
    video_script_path_list = [
        os.path.join(config["compose_params"]["media_root_path"], filename)
        for filename in os.listdir(config["compose_params"]["media_root_path"])
        if filename.endswith(('.xlsx', '.xls'))
    ]
    # 一个字幕要生成几个视频
    videos_per_subtitles = config["compose_params"]["videos_per_subtitles"]

    # 持久化处理：程序重启时先读取持久化文件，再进行任务处理
    persistent_file_path = os.path.join(BASE_DIR, f'output/{config["compose_params"]["media_root_path"]}.pkl'.replace('\\', ''))
    if not os.path.exists(persistent_file_path):
        logger.warning(f"新建持久化文件：{persistent_file_path}")
        with open(persistent_file_path, 'wb') as f:
            session: Dict = {
                "video_cut_points": dict(),
                "medias_used":  dict(),
                "success_tasks": list(),
            }
            pickle.dump(session, f)
        print(os.path.getsize(persistent_file_path))
    else:
        logger.warning(f"加载持久化文件：{persistent_file_path}")
        with open(persistent_file_path, 'rb') as f:
            session: Dict = pickle.load(f, encoding='bytes')
        logger.warning(f"持久化文件内容：{session}")

        res = input(f"本地已有持久化文件，是否继续【y/n】：")
        if res.lower() != 'y':
            return

        conf.config.video_cut_points = session.get("video_cut_points")
        conf.config.medias_used = session.get("medias_used")

    for video_script_path in video_script_path_list:
        for i in range(videos_per_subtitles):

            # 持久化处理：跳过已成功的任务
            task_name = f"{video_script_path}-{i+1}"
            if task_name in session["success_tasks"]:
                logger.info(f"跳过任务：{task_name}")
                continue

            logger.info(f"准备合成：{video_script_path} - 第{i+1}个/共{videos_per_subtitles}个")
            subtitles2video(
                video_script_path=video_script_path,
                shuffle_subtitles=False
            )

            # 持久化处理：成功的任务进行持久化
            logger.info(f"开始持久化任务：{task_name}")
            with open(persistent_file_path, 'rb') as f:
                session: Dict = pickle.load(f, encoding='bytes')
            with open(persistent_file_path, 'wb') as f:
                session["success_tasks"].append(task_name)
                session["video_cut_points"] = conf.config.video_cut_points
                session["medias_used"] = conf.config.medias_used
                pickle.dump(session, f)


if __name__ == '__main__':
    main()
