import datetime
import itertools
import os.path
import random
from typing import List

import pandas

from conf.config import BASE_DIR, config
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


def main():
    # 读取视频脚本文件
    rows = pandas.read_excel(os.path.join(BASE_DIR, '视频脚本文件.xlsx'), header=0)
    rows = list(rows.values)

    subtitles = [Subtitle(text=row[0], metadata={"media_path": row[1], "cover_path": row[2]}) for row in rows]

    # 封面路径
    cover_path = os.path.join(config["media_root_path"], subtitles[0].metadata["cover_path"])
    cover_path = random.choice([os.path.join(cover_path, filename) for filename in os.listdir(cover_path)])

    subtitles_list = get_subtitles_list(subtitles)

    for subtitles in subtitles_list:
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        os.makedirs(os.path.join(BASE_DIR, f"output/{now}"))  # 文件输出路径

        video_path_list = list()
        audio_path_list = list()
        subtitle_path_list = list()
        for index, subtitle in enumerate(subtitles):
            # 生成音频（附带字幕文件）
            audio_output_path = os.path.join(BASE_DIR, f"output/{now}/{index+1}.mp3")
            subtitle_output_path = os.path.join(BASE_DIR, f"output/{now}/{index+1}.srt")
            audio_path_list.append(audio_output_path)
            subtitle_path_list.append(subtitle_output_path)
            text2audio(text=subtitle.text, audio_output_path=audio_output_path,
                       subtitle_output_path=subtitle_output_path)
            # 生成视频文件
            video_output_path = os.path.join(BASE_DIR, f"output/{now}/{index+1}.mp4")
            video_path_list.append(video_output_path)
            generate_video(subtitle=subtitle, audio_path=audio_output_path, subtitle_path=subtitle_output_path,
                           video_output_path=video_output_path)

        # 组合片段，生成最终视频
        video_output_final_path = os.path.join(BASE_DIR, f"output/{now}/{now}.mp4")
        combining_video(video_path_list=video_path_list, audio_path_list=audio_path_list, subtitle_path_list=subtitle_path_list,
                        cover_path=cover_path,
                        video_output_path=video_output_final_path)


if __name__ == '__main__':
    main()
