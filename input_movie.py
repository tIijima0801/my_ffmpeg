# coding: utf-8

import plot_wav
import os
import sys
from pydub import AudioSegment
import ffmpy
import scipy.signal as sig
import soundfile as sf
import time
import wx

MOVIE_WAVE = "m_output.wav"
SOUND_WAVE = "s_output.wav"


def main():
    movie_file = input_filename("Input movie file name. > ")
    sound_file = input_filename("Input sound file name. > ")
    accel_file = input_filename("Input accel file name. > ")

    time_lag_sec, movie_length_sec = calculate_time_lag_sec(movie_file, sound_file)

    begin_sec = get_trim_begin_sec(time_lag_sec)
    length_sec = get_trim_length_sec(begin_sec, movie_length_sec)

    trim_sensor_data(accel_file, begin_sec + time_lag_sec, length_sec)
    # trim_movie(movie_file, begin_sec, length_sec)


# ファイル名を取得，存在するファイル名を入力するまで聞き返す
def input_filename(sentence_to_display):
    while True:
        filename = input(sentence_to_display)
        if os.path.exists(filename):
            break
        else:
            print("入力した名前のファイルは存在しません。")
            print("もう一度入力してください。")

    return filename


# 動画と音声の時間差を計測。動画の方が進んでいれば符号はプラス，反対だとマイナス
# 実例)
# 聞き比べた時，動画よりも音声が1秒遅れていた場合
# time_lag_secの値は+1
# 聞き比べた時，動画よりも音声が1秒進んでいた場合
# time_lag_secの値は-1
def calculate_time_lag_sec(movie_file, sound_file):
    sample_rate = get_lower_sample_rate(movie_file, sound_file)

    output_wave_with_subsampling(movie_file, sound_file, sample_rate)

    data1, data2 = tidy_up_data_for_calculation()

    movie_length_sec = len(data1) / sample_rate

    corr = sig.correlate(data1, data2, "full")
    # plot_wav.output_waveform2(corr)

    time_lag_sec = (len(data1) - corr.argmax()) / sample_rate
    time_lag_sec = round(time_lag_sec, 2)

    display_time_lag_sec(time_lag_sec)

    remove_wav(MOVIE_WAVE)
    remove_wav(SOUND_WAVE)

    return time_lag_sec, movie_length_sec


# calculate_time_lag_sec用。filenameで指定したファイルの存在を確認して削除
def remove_wav(filename):
    if os.path.exists(filename):
        os.remove(filename)


# calculate_time_lag_sec用。ダウンサンプリングのため，２つのファイルのうち，低い方のサンプリング周波数の値を返す。
def get_lower_sample_rate(movie_file, sound_file):
    movie = AudioSegment.from_file(movie_file)
    sound = AudioSegment.from_file(sound_file)

    if movie.frame_rate < sound.frame_rate:
        sample_rate = movie.frame_rate
    else:
        sample_rate = sound.frame_rate

    return sample_rate


# calculate_time_lag_sec用。sample_rateで指定した周波数でリサンプリングしてwavに書き出し
def output_wave_with_subsampling(movie_file, sound_file, sample_rate):
    # HACK: wavを書き出さなくてもできる方法を探す
    fm = ffmpy.FFmpeg(
        inputs={movie_file: None},
        outputs={MOVIE_WAVE: '-ac 1 -ar %d' % sample_rate}
    )
    fo = ffmpy.FFmpeg(
        inputs={sound_file: None},
        outputs={SOUND_WAVE: '-ac 1 -ar %d' % sample_rate}
    )
    fm.run()
    fo.run()


# calculate_time_lag_sec用。データを読み込んで計算用に整形
def tidy_up_data_for_calculation():
    movie_data, movie_rate = sf.read(MOVIE_WAVE)
    sound_data, sound_rate = sf.read(SOUND_WAVE)

    # 2データの長さを揃える
    if len(movie_data) < len(sound_data):
        sound_data = sound_data[:len(movie_data)]
    elif len(movie_data) > len(sound_data):
        movie_data = movie_data[:len(sound_data)]

    # 相互相関関数の計算に影響が出る可能性があるため，平均を0に
    data1 = movie_data - movie_data.mean()
    data2 = sound_data - sound_data.mean()

    return data1, data2


# calculate_time_lag_sec用。時間差を画面表示
def display_time_lag_sec(time_lag_sec):
    if time_lag_sec > 0:
        print("音声は映像より" + str(time_lag_sec) + "秒遅れています。")
    elif time_lag_sec < 0:
        print("音声は映像より" + str(time_lag_sec * -1) + "秒進んでいます")
    else:
        print("映像と音声の間に時間差はありません。")


# トリミングの開始点を入力
def get_trim_begin_sec(time_lag_sec):
    while True:
        trim_begin_sec = input_trim_time_sec("動画の開始地点[秒] = ")
        if trim_begin_sec + time_lag_sec < 0:
            # センサデータが用意できないため再入力
            print("指定した時間のセンサデータを用意できません。")
        else:
            return trim_begin_sec


# トリミングで切り出したい長さを入力
def get_trim_length_sec(trim_begin_sec, movie_length_sec):
    while True:
        trim_length_sec = input_trim_time_sec("動画の長さ[秒] = ")
        if trim_begin_sec + trim_length_sec > movie_length_sec:
            # 指定した範囲が動画の長さを超えるため再入力。
            print("指定した時間が動画の長さを超えています。")
        else:
            return trim_length_sec


# get_trim_time_sec用。数値が入力されるまでループ
def input_trim_time_sec(sentence_to_display):
    while True:
        try:
            input_string = float(input(sentence_to_display))
        except ValueError:
            print("入力が正しくありません。数値を入力してください")
        else:
            if input_string < 0:
                print("入力が正しくありません。0以上の数値を入力してください")
            else:
                return input_string


# 指定されたbegin_secからlength_sec分のセンサデータを切り出し
def trim_sensor_data(accel_file, begin_sec, length_sec):
    begin_ms, length_ms = to_millisecond(begin_sec), to_millisecond(length_sec)
    end_ms = begin_ms + length_ms
    complete = 0  # 動画の最後までセンサデータを用意できたかの判定

    in_file, out_file = open(accel_file, "r"), open("trim_" + accel_file, "w")

    header = in_file.readline()
    out_file.write(header)

    lines = in_file.readlines()

    for line in lines:
        line = line.replace("\n" or "\r", "")
        line = line.split(",")

        row = "{},{},{},{}\r\n".format(
            (float(line[0]) - begin_ms),
            line[1],
            line[2],
            line[3]
        )

        if begin_ms <= float(line[0]) <= end_ms:
            out_file.write(row)
        elif float(line[0]) >= end_ms:
            complete = 1
            break

    in_file.close()
    out_file.close()

    check_sensor_data_existence_end(complete)


# trim_sensor_data用。入力された秒数をミリ秒にして返す。
def to_millisecond(sec):
    return sec * 1000


# 動画の最後まで対応するセンサデータが用意できたかを判定
def check_sensor_data_existence_end(complete):
    if not complete:
        print("最後までセンサデータを用意できませんでした。")
        sys.exit(1)


# 指定されたbegin_secからlength_sec秒間の動画を書き出し
def trim_movie(movie_file, begin_sec, length_sec):
    cmd1 = "-ss " + str(begin_sec)
    cmd2 = "-t " + str(length_sec)
    out_name = "trim_" + str(movie_file)

    remove_wav(out_name)

    fc = ffmpy.FFmpeg(
        inputs={movie_file: cmd1},
        outputs={out_name: cmd2}
    )
    fc.run()


if __name__ == '__main__':
    main()


# TODO
# trim_sensor_dataの中綺麗にしたいな
# get_fileの名前もうちょい考えよう。get_three_filesとか。そもそもなくてもいいかも
# 各種変数名の見直し