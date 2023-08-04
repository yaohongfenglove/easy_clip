import os
from typing import Tuple, List, Union

import numpy as np
from moviepy.video.VideoClip import ColorClip, VideoClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.fx.resize import resize
from moviepy.video.fx.rotate import rotate
from moviepy.video.io.VideoFileClip import VideoFileClip

from conf.config import BASE_DIR


def get_file_path_list(folder, extensions: Tuple = ('.mp4', '.avi', '.mov', '.mkv')) -> List[str]:
    """
    获取特定文件夹下的特定扩展名的文件
    :param folder: 待查找的文件夹
    :param extensions: 扩展名数组，比如：('.mp4', '.avi', '.mov', '.mkv')
    :return:
    """
    file_path_list = list()
    for dir_path, dirname_list, filename_list in os.walk(folder):
        for filename in filename_list:
            if filename.lower().endswith(extensions):
                file_path_list.append(os.path.join(dir_path, filename))

    return file_path_list


def add_key_frame_a2b(
        clip: VideoClip,
        t_start: Union[float, None] = None, t_end: Union[float, None] = None,
        position_start: Union[Tuple, None] = None, position_end: Union[Tuple, None] = None,
        rotate_start: Union[int, None] = None, rotate_end: Union[int, None] = None,
        size_start: Union[Tuple, None] = None, size_end: Union[Tuple, None] = None,
        opacity_start: Union[float, None] = None, opacity_end: Union[float, None] = None) -> VideoClip:
    """
    添加a至b的关键帧特效（目前是添加两帧，多帧可以用moviepy的fx链式调用）
    特别注意：本函数的if variable is not None不要用if variable这种写法，后者当variable为0，空字符串等时不符合逻辑要求

    Example of calculation for masks，
    After the Composite Video Clip, the masks are counted as one

              **********
              * .5 .5  *
              *        *
         ******        *
         * 1 1*   mask3*
         *    **********
    ******        *
    * 0 0*   mask2*
    *    **********
    *   mask1*
    **********

    :param clip: 视频剪辑
    :param t_start: 关键帧a的时间点，例：0.0
    :param t_end: 关键帧b的时间点，例：2.0
    :param opacity_start: 关键帧a的不透明度，范围0～1，0表示全透明，例：0.0
    :param opacity_end: 关键帧b的不透明度，范围0～1，0表示全透明，例：0.6
    :param position_start: 关键帧a的位置，例：(0, 0)
    :param position_end: 关键帧b的位置，例：(520, 520)
    :param rotate_start: 关键帧a的旋转角度，例：0
    :param rotate_end: 关键帧b的旋转角度，例：90
    :param size_start: 关键帧a的宽高，格式为(width, height)，例：(1080, 1920)
    :param size_end: 关键帧b的宽高，格式为(width, height)，例：(720, 1280)
    :return: 加了关键帧特效后的视频片段
    """

    # 对部分参数进行简单校验
    if clip is None:
        raise ValueError('视频不能为空')
    if all([opacity_start is not None, opacity_end is not None]):
        if not all([0 <= opacity_start <= 1, 0 <= opacity_end <= 1]):
            raise ValueError('透明度设置范围为0～1')
        if any([position_start, position_end, rotate_start, rotate_end, size_start, size_end]):
            raise ValueError("不透明度变换暂不支持与其他变换结合使用")

    # 如果没有遮罩需要添加遮罩，否则后续与其他视频使用CompositeVideoClip叠加后，画中画效果会有异常
    if clip.mask is None:
        clip = clip.add_mask()  # 遮罩全1

    # 用来保存加关键帧特效后的视频剪辑
    clip_add_effects: VideoClip = clip.subclip(t_start, t_end)

    # 透明剪辑
    color_clip = ColorClip(
        size=clip_add_effects.size,
        duration=clip_add_effects.duration,
        color=(0, 0, 0, 0)  # RGB通道 + α透明度通道  # 遮罩全0
    )

    # 不透明度变换
    if (opacity_start is not None) and (opacity_end is not None):
        step_opacity = (opacity_end - opacity_start) / (t_end - t_start)
        clip_add_effects.mask.get_frame = lambda t: np.full(shape=(clip_add_effects.h, clip_add_effects.w),
                                                            fill_value=opacity_start + step_opacity * t)  # 不能用shape=clip_add_effects.size，np与moviepy宽高相反

    # 位置变换
    if (position_start is not None) and (position_end is not None):
        step_x = (position_end[0] - position_start[0]) / (t_end - t_start)
        step_y = (position_end[1] - position_start[1]) / (t_end - t_start)
        clip_add_effects = clip_add_effects.set_position(
            lambda t: (position_start[0] + step_x * t, position_start[1] + step_y * t)
        )

    # 旋转变换
    if (rotate_start is not None) and (rotate_end is not None):
        step_angle = (rotate_end - rotate_start) / (t_end - t_start)
        clip_add_effects = rotate(clip=clip_add_effects, angle=lambda t: rotate_start + t * step_angle,
                                  expand=True)

    # 大小变换
    if (size_start is not None) and (size_end is not None):
        # 至少一个像素点大小，防止resize(clip=clip, newsize=(0, 0))报错
        width_min, height_min = (1, 1)

        width_start, height_start = size_start
        width_end, height_end = size_end

        step_width = (width_end - width_start) / (t_end - t_start)
        step_height = (height_end - height_start) / (t_end - t_start)

        clip_add_effects = resize(
            clip=clip_add_effects,
            newsize=lambda t: (max(width_min, int(width_start + t * step_width)), max(height_min, int(height_start + t * step_height))),
        )

    # 其他变换,待完善。比如音量的渐强渐弱
    pass

    # 叠加在透明剪辑上
    if (opacity_start is not None) and (opacity_end is not None):  # 透明变换时，不叠加color_clip，否则有半透明黑底
        pass
    else:
        clip_add_effects = CompositeVideoClip(clips=[color_clip, clip_add_effects])

    final_clip = concatenate_videoclips(
        clips=[clip.subclip(t_start=0, t_end=t_start),
               clip_add_effects,
               clip.subclip(t_start=t_end, t_end=clip.duration)]
    )

    return final_clip


def main():
    video_clip1: VideoClip = VideoFileClip(os.path.join(BASE_DIR, "example/1.mp4"))
    video_clip2: VideoClip = VideoFileClip(os.path.join(BASE_DIR, "example/2.mp4"))

    # 不透明度变换
    video_clip2 = add_key_frame_a2b(clip=video_clip2,
                                    t_start=2, t_end=video_clip2.duration,
                                    opacity_start=1, opacity_end=0)

    # # 位置变换
    # video_clip2 = add_key_frame_a2b(clip=video_clip2,
    #                                 t_start=0, t_end=2,
    #                                 position_start=(0, video_clip2.h), position_end=(0, 0))

    # # 旋转变换
    # video_clip2 = add_key_frame_a2b(clip=video_clip2,
    #                                 t_start=1, t_end=video_clip2.duration,
    #                                 rotate_start=0, rotate_end=60)

    # # 大小变换
    # video_clip2 = add_key_frame_a2b(clip=video_clip2,
    #                                 t_start=0, t_end=2,
    #                                 size_start=(0, 0), size_end=video_clip2.size)

    video_clip: VideoClip = CompositeVideoClip(clips=[video_clip1, video_clip2]).without_audio()

    video_clip.write_videofile(
        filename=os.path.join(BASE_DIR, "example/output_1and2.mp4"),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        logger="bar"
    )

    # 调试代码
    # video_clip.save_frame(filename=os.path.join(BASE_DIR, "example/output_1and2.png"), t=1)


if __name__ == '__main__':
    main()
