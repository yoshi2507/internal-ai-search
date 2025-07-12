from components import compare_files_with_vectorstore
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import constants as ct

# ベクターストアを再読み込み
db = Chroma(persist_directory="./chroma_db", embedding_function=OpenAIEmbeddings())

# data フォルダと比較
registered, not_registered = compare_files_with_vectorstore(db, "./data")

# 結果表示
print("✅ ベクターストレージに登録済みファイル一覧:")
for f in registered:
    print(f)

print("\n❌ 未登録ファイル一覧:")
for f in not_registered:
    print(f)

# 中身を確認（ファイルごとのテキスト表示）
print("\n--- ドキュメント中身と参照元ファイル ---")
docs = db.get()
for i in range(len(docs["documents"])):
    print(f"\n[{i}] {docs['metadatas'][i].get('source')}")
    print(docs["documents"][i][:300])  # 先頭300文字だけ表示