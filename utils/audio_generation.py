import asyncio
import random
import re
import textwrap
from typing import List, Tuple, Dict

import edge_tts

from conf.config import config, logger


class Subtitle(object):
    def __init__(self, text: str, metadata: Dict = None):
        """
        初始化字幕类，带元数据
        :param text: 字幕文本
        :param metadata: 元数据，例如{"media_path": "...", ...}
        """
        self.text = text
        self.metadata = metadata


def vtt_file_to_subtitles(file_path: str):
    """
    Converts a .vvt file into .srt subtitles.
    Only works for '.vvt' format for the moment.
    :param file_path: .vtt文件全路径
    :return:
    """
    times_texts = []
    current_times = None
    current_text = ""
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            times = re.findall("([0-9]*:[0-9]*:[0-9]*.[0-9]*)", line)
            if times:
                current_times = [t.replace('.', ',') for t in times]
            elif line.strip() == '':
                pass
            elif current_times:
                current_text = line
                times_texts.append((current_times, current_text.strip('\n')))
                current_times = None
                current_text = ""
    return times_texts


def split_text(text: str, max_len: int = 15) -> List[str]:
    """
    分割文本
    :param text: 待分割的文本
    :param max_len:分割后句子最大长度限制
    :return:
    """

    separators: List[str] = ["。", "，", "？", "！"]  # 分割符集合

    pattern = '|'.join(separators)
    sentences = re.split(pattern=pattern, string=text)

    # 太长的句子也拆开
    results = list()
    for sentence in sentences:
        if not sentence:  # 删除空字符串
            continue

        if len(sentence) > max_len:
            # results.extend([sentence[i:i + max_len] for i in range(0, len(sentence), max_len)])
            sentence = textwrap.fill(text=sentence, width=max_len)
            results.append(sentence)
        else:
            results.append(sentence)

    return results


def remove_punctuation(sentence):
    # 删除标点符号和空格
    sentence = re.sub(r'\W', '', sentence)
    return sentence


def format_subtitle_file(text, subtitle_input_path, subtitle_output_path):
    subtitle_sentence_list = split_text(text)
    subtitle_chunk_list = vtt_file_to_subtitles(subtitle_input_path)
    logger.info(f"字幕句子列表：{subtitle_sentence_list}")
    logger.info(f"字幕文本块列表：{subtitle_chunk_list}")

    # 以句子列表中的句子为基准，将文本块及时间轴合并
    results = list()
    for subtitle in subtitle_sentence_list:
        text = ''
        start_time = ''
        end_time = ''
        for index, chunk in enumerate(subtitle_chunk_list):
            if start_time == '':
                start_time = chunk[0][0]
            end_time = chunk[0][1]

            text += remove_punctuation(chunk[1])
            if text == remove_punctuation(subtitle):
                results.append(([start_time, end_time], subtitle))
                subtitle_chunk_list = subtitle_chunk_list[index+1:]
                break

    text_srt = ""
    for index, subtitle in enumerate(results):
        text_srt += f"{index+1}\n{subtitle[0][0]} --> {subtitle[0][1]}\n{subtitle[1]}\n\n"

    with open(subtitle_output_path, "w") as f:  # TODO 2023-7-17 encoding="utf-8"写入的话，因为moviepy的SubtitlesClip默认不以utf-8打开，会报错
        f.write(text_srt)


async def generate_audio(text: str, audio_output_path: str, subtitle_output_path: str) -> Tuple:
    """
    本生成音频文件
    :param text: 待转化为音频的文本
    :param audio_output_path: 音频输出的绝对路径，/xxx/xxx/xxx.mp3
    :param subtitle_output_path: 字幕输出的绝对路径，/xxx/xxx/xxx.srt
    :return:
    """
    subtitle_audio = random.choice(list(config["SUPPORTED_VOICES"].keys()))  # 随机选一个字幕配音
    communicate = edge_tts.Communicate(text, config["SUPPORTED_VOICES"][subtitle_audio])

    subtitle_maker = edge_tts.SubMaker()
    with open(audio_output_path, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                subtitle_maker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])

    with open(subtitle_output_path, "w", encoding="utf-8") as file:
        file.write(subtitle_maker.generate_subs(words_in_cue=1))

    format_subtitle_file(text, subtitle_output_path, subtitle_output_path)

    return audio_output_path, subtitle_output_path


def sync_generate_audios(text_list: List, audio_output_path_list: List, subtitle_output_path_list: List) -> None:
    """
    批量文本生成音频文件
    :param text_list: 待转化为音频的文本列表
    :param audio_output_path_list: 音频输出的绝对路径列表，[/xxx/xxx/xxx.mp3, /xxx/xxx/aaa.mp3, ...]
    :param subtitle_output_path_list: srt字幕输出的绝对路径列表，[/xxx/xxx/xxx.srt, /xxx/xxx/aaa.srt, ...]
    :return:
    """
    loop = asyncio.get_event_loop()

    try:
        if not loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        tasks = list()
        for i in range(len(text_list)):
            tasks.append((lambda: generate_audio(text_list[i], audio_output_path_list[i], subtitle_output_path_list[i]))())

        results = loop.run_until_complete(asyncio.gather(*tasks))
        for result in results:
            logger.info(f"生成路径：{result}")
    finally:
        loop.close()


def text2audio(text: str, audio_output_path: str, subtitle_output_path: str) -> None:
    """
    将文本转为音频
    :param text: 待转化的文本
    :param audio_output_path: 音频输出路径
    :param subtitle_output_path: srt字幕输出路径
    :return:
    """
    sync_generate_audios(
        text_list=[text, ],
        audio_output_path_list=[audio_output_path, ],
        subtitle_output_path_list=[subtitle_output_path, ]
    )


def main():
    pass


if __name__ == "__main__":
    main()
