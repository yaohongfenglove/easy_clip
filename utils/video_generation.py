import math
import os
import random
from typing import List

from moviepy.audio.AudioClip import concatenate_audioclips
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.editor import ImageClip
from moviepy.video.VideoClip import TextClip, VideoClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.compositing.transitions import crossfadein
from moviepy.video.fx.resize import resize
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.tools.subtitles import SubtitlesClip

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

    file_extension = os.path.splitext(file_path)[-1]

    if file_extension in image_extensions:
        return 'image'
    elif file_extension in video_extensions:
        return 'video'
    else:
        return 'unknown'


def combining_video(video_path_list: List[str], audio_path_list: List[str], subtitle_path_list: List[str],
                    cover_path: str, video_output_path: str):
    """
    连接视频合成最终视频
    :param video_path_list: 视频片段路径列表
    :param audio_path_list: 音频片段路径列表
    :param subtitle_path_list: 字幕路径列表
    :param cover_path: 封面路径
    :param video_output_path: 视频输出路径
    :return:
    """
    # 合成视频
    video_clips = [VideoFileClip(video_path) for video_path in video_path_list]
    audio_clips = [AudioFileClip(audio_path) for audio_path in audio_path_list]
    video_clip = concatenate_videoclips(video_clips, method="compose")
    audio_clip = concatenate_audioclips(audio_clips)

    video_clip = video_clip.without_audio()
    video_clip = video_clip.set_audio(audio_clip)
    video_clip = resize(video_clip, width=1080, height=math.floor(1080/(1920/1080)))

    # 加封面
    background_clip = ImageClip(cover_path).set_duration(video_clip.duration)
    background_clip = resize(background_clip, width=1080, height=1920)

    final_clip = CompositeVideoClip([background_clip, video_clip.set_position("center")])

    # 保存合成的视频
    final_clip.write_videofile(filename=video_output_path, fps=30, audio_codec="aac", codec="mpeg4",
                               bitrate='10000k', threads=os.cpu_count())
    final_clip.close()


def combining_video_within_cross_fade(clips: List[VideoClip], cross_fade_duration: float = 0.5) -> VideoClip:
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


def generate_video(subtitle: Subtitle, audio_path: str, subtitle_path: str, video_output_path: str) -> VideoClip:
    """
    生成视频
    :param subtitle: 字幕
    :param audio_path:
    :param subtitle_path:
    :param video_output_path:
    :return:
    """

    # 获取视频画面素材
    media_path = os.path.join(config["media_root_path"], subtitle.metadata["media_path"])
    medias = [os.path.join(media_path, filename) for filename in os.listdir(media_path)]

    video_final_duration = AudioFileClip(audio_path).duration  # 视频的最终时长
    video_current_duration = 0  # 视频的当前时长
    video_clips: List[ImageClip, VideoFileClip] = list()

    while medias:
        media_path = random.choice(medias)
        medias.remove(media_path)

        media_type = get_file_type(file_path=media_path)
        if media_type == "image":
            image_clip = ImageClip(media_path).set_duration(3)
            image_clip = resize(clip=image_clip, width=1920, height=1080)
            video_clip = image_clip
        elif media_type == "video":
            video_clip = VideoFileClip(media_path).subclip(0, 3)
            video_clip = resize(clip=video_clip, width=1920, height=1080)
        else:
            raise ValueError(f"不支持该类型的媒体文件：{media_path}")

        video_left_duration = video_final_duration - (video_current_duration + video_clip.duration)  # 时间轴剩余时长
        if video_left_duration > 2:  # 没有超时间轴，且时间轴还剩很长。直接添加
            duration = video_clip.duration
            video_current_duration += duration
            video_clips.append(video_clip)
        elif 0 <= video_left_duration < 2:  # 没有超时间轴，但时间轴只剩一点点了。是图片则拉长一点，是视频则继续
            if isinstance(video_clip, ImageClip):
                duration = video_clip.duration + abs(video_left_duration)
                video_clip.set_duration(duration)
                video_clip = video_clip.set_duration(duration)
                video_current_duration += duration
                video_clips.append(video_clip)
            elif isinstance(video_clip, VideoFileClip):
                continue
        elif -2 < video_left_duration < 0:  # 超时间轴不多。截断一点
            duration = video_clip.duration - abs(video_left_duration)
            if isinstance(video_clip, ImageClip):
                video_clip.set_duration(duration)
            elif isinstance(video_clip, VideoFileClip):
                video_clip = video_clip.subclip(0, duration)
            video_current_duration += duration
            video_clips.append(video_clip)
        else:  # 超时间轴太多。继续
            continue
        logger.info(f"当前时长：{video_current_duration} 最终时长：{video_final_duration}")

        if video_current_duration == video_final_duration:
            break

    if video_current_duration < video_final_duration:
        raise ValueError(f"素材不够")

    # 合成视频
    video_clip = concatenate_videoclips(video_clips, method="compose")

    # 添加字幕
    subtitles = SubtitlesClip(
        subtitle_path,
        lambda txt: TextClip(txt, font='SimHei', color='white', fontsize=100)
    )
    subtitles = subtitles.set_position(("center", "bottom"))
    video_clip = CompositeVideoClip([video_clip, subtitles])

    # 添加音频
    audio_clip = AudioFileClip(audio_path)
    video_clip = video_clip.set_audio(audio_clip)

    # 保存合成的视频
    video_clip.write_videofile(filename=video_output_path, fps=30, audio_codec="aac", codec="mpeg4",
                               bitrate='10000k', threads=os.cpu_count())
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
                               bitrate='10000k', threads=os.cpu_count())
    final_clip.close()


if __name__ == '__main__':
    main()
