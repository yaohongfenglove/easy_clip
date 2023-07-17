import os

from moviepy.audio.AudioClip import concatenate_audioclips
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.editor import ImageClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.fx.resize import resize
from moviepy.video.tools.subtitles import SubtitlesClip

from conf.config import BASE_DIR


def generate_video(audio_path: str, subtitle_path: str, video_output_path: str):
    """
    生成视频
    """

    image_clip1 = ImageClip(os.path.join(BASE_DIR, "media/image/1.jpg")).set_duration(30)
    image_clip1 = resize(clip=image_clip1, width=1920, height=1080)

    # 合成视频
    video_clip = concatenate_videoclips([image_clip1, ])

    # 添加字幕
    subtitles = SubtitlesClip(
        subtitle_path,
        lambda txt: TextClip(txt, font='SimHei', color='white', fontsize=100)
    )
    subtitles = subtitles.set_position(("center", "bottom"))
    video_clip = CompositeVideoClip([video_clip, subtitles])

    # 添加音频
    audio_clip = AudioFileClip(audio_path)
    composite_audio = concatenate_audioclips([audio_clip, ])
    video_clip = video_clip.set_audio(composite_audio)

    # 保存合成的视频
    video_clip.write_videofile(filename=video_output_path, fps=30, audio_codec="aac")
    video_clip.close()


def main():
    pass


if __name__ == '__main__':
    main()
