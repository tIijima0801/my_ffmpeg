# my_ffmpeg

# 動作バージョン
python 3.6.4

# 使い方
## 1.起動方法
windowsならコマンドプロンプト，
macOSならターミナルで以下のコマンドを実行

**'python3 input_movie.py'**

## 2.ファイル名の入力
・動画ファイル名（テスト環境では.mp4）  
・音声ファイル名（テスト環境では.wav）  
・センサデータのファイル名（テスト環境では.csv）  
を順番に入力します。  
注）順番を間違えると正しく実行されない 

## 3.時間差計算
内部で勝手に時間差を計算してくれる。 
計算が終わったら画面に表示。

## 4.トリミングの時間入力
beginとlengthの入力を促される。  
beginにはトリミングの開始地点，  
lengthには何秒切り出すのかを入力します。  

一応，始点から終点まで入力するコードもコメントアウトして残しておきます。 　
使い勝手に応じて好きな方を選んでください。

## 5.動画とセンサデータのトリミング
センサデータはすぐに終わりますが，動画の方はそこそこ時間がかかります（30秒切り出すのにだいたい5分くらい）
トリミング時間については改善方法を模索中です。
