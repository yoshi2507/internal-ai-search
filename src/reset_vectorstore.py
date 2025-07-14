import os
import shutil

def reset_vectorstore():
    """ベクターストアを削除して再作成を促す"""
    chroma_path = "./chroma_db"
    
    if os.path.exists(chroma_path):
        try:
            shutil.rmtree(chroma_path)
            print("✅ ベクターストアを削除しました")
            print("アプリケーションを再起動してベクターストアを再作成してください")
        except Exception as e:
            print(f"❌ 削除エラー: {e}")
    else:
        print("ベクターストアは存在しません")

if __name__ == "__main__":
    reset_vectorstore()