"""
このファイルは、画面表示以外の様々な関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import os
from dotenv import load_dotenv
import streamlit as st
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import constants as ct
from filter_extraction_llm import extract_filters_from_text

############################################################
# 設定関連
############################################################
# 「.env」ファイルで定義した環境変数の読み込み
load_dotenv()


############################################################
# 関数定義
############################################################
def extract_department_name(chat_message):
    """
    ユーザー入力に含まれる部署名を抽出する（簡易キーワード一致）

    Args:
        chat_message: ユーザー入力メッセージ

    Returns:
        部署名（例：「人事部」）または None
    """
    departments = ["人事部", "営業部", "IT部", "マーケティング部", "経理部", "総務部"]
    for dept in departments:
        if dept in chat_message:
            return dept
    return None

def get_source_icon(source):
    """
    メッセージと一緒に表示するアイコンの種類を取得

    Args:
        source: 参照元のありか

    Returns:
        メッセージと一緒に表示するアイコンの種類
    """
    # 参照元がWebページの場合とファイルの場合で、取得するアイコンの種類を変える
    if source.startswith("http"):
        icon = ct.LINK_SOURCE_ICON
    else:
        icon = ct.DOC_SOURCE_ICON
    
    return icon


def build_error_message(message):
    """
    エラーメッセージと管理者問い合わせテンプレートの連結

    Args:
        message: 画面上に表示するエラーメッセージ

    Returns:
        エラーメッセージと管理者問い合わせテンプレートの連結テキスト
    """
    return "\n".join([message, ct.COMMON_ERROR_MESSAGE])

def is_employee_query(chat_message):
    """
    入力が社員情報に関する質問かどうかを判定（簡易的なキーワードマッチ）
    """
    keywords = [
        "社員", "従業員", "人事", "所属", "部署",
        "メンバー", "一覧", "スタッフ", "人員"
    ]
    return any(keyword in chat_message for keyword in keywords)

def get_llm_response(chat_message):
    """
    LLMからの回答取得

    Args:
        chat_message: ユーザー入力値

    Returns:
        LLMからの回答
    """
    # LLMのオブジェクトを用意
    llm = ChatOpenAI(model_name=ct.MODEL, temperature=ct.TEMPERATURE)

    # 会話履歴なしでもLLMに理解してもらえる、独立した入力テキストを取得するためのプロンプトテンプレートを作成
    question_generator_template = ct.SYSTEM_PROMPT_CREATE_INDEPENDENT_TEXT
    question_generator_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", question_generator_template),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )

    # モードによってLLMから回答を取得する用のプロンプトを変更
    if st.session_state.mode == ct.ANSWER_MODE_1:
        question_answer_template = ct.SYSTEM_PROMPT_DOC_SEARCH
    else:
        question_answer_template = ct.SYSTEM_PROMPT_INQUIRY

    question_answer_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", question_answer_template),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )

    # === retrieverを社員か文書かで切り替え ===
    if is_employee_query(chat_message):
        retriever = st.session_state.employee_retriever

        # 🔹 LLMでフィルタ抽出
        filters = extract_filters_from_text(chat_message)

        # ✅ フィルタキーのマッピング変換
        key_mapping = {
            "部署": "department",
            "従業員区分": "employment_type"  # 今後の拡張を見据えて、英語に統一
        }      
        converted_filters = {key_mapping.get(k, k): v for k, v in filters.items() if v}

        # 🔹 フィルタ条件を画面に表示（ユーザーに明示）
        if filters:
            st.markdown("#### 🧠 AIが抽出した検索条件")
            for key, value in filters.items():
                if value:
                    st.markdown(f"- **{key}**: {value}")
            st.markdown("（※条件が意図と違う場合は、修正して再入力してください）")

            # 🔹 検索フィルタに反映
            retriever.search_kwargs["filter"] = {
                "$and": [{"category": "employee"}] + [{k: v} for k, v in converted_filters.items()]
            }

            # 🔍 フィルタ条件をデバッグ出力
            print("[DEBUG] 設定された検索フィルタ:", retriever.search_kwargs["filter"])
    else:
        retriever = st.session_state.full_retriever

    # retriever に基づいて chain を構築
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, question_generator_prompt
    )

    question_answer_chain = create_stuff_documents_chain(llm, question_answer_prompt)

    chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    # LLMへのリクエストとレスポンス取得
    llm_response = chain.invoke({
        "input": chat_message,
        "chat_history": st.session_state.chat_history
    })

    # 会話履歴に追加
    st.session_state.chat_history.extend([
        HumanMessage(content=chat_message),
        llm_response["answer"]
    ])

    return llm_response

