# src/filter_extraction_llm.py

from langchain_openai import ChatOpenAI
import json

llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2)

def extract_filters_from_text(user_input: str) -> dict:
    """
    ユーザー入力から社員検索用フィルタ条件（部署、従業員区分など）を抽出する。

    Args:
        user_input (str): ユーザーの自然文入力

    Returns:
        dict: {"部署": ..., "従業員区分": ...}
    """
    prompt = f"""
あなたは社員名簿検索に特化した社内AIアシスタントです。
次のユーザー入力から、社員名簿.csv に存在する「部署」や「従業員区分」の値を特定してください。
不明な場合は空欄のままで構いません。

【入力】「{user_input}」

【出力形式】
{{"部署": "...", "従業員区分": "..."}}
    """.strip()

    try:
        response = llm.invoke(prompt).content
        filters = json.loads(response)
        return filters
    except Exception as e:
        print(f"[ERROR] フィルタ抽出失敗: {e}")
        return {}