from audio_generation import sync_generate_audios
from video_generation import generate_video


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
    # 素材源
    text = "城西好房推荐，项目位于主城西中轴-红光大道，首付5千起，建面88-112㎡。高端双会所设计的墅区品质小区，三面环绿百亩大盘，坐拥城西两条黄金地铁6号线和2号线，坐享成熟完善的交通、学区、医疗、购物、公园的生活配套。看房专车接送，点击下方链接，领取更多购房优惠！"

    # 生成音频（附带字幕文件）
    text2audio(text, f"{__file__}.mp3", f"{__file__}.srt")

    # 生成视频文件
    generate_video(audio_path=f"{__file__}.mp3", subtitle_path=f"{__file__}.srt", video_output_path=f"{__file__}.mp4")


if __name__ == '__main__':
    main()
