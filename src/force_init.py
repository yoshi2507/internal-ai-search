import shutil
import os
import sys
# streamlitインポートを削除

def force_initialize():
    """強制的に初期化を実行"""
    
    # 環境変数設定
    if not os.getenv("USER_AGENT"):
        os.environ["USER_AGENT"] = "company-inner-search-app/1.0"
    
    print("=== 強制初期化を開始します ===")
    
    # 削除対象のパス一覧（簡素化）
    paths_to_delete = [
        "chroma_db",
        "../data/vectorstore", 
        "../chroma_db",
        "__pycache__",
        ".streamlit"
    ]
    
    deleted_count = 0
    for path in paths_to_delete:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                print(f"[OK] 削除: {path}")
                deleted_count += 1
            except Exception as e:
                print(f"[ERROR] 削除失敗: {path} - {e}")
    
    print(f"=== 削除完了: {deleted_count}件 ===")
    print("[SUCCESS] 強制初期化完了")
    return True

if __name__ == "__main__":
    success = force_initialize()
    if success:
        print("*** 強制初期化が正常に完了しました ***")
    else:
        print("*** 強制初期化に失敗しました ***")
        sys.exit(1)