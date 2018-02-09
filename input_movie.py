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

MOVIE_LENGTH_SEC = None


def main():
    movie_file, sound_file, accel_file = get_filename()

    time_lag = calculate_time_lag_sec(movie_file, sound_file)

    begin, length = get_trim_time_sec()

    trim_movie(movie_file, begin, length)
    trim_censor_data(accel_file, begin + time_lag, length)

    print(MOVIE_LENGTH_SEC)


# 動画，音声，センサデータのファイル名を取得
def get_filename():
    movie_file = input_filename("Input movie file name. > ")
    sound_file = input_filename("Input sound file name. > ")
    accel_file = input_filename("Input accel file name. > ")

    return movie_file, sound_file, accel_file


# get_filename用。存在するファイルの名前を入力するまでループ
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
    begin = input_trim_time_sec("動画の開始地点[秒] = ")
    length = input_trim_time_sec("動画の長さ[秒] = ")

    return begin, length


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
def calculate_time_lag_sec(filename1, filename2):
    global MOVIE_LENGTH_SEC
    remove_wav(MOVIE_WAVE)
    remove_wav(SOUND_WAVE)

    sample_rate = convert_wave_to_calculate(filename1, filename2)

    data1, data2 = tidy_up_data_for_calculation()
    MOVIE_LENGTH_SEC = len(data1) / sample_rate

    corr = sig.correlate(data1, data2, "full")
    plot_wav.output_waveform2(corr)

    time_lag = (len(data1) - corr.argmax()) / sample_rate

    if time_lag > 0:
        print("音声は映像より" + str(round(time_lag, 2)) + "秒遅れています。")
    elif time_lag < 0:
        print("映像は音声より" + str(round(time_lag, 2) * -1) + "秒遅れています。")
    else:
        print("映像と音声の間に時間差はありません。")

    remove_wav(MOVIE_WAVE)
    remove_wav(SOUND_WAVE)

    return time_lag


# calculate_time_lag_sec用。filenameで指定したファイルの存在を確認して削除
def remove_wav(filename):
    if os.path.exists(filename):
        os.remove(filename)


# calculate_time_lag_sec用。２つの音声のうち，小さい方のサンプリング周波数でリサンプリングしたwavを書き出し，その周波数を返す
def convert_wave_to_calculate(filename1, filename2):
    movie_file = AudioSegment.from_file(filename1)
    sound_file = AudioSegment.from_file(filename2)

    if movie_file.frame_rate < sound_file.frame_rate:
        sample_rate = movie_file.frame_rate
    else:
        sample_rate = sound_file.frame_rate

    output_wave_with_subsampling(filename1, filename2, sample_rate)

    return sample_rate


# calculate_time_lag_sec用。sample_rateで指定した周波数でリサンプリングしてwavに書き出し
def output_wave_with_subsampling(filename1, filename2, sample_rate):
    # HACK: wavを書き出さなくてもできる方法を探す
    fm = ffmpy.FFmpeg(
        inputs={filename1: None},
        outputs={MOVIE_WAVE: '-ac 1 -ar %d' % sample_rate}
    )
    fo = ffmpy.FFmpeg(
        inputs={filename2: None},
        outputs={SOUND_WAVE: '-ac 1 -ar %d' % sample_rate}
    )
    fm.run()
    fo.run()


# calculate_time_lag_sec用。データを読み込んで計算用に整形
def tidy_up_data_for_calculation():
    data1, rate1 = sf.read(MOVIE_WAVE)
    data2, rate2 = sf.read(SOUND_WAVE)

    if len(data1) < len(data2):
        data2 = data2[:len(data1)]
    elif len(data1) > len(data2):
        data1 = data1[:len(data2)]

    data1 = data1 - data1.mean()
    data2 = data2 - data2.mean()

    return data1, data2


# 指定されたbegin_timeからlength秒間の動画を書き出し
def trim_movie(filename, begin, length):
    cmd1 = "-ss " + str(begin)
    cmd2 = "-t " + str(length)
    out_name = "trim_" + str(filename)

    remove_wav(out_name)

    fc = ffmpy.FFmpeg(
        inputs={filename: cmd1},
        outputs={out_name: cmd2}
    )

    # start = time.time()
    # fc.run()
    # end_time = time.time() - start
    # print("elapsed_time:{0}".format(end_time) + "[sec]")
    fc.run()


# 指定されたbeginからlength分のセンサデータを切り出し
def trim_censor_data(filename, begin, length):
    begin *= 1000
    length *= 1000
    end = begin + length

    file = open(filename, "r")
    out_file = open("trim_" + filename, "w")

    if begin < 0:
        print("指定した時間に対応するセンサデータが用意できませんでした。")
        print("開始時間を変更すると解決する可能性があります。")
        sys.exit(1)

    out_file.write("DataNum,0.016,offset.\n")
    file.readline()

    lines = file.readlines()
    print(len(lines))
    line = None

    for line in lines:
        line = line.replace("\n", "")
        line = line.split(",")

        row = "{},{},{},{}\n".format(
            (float(line[0]) - begin),
            line[1],
            line[2],
            line[3]
        )
        if begin < float(line[0]) < end:
            out_file.write(row)

    last_time = line[0]
    print(last_time)

    if float(last_time) < (begin + length):
        print("指定した時間に対応するセンサデータが用意できませんでした。")
        print("動画の長さを短くすると解決する可能性があります。")
        sys.exit(1)

    file.close()
    out_file.close()


if __name__ == '__main__':
    main()


# TODO
# movie_lengthの範囲外をトリミングしようとした時にエラーをはくように
# センサデータについてもおんなじような仕様が作れたら嬉しい
# 各種変数名の見直し