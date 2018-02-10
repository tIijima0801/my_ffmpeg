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

# 動画の長さを保存する変数
# calculate_tim_lag_secで動画の長さを求める。
# トリミングの時に(begin_sec + length_sec)がこの値を超えていた場合エラーを返す。
MOVIE_LENGTH_SEC = None


def main():
    movie_file, sound_file, accel_file = get_file()
    begin_sec, length_sec = get_trim_time_sec()

    time_lag_sec = calculate_time_lag_sec(movie_file, sound_file)

    trim_censor_data(accel_file, begin_sec + time_lag_sec, length_sec)
    trim_movie(movie_file, begin_sec, length_sec)

    print(MOVIE_LENGTH_SEC)


# 動画，音声，センサデータのファイル名を取得
def get_file():
    movie_file = input_filename("Input movie file name. > ")
    sound_file = input_filename("Input sound file name. > ")
    accel_file = input_filename("Input accel file name. > ")

    return movie_file, sound_file, accel_file


# get_file用。存在するファイルの名前を入力するまでループ
def input_filename(string):
    while True:
        filename = input(string)
        if os.path.exists(filename):
            break
        else:
            print("入力した名前のファイルは存在しません。")
    return filename


# 動画のトリミングの開始時間，切り出したい長さを入力
def get_trim_time_sec():
    begin_sec = input_trim_time_sec("動画の開始地点[秒] = ")
    length_sec = input_trim_time_sec("動画の長さ[秒] = ")

    return begin_sec, length_sec


# get_trim_time_sec用。数値が入力されるまでループ
def input_trim_time_sec(string):
    while True:
        try:
            input_string = float(input(string))
        except ValueError:
            print("入力が正しくありません。数値を入力してください")
        else:
            if input_string < 0:
                print("入力が正しくありません。0以上の数値を入力してください")
            else:
                return input_string


# 時間差を計測
# 音声の方に遅延がある場合は符号がプラス，動画の方に遅延がある場合は符号がマイナスになる。
# 実例)
# 聞き比べた時，動画よりも音声が1秒遅れていた場合
# time_lag_secの値は＋1になる。
def calculate_time_lag_sec(movie_file, sound_file):
    global MOVIE_LENGTH_SEC

    remove_wav(MOVIE_WAVE)
    remove_wav(SOUND_WAVE)

    sample_rate = convert_wave_to_calculate(movie_file, sound_file)

    output_wave_with_subsampling(movie_file, sound_file, sample_rate)

    data1, data2 = tidy_up_data_for_calculation()

    MOVIE_LENGTH_SEC = len(data1) / sample_rate

    corr = sig.correlate(data1, data2, "full")
    # plot_wav.output_waveform2(corr)

    time_lag_sec = (len(data1) - corr.argmax()) / sample_rate

    if time_lag_sec > 0:
        print("音声は映像より" + str(round(time_lag_sec, 2)) + "秒遅れています。")
    elif time_lag_sec < 0:
        print("音声は映像より" + str(round(time_lag_sec, 2) * -1) + "秒進んでいます")
    else:
        print("映像と音声の間に時間差はありません。")

    remove_wav(MOVIE_WAVE)
    remove_wav(SOUND_WAVE)

    return time_lag_sec


# calculate_time_lag_sec用。filenameで指定したファイルの存在を確認して削除
def remove_wav(filename):
    if os.path.exists(filename):
        os.remove(filename)


# calculate_time_lag_sec用。ダウンサンプリングのため，２つのファイルのうち，低い方のサンプリング周波数の値を返す。
def convert_wave_to_calculate(movie_file, sound_file):
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


# 指定されたbegin_secからlength_sec分のセンサデータを切り出し
def trim_censor_data(accel_file, begin_sec, length_sec):
    check_censor_data_existence_begin(begin_sec)

    begin_ms, length_ms = to_millisecond(begin_sec), to_millisecond(length_sec)
    end_ms = begin_ms + length_ms
    complete = 0    # 動画の最後までセンサデータを用意できたかの判定

    in_file, out_file = open(accel_file, "r"), open("trim_" + accel_file, "w")

    out_file.write("DataNum,0.016,offset.\n")
    in_file.readline()

    lines = in_file.readlines()

    for line in lines:
        line = line.replace("\n", "")
        line = line.split(",")

        row = "{},{},{},{}\n".format(
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

    check_censor_data_existence_end(complete)


# trim_censor_data用。入力された秒数をミリ秒にして返す。
def to_millisecond(sec):
    m_sec = sec * 1000
    return m_sec


def check_censor_data_existence_begin(begin_time):
    if begin_time < 0:
        print("指定した時間に対応するセンサデータが用意できませんでした。")
        print("開始時間を変更すると解決する可能性があります。")
        sys.exit(1)


def check_censor_data_existence_end(complete):
    if not complete:
        print("最後までセンサデータを用意できませんでした。")
        sys.exit(1)


if __name__ == '__main__':
    main()


# TODO
# MOVIE_LENGTH_SECの範囲外をトリミングしようとした時にエラーをはくように
# trim_censor_dataの中綺麗にしたいな
# 各種変数名の見直し