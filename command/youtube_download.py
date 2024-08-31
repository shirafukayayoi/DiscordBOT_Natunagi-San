from yt_dlp import YoutubeDL
import os
import asyncio

async def YoutubeDownload(url: str):
    loop = asyncio.get_event_loop()
    
    # オプション
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # 最良の画質と音質をダウンロード
        'outtmpl': 'Download/video.%(ext)s',  # ダウンロードファイル名テンプレート
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',  # MP4形式に変換
        }],
        'prefer_ffmpeg': True,  # FFmpegを使用して変換
        'noplaylist': True,  # プレイリスト全体をダウンロードしない
        'retry_times': 5,  # エラー発生時のリトライ回数
        'quiet': True,  # ログ出力を抑制
    }

    # `yt_dlp` のダウンロード処理をバックグラウンドで実行
    info_dict = await loop.run_in_executor(None, lambda: YoutubeDL(ydl_opts).extract_info(url, download=True))
    
    title = info_dict.get('title', None)
    ext = 'mp4'  # 変換後のファイル拡張子
    file_path = f"Download/video.{ext}"
    print(f"ダウンロード完了: {file_path}")

    # ダウンロードしたファイルのパスを返す
    return file_path, title
