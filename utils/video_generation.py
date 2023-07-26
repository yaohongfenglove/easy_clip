import math
import os
import random
from typing import List

import cv2
from PIL import Image
from moviepy.audio.fx.audio_fadeout import audio_fadeout
from moviepy.audio.AudioClip import concatenate_audioclips, CompositeAudioClip
from moviepy.audio.fx.audio_loop import audio_loop
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.editor import ImageClip
from moviepy.video.VideoClip import TextClip, VideoClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.compositing.transitions import crossfadein
from moviepy.video.fx.resize import resize
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.tools.subtitles import SubtitlesClip

import conf
from conf.config import logger, config, BASE_DIR
from utils.audio_generation import Subtitle


def get_file_type(file_path: str) -> str:
    """
    获取文件类型
    :param file_path:文件全路径
    :return:
    """
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    video_extensions = ['.mp4', '.avi', '.mov']

    file_extension = os.path.splitext(file_path)[-1].lower()

    if file_extension in image_extensions:
        return 'image'
    elif file_extension in video_extensions:
        return 'video'
    else:
        return 'unknown'


def is_vertical_material(file_path: str) -> bool:
    """
    判断是否竖向素材。
    是则返回True，否则False
    :param file_path: 文件的全路径
    :return:
    """
    file_type = get_file_type(file_path)
    if file_type == "image":
        img = Image.open(file_path)
        width, height = img.size
    elif file_type == "video":
        cap = cv2.VideoCapture(file_path)
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    else:
        raise ValueError("不支持的文件类型")
    return height > width


def combining_video(video_path_list: List[str], audio_path_list: List[str], subtitle_path_list: List[str],
                    cover_path: str, bgm_path: str, video_output_path: str):
    """
    连接视频合成最终视频
    :param video_path_list: 视频片段路径列表
    :param audio_path_list: 音频片段路径列表
    :param subtitle_path_list: 字幕路径列表
    :param cover_path: 封面路径
    :param bgm_path: 背景音乐路径
    :param video_output_path: 视频输出路径
    :return:
    """
    # 合成视频
    video_clips = [VideoFileClip(video_path) for video_path in video_path_list]
    audio_clips = [AudioFileClip(audio_path) for audio_path in audio_path_list]
    video_clip = concatenate_videoclips(video_clips, method="compose")
    voice_clip = concatenate_audioclips(audio_clips)

    video_clip = video_clip.without_audio()

    # 加封面
    cover_image_clip = ImageClip(cover_path).set_duration(video_clip.duration)
    cover_image_clip = resize(cover_image_clip,
                              width=config["compose_params"]["background_width"],
                              height=config["compose_params"]["background_height"])
    final_clip = CompositeVideoClip([video_clip, cover_image_clip])

    # 添加人声和bgm
    bgm_clip = AudioFileClip(bgm_path).set_duration(video_clip.duration)
    bgm_clip = audio_loop(bgm_clip, duration=video_clip.duration)
    bgm_clip = bgm_clip.volumex(config["compose_params"]["bgm_volume"])
    bgm_clip = audio_fadeout(bgm_clip, config["compose_params"]["bgm_fadeout_duration"])

    final_audio_clip = CompositeAudioClip([voice_clip, bgm_clip])
    final_clip = final_clip.set_audio(final_audio_clip)

    # 保存合成的视频
    final_clip.write_videofile(filename=video_output_path, fps=30, audio_codec="aac", codec="mpeg4",
                               bitrate='10000k', threads=os.cpu_count(), audio_bufsize=1000)  # 尝试解决末尾的音频重复问题 https://github.com/Zulko/moviepy/issues/1310
    final_clip.close()


def combining_video_within_cross_fade(clips: List[VideoClip],
                                      cross_fade_duration: float = config["compose_params"]["cross_fade_duration"]) -> VideoClip:
    """
    以交叉淡化(叠化转场)的方式组合视频
    :param clips: 视频片段
    :param cross_fade_duration: 交叉淡化时长
    :return:
    """

    clips_new = list()
    current_duration = 0
    for index, clip in enumerate(clips):
        if index == 0:
            clips_new.append(clip)
            current_duration += clip.duration
        else:
            clip: VideoClip = crossfadein(clip, cross_fade_duration)
            clips_new.append(clip.set_start(current_duration-cross_fade_duration))
            current_duration += (clip.duration - cross_fade_duration)

    final_clip = CompositeVideoClip(clips_new)

    return final_clip


def generate_video(subtitle: Subtitle, audio_path: str, subtitle_path: str, video_output_path: str,
                   material_direction: str, cross_fade_duration: float = config["compose_params"]["cross_fade_duration"]) -> VideoClip:
    """
    生成视频
    :param cross_fade_duration: 转场时间
    :param subtitle: 字幕对象
    :param audio_path: 音频文件路径
    :param subtitle_path: 字幕文件路径
    :param material_direction: 素材方向
    :param video_output_path: 视频输出路径
    :return:
    """

    # 获取视频画面素材
    if subtitle_path not in conf.config.medias_used.keys():
        media_path = os.path.join(config["compose_params"]["media_root_path"], subtitle.metadata["media_path"])

        medias = list()
        for filename in os.listdir(media_path):
            file_path = os.path.join(media_path, filename)

            if filename.startswith(('.', 'Thumbs.db')):
                continue

            if material_direction == "vertical" and is_vertical_material(str(file_path)):
                medias.append(file_path)
            elif material_direction == "horizontal" and not is_vertical_material(str(file_path)):
                medias.append(file_path)

        conf.config.medias_used[f"{subtitle_path}"] = medias

    video_final_duration = AudioFileClip(audio_path).duration  # 视频的最终时长
    video_current_duration = 0  # 视频的当前时长
    video_left_duration = video_final_duration  # 时间轴剩余时长
    video_clips: List[ImageClip, VideoFileClip] = list()

    i = 1
    while conf.config.medias_used[f"{subtitle_path}"]:
        media_path = random.choice(conf.config.medias_used[f"{subtitle_path}"])

        media_type = get_file_type(file_path=media_path)

        if media_type == "image":
            conf.config.medias_used[f"{subtitle_path}"].remove(media_path)

            if i == 1:
                image_duration = random.uniform(config["compose_params"]["image_duration"]["min"],
                                                config["compose_params"]["image_duration"]["max"])
            else:
                image_duration = random.uniform(
                    config["compose_params"]["image_duration"]["min"] + cross_fade_duration,
                    config["compose_params"]["image_duration"]["max"] + cross_fade_duration)

            image_clip = ImageClip(media_path).set_duration(min(video_left_duration, image_duration))
            if material_direction == "horizontal":
                image_clip = resize(clip=image_clip, width=config["compose_params"]["horizontal_material_width"],
                                    height=config["compose_params"]["horizontal_material_height"])
            else:
                image_clip = resize(clip=image_clip, width=config["compose_params"]["background_width"],
                                    height=config["compose_params"]["background_height"])

            video_clips.append(image_clip)
            if i == 1:
                video_current_duration += image_clip.duration
            else:
                video_current_duration += (image_clip.duration - cross_fade_duration)
            video_left_duration = video_final_duration - video_current_duration
            i += 1

            logger.info(
                f"当前时长：{video_current_duration} 剩余时长:：{video_left_duration} 最终时长：{video_final_duration}")

            # 这里不能用等于0来判断时间轴是否已经填满，因为浮点数计算时会有误差，差值可能会是一个无限接近0的数，所以这里用0.01近似表示相等。
            if abs(video_final_duration - video_current_duration) < 0.01:
                break
        elif media_type == "video":
            if media_path not in conf.config.video_cut_points.keys():
                conf.config.video_cut_points[f"{media_path}"] = 0

            video_clip = VideoFileClip(media_path)
            if i == 1:
                if (video_clip.duration - conf.config.video_cut_points[f"{media_path}"]) <= video_left_duration:
                    conf.config.medias_used.get(f"{subtitle_path}").remove(media_path)
                    t_start = conf.config.video_cut_points[f"{media_path}"]
                    t_end = video_clip.duration
                    video_clip = video_clip.subclip(t_start, t_end)
                else:
                    t_start = conf.config.video_cut_points[f"{media_path}"]
                    t_end = conf.config.video_cut_points[f"{media_path}"] + video_left_duration
                    video_clip = video_clip.subclip(t_start, t_end)
                    conf.config.video_cut_points[f"{media_path}"] = conf.config.video_cut_points[f"{media_path}"] + video_left_duration

                if material_direction == "horizontal":
                    video_clip = resize(clip=video_clip, width=config["compose_params"]["horizontal_material_width"],
                                        height=config["compose_params"]["horizontal_material_height"])
                else:
                    video_clip = resize(clip=video_clip, width=config["compose_params"]["background_width"],
                                        height=config["compose_params"]["background_height"])

                video_clips.append(video_clip)
                video_current_duration += video_clip.duration
                video_left_duration = video_final_duration - video_current_duration
                i += 1

                logger.info(
                        f"当前时长：{video_current_duration} 剩余时长:：{video_left_duration} 最终时长：{video_final_duration}")
                if abs(video_final_duration - video_current_duration) < 0.01:
                    break
            else:
                if (video_clip.duration - conf.config.video_cut_points[f"{media_path}"] - cross_fade_duration) <= video_left_duration:
                    t_start = conf.config.video_cut_points[f"{media_path}"]
                    t_end = video_clip.duration
                    video_clip = video_clip.subclip(t_start, t_end)

                    if material_direction == "horizontal":
                        video_clip = resize(clip=video_clip, width=config["compose_params"]["horizontal_material_width"],
                                            height=config["compose_params"]["horizontal_material_height"])
                    else:
                        video_clip = resize(clip=video_clip,
                                            width=config["compose_params"]["background_width"],
                                            height=config["compose_params"]["background_height"])

                    conf.config.medias_used.get(f"{subtitle_path}").remove(media_path)
                    video_clips.append(video_clip)
                    video_current_duration += (video_clip.duration - cross_fade_duration)
                    video_left_duration = video_final_duration - video_current_duration
                    i += 1

                    logger.info(
                        f"当前时长：{video_current_duration} 剩余时长:：{video_left_duration} 最终时长：{video_final_duration}")
                    if abs(video_final_duration - video_current_duration) < 0.01:
                        break
                else:
                    t_start = conf.config.video_cut_points[f"{media_path}"]
                    t_end = conf.config.video_cut_points[f"{media_path}"] + video_left_duration + cross_fade_duration
                    video_clip = video_clip.subclip(t_start, t_end)

                    if material_direction == "horizontal":
                        video_clip = resize(clip=video_clip, width=config["compose_params"]["horizontal_material_width"],
                                            height=config["compose_params"]["horizontal_material_height"])
                    else:
                        video_clip = resize(clip=video_clip,
                                            width=config["compose_params"]["background_width"],
                                            height=config["compose_params"]["background_height"])

                    conf.config.video_cut_points[f"{media_path}"] = conf.config.video_cut_points[
                                                            f"{media_path}"] + video_left_duration + cross_fade_duration

                    video_clips.append(video_clip)
                    video_current_duration += (video_clip.duration - cross_fade_duration)
                    video_left_duration = video_final_duration - video_current_duration
                    i += 1

                    logger.info(
                        f"当前时长：{video_current_duration} 剩余时长:：{video_left_duration} 最终时长：{video_final_duration}")
                    if abs(video_final_duration - video_current_duration) < 0.01:
                        break
        else:
            raise ValueError(f"不支持该类型的媒体文件：{media_path}")

    # 合成视频
    video_clip = combining_video_within_cross_fade(video_clips, cross_fade_duration=cross_fade_duration)

    # 合成字幕
    subtitles = SubtitlesClip(
        subtitle_path,
        lambda txt: TextClip(txt, font=f"{config['compose_params']['subtitles']['font_filename']}",
                             fontsize=config["compose_params"]["subtitles"]["fontsize"], color=config["compose_params"]["subtitles"]["color"],
                             stroke_color=config["compose_params"]["subtitles"]["stroke_color"],
                             stroke_width=config["compose_params"]["subtitles"]["stroke_width"])
    )

    video_clip = CompositeVideoClip(
        clips=[
            video_clip.set_position(("center", "center")),
            subtitles.set_position(("center", "bottom")).margin(bottom=config["compose_params"]["subtitles"]["margin"]["bottom"], opacity=0)
        ],
        size=(config["compose_params"]["background_width"], config["compose_params"]["background_height"])
    )

    # 添加音频
    audio_clip = AudioFileClip(audio_path)
    video_clip = video_clip.set_audio(audio_clip)

    # 保存合成的视频
    video_clip.write_videofile(filename=video_output_path, fps=30, audio_codec="aac", codec="mpeg4",
                               bitrate='10000k', threads=os.cpu_count(), audio_bufsize=1000)
    video_clip.close()

    return video_clip


def main():
    # 交叉淡化
    clip1 = ImageClip(os.path.join(BASE_DIR, "example/1.jpg")).set_duration(3)
    clip2 = ImageClip(os.path.join(BASE_DIR, "example/2.jpg")).set_duration(3)

    clip1 = resize(clip1, width=1080, height=math.floor(1080/(1920/1080)))
    clip2 = resize(clip2, width=1080, height=math.floor(1080/(1920/1080)))

    final_clip = combining_video_within_cross_fade(clips=[clip1, clip2], cross_fade_duration=1)

    video_output_path = os.path.join(BASE_DIR, f"output/cross_fade.mp4")
    final_clip.write_videofile(filename=video_output_path, fps=30, audio_codec="aac", codec="mpeg4",
                               bitrate='10000k', threads=os.cpu_count(), audio_bufsize=1000)
    final_clip.close()


if __name__ == '__main__':
    main()
