import discord
from discord.ext import commands
import os
import zipfile

# 非同期関数として定義
async def process_file(file: discord.Attachment, save_directory="./Download/"):
    os.makedirs(save_directory, exist_ok=True)  # 保存先ディレクトリが存在しない場合は作成する

    save_path = os.path.join(save_directory, file.filename)

    try:
        # ファイルの保存 (awaitが必要)
        await file.save(save_path, seek_begin=True, use_cached=False)
        
        # ファイルを読み込む
        with open(save_path, "r", encoding="utf-8") as f:
            content = f.read()
            chenge_text = ['人名', '名詞', '動詞', '形容詞', '副詞', '助詞', '助動詞', '連体詞', '感動詞', '接続詞', '接頭詞', '記号', '固有名詞']
            for i in chenge_text:
                content = content.replace(i, "ja-JP")
            new_file_path = os.path.splitext(save_path)[0] + "_new"
            with open(new_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            zip_file_name = "Gboard_ja-JP.zip"
            with zipfile.ZipFile(zip_file_name, "w") as new_zip:
                new_zip.write(new_file_path, os.path.basename(new_file_path))
                
            # 一時ファイルの削除
            os.remove(new_file_path)
            
            return zip_file_name
            
    except Exception as e:
        print(e)
        raise
    finally:
        if os.path.exists(save_path):
            os.remove(save_path)
