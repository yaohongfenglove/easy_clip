import os

from audio_generation import sync_generate_audios
from conf.config import BASE_DIR
from video_generation import generate_video


def main():
    text_json = {
        1: "城西好房推荐，项目位于主城西中轴 - 红光大道，首付5千起，建面88 - 112㎡。",
        2: "高端双会所设计的墅区品质小区，三面环绿百亩大盘。",
        3: "坐拥城西两条黄金地铁6号线和2号线，坐享成熟完善的交通、学区、医疗、购物、公园的生活配套。",
        4: "看房专车接送，点击下方链接，领取更多购房优惠！"
    }

    # sentence_separators = ["。", "？", "！"]

    paragraph_list = list(text_json.values())
    paragraph_audio_output_path_list = [os.path.join(BASE_DIR, f"output/audio/{i + 1}.mp3") for i in range(len(paragraph_list))]

    # 生成音频文件
    sync_generate_audios(paragraph_list, paragraph_audio_output_path_list)

    # 生成视频文件
    video_output_path = os.path.join(BASE_DIR, f"output/video/1.mp4")
    generate_video(paragraph_audio_output_path_list, video_output_path)


if __name__ == '__main__':
    main()
