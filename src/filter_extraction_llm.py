import re
import json
from constants import EXTRACTION_SYSTEM_PROMPT
from openai import OpenAI

# OpenAIクライアントの初期化（環境変数 OPENAI_API_KEY が必要）
client = OpenAI()

def extract_filters_from_text(question: str) -> dict:
    """
    ユーザーの質問文から検索用フィルタ（例: 部署、従業員区分）を抽出する
    """
    prompt = EXTRACTION_SYSTEM_PROMPT + f"\n\n質問文: {question}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたはPythonで辞書形式のデータ抽出を専門とするアシスタントです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        raw_text = response.choices[0].message.content

        # ```python ... ``` のコードブロックを取り除く
        raw_text_clean = re.sub(r"```(?:json|python)?\n*([\s\S]+?)\n*```", r"\1", raw_text).strip()
        filters = json.loads(raw_text_clean)

        if not isinstance(filters, dict):
            print("[ERROR] 抽出結果が辞書型ではありません。")
            return {}

        return filters

    except Exception as e:
        print(f"[ERROR] フィルタ抽出失敗: {e}")
        return {}
