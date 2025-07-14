from csv_employee_loader import EmployeeCSVLoader
import os

def test_csv_loading():
    """CSVローダーの動作テスト"""
    csv_files = []
    
    # パスを修正: ./data → ../data
    data_path = "../data"  # 修正箇所
    
    # dataフォルダ内のCSVファイルを検索
    for root, dirs, files in os.walk(data_path):
        for file in files:
            if file.endswith(".csv"):
                csv_files.append(os.path.join(root, file))
    
    print(f"発見されたCSVファイル: {len(csv_files)}個")
    for csv_file in csv_files:
        print(f"  - {csv_file}")
    
    # CSVローダーのテスト
    for csv_file in csv_files:
        try:
            loader = EmployeeCSVLoader(csv_file)
            docs = loader.load()
            print(f"\n✅ {csv_file}: {len(docs)}個のドキュメント読み込み成功")
            
            # 人事部のデータを確認
            hr_docs = [doc for doc in docs if "人事部" in doc.page_content]
            print(f"   人事部のドキュメント: {len(hr_docs)}個")
            
            for i, doc in enumerate(hr_docs[:3]):
                print(f"   人事部{i+1}: {doc.page_content[:100]}...")
                print(f"   メタデータ: {doc.metadata}")
                
        except Exception as e:
            print(f"❌ {csv_file}: エラー - {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_csv_loading()