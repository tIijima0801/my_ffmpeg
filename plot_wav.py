import matplotlib.pyplot as plt


def output_waveform(data1, data2):
    plt.plot(data1, label="data1")
    plt.plot(data2, label="data2")
    plt.title("WAVE")
    plt.xlabel(' data num ')
    plt.ylabel(' Amplitude ')
    plt.legend()
    plt.show()


def output_waveform2(data):
    plt.plot(data)
    # plt.title("Cross Correlation")
    plt.xlabel("Data num")
    plt.ylabel("Cross Correlation")
    plt.show()

# import numpy as np
#
# target_sig = np.random.normal(size=1000) * 1.0
# delay = 800
# sig1 = np.random.normal(size=2000) * 0.2
# sig1[:1000] += target_sig
# sig2 = np.random.normal(size=2000) * 0.2
# sig2[delay:delay+1000] += target_sig
#
# corr = np.correlate(sig1, sig2, "full")
# estimated_delay = corr.argmax() - (len(sig1) - 1)
# print("estimated delay is " + str(estimated_delay))
#
#
# # print("Input file name 1 = in.mp4")
#     # print("Input file name 2 = in.wav")
#     # print("Sampling frequency = " + str(sample_freq))
#     # print("Number of data = 410000")
#     # print("\nWhen using \"scipy.correlate\"")
#
# # 正規化のために標準偏差を求める
# standard_deviation1 = []
# standard_deviation2 = []
# for i in range(len(data1)):
#     if i % 10000 == 0:
#         print("i = " + str(i))
#     standard_deviation1.append(np.std(data1[i:]))
#     standard_deviation2.append(np.std(data2[i:]))
#
#  # 標準偏差で相互相関関数を正規化
#     for j in range(len(data1)):
#         corr[j] *= standard_deviation1[j] * standard_deviation2[j]
#
#
# # scipyを使った相関係数（間違ったファイルをinputしていないかの判定）
#     if estimated_delay < 0:
#         check = sta.stats.pearsonr(data1[len(data1) - corr.argmax():], data2[:corr.argmax()])
#         print(check)
#     elif estimated_delay > 0:
#         print("a")
#         check = sta.stats.pearsonr(data1[:corr.argmax()], data2[len(data2) - corr.argmax():])
#         print(check)