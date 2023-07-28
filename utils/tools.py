import os
from typing import Tuple, List

from moviepy.video.io.VideoFileClip import VideoFileClip


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


def main():
    root_folder = r"\\192.168.100.199\video_share\AIGC\drafts_config_0724_01"

    video_path_list = get_file_path_list(root_folder)
    for video_path in video_path_list:
        video_clip = VideoFileClip(video_path)
        fps = video_clip.fps
        video_clip.close()
        if (int(fps) - fps) != 0:
            print(f"帧率：{fps} → 视频源：{video_path}")


if __name__ == '__main__':
    main()
