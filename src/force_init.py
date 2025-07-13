import streamlit as st
import shutil
import os

def force_initialize():
    """強制的に初期化を実行"""
    print("🔄 強制初期化を開始します...")
    
    # ベクターストアを削除
    persist_dir = "./chroma_db"
    if os.path.exists(persist_dir):
        try:
            shutil.rmtree(persist_dir)
            print("✅ ベクターストアを削除しました")
        except Exception as e:
            print(f"⚠️ ベクターストア削除エラー: {e}")
    
    # セッション状態ファイルがあれば削除
    session_files = [".streamlit", "__pycache__"]
    for session_file in session_files:
        if os.path.exists(session_file):
            try:
                if os.path.isdir(session_file):
                    shutil.rmtree(session_file)
                else:
                    os.remove(session_file)
                print(f"✅ {session_file}を削除しました")
            except Exception as e:
                print(f"⚠️ {session_file}削除エラー: {e}")
    
    print("🎉 強制初期化完了！アプリを再起動してください")

if __name__ == "__main__":
    force_initialize()