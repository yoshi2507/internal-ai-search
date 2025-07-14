"""
このファイルは、最初の画面読み込み時にのみ実行される初期化処理が記述されたファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
from logging.handlers import TimedRotatingFileHandler
import os
import logging
import shutil
from uuid import uuid4
import sys
import unicodedata
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
import streamlit as st
from docx import Document
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
import constants as ct
from csv_employee_loader import EmployeeCSVLoader
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders.csv_loader import CSVLoader

############################################################
# 設定関連
############################################################
# 「.env」ファイルで定義した環境変数の読み込み
load_dotenv()


############################################################
# 関数定義
############################################################

def initialize():
    """
    画面読み込み時に実行する初期化処理
    """
    # 初期化データの用意
    initialize_session_state()
    # ログ出力用にセッションIDを生成
    initialize_session_id()
    # ログ出力の設定
    initialize_logger()
    # RAGのRetrieverを作成 （retriever構築を切り出し）
    initialize_all_retrievers()


def initialize_logger():
    """
    ログ出力の設定
    """
    # 指定のログフォルダが存在すれば読み込み、存在しなければ新規作成
    os.makedirs(ct.LOG_DIR_PATH, exist_ok=True)
    
    # 引数に指定した名前のロガー（ログを記録するオブジェクト）を取得
    # 再度別の箇所で呼び出した場合、すでに同じ名前のロガーが存在していれば読み込む
    logger = logging.getLogger(ct.LOGGER_NAME)

    # すでにロガーにハンドラー（ログの出力先を制御するもの）が設定されている場合、同じログ出力が複数回行われないよう処理を中断する
    if logger.hasHandlers():
        return

    # 1日単位でログファイルの中身をリセットし、切り替える設定
    log_handler = TimedRotatingFileHandler(
        os.path.join(ct.LOG_DIR_PATH, ct.LOG_FILE),
        when="D",
        encoding="utf8"
    )
    # 出力するログメッセージのフォーマット定義
    # - 「levelname」: ログの重要度（INFO, WARNING, ERRORなど）
    # - 「asctime」: ログのタイムスタンプ（いつ記録されたか）
    # - 「lineno」: ログが出力されたファイルの行番号
    # - 「funcName」: ログが出力された関数名
    # - 「session_id」: セッションID（誰のアプリ操作か分かるように）
    # - 「message」: ログメッセージ
    formatter = logging.Formatter(
        f"[%(levelname)s] %(asctime)s line %(lineno)s, in %(funcName)s, session_id={st.session_state.session_id}: %(message)s"
    )

    # 定義したフォーマッターの適用
    log_handler.setFormatter(formatter)

    # ログレベルを「INFO」に設定
    logger.setLevel(logging.INFO)

    # 作成したハンドラー（ログ出力先を制御するオブジェクト）を、
    # ロガー（ログメッセージを実際に生成するオブジェクト）に追加してログ出力の最終設定
    logger.addHandler(log_handler)


def initialize_session_id():
    """
    セッションIDの作成
    """
    if "session_id" not in st.session_state:
        # ランダムな文字列（セッションID）を、ログ出力用に作成
        st.session_state.session_id = uuid4().hex


def initialize_all_retrievers():
    """
    社員名簿用と全体用の retriever を構築
    """
    logger = logging.getLogger(ct.LOGGER_NAME)

    # すでに retriever がある場合はスキップ
    if "employee_retriever" in st.session_state and "full_retriever" in st.session_state:
        return

    embeddings = OpenAIEmbeddings()
    text_splitter = CharacterTextSplitter(
        chunk_size=ct.CHUNK_SIZE,
        chunk_overlap=ct.CHUNK_OVERLAP,
        separator="\n"
    )

    # 🔹 社員名簿 retriever（分割しない）
    employee_csv_path = os.path.join(ct.RAG_TOP_FOLDER_PATH, "社員について", "社員名簿.csv")
    csv_loader = CSVLoader(file_path=employee_csv_path, encoding="utf-8")
    employee_docs = csv_loader.load()
    employee_db = Chroma.from_documents(employee_docs, embedding=embeddings)
    st.session_state.employee_retriever = employee_db.as_retriever(search_kwargs={"k": ct.NUM_RELATED_DOCUMENTS})

    # 🔸 全体 retriever（従来通り分割あり）
    full_docs = load_data_sources()
    splitted_docs = text_splitter.split_documents(full_docs)
    full_db = Chroma.from_documents(splitted_docs, embedding=embeddings)
    st.session_state.full_retriever = full_db.as_retriever(search_kwargs={"k": ct.NUM_RELATED_DOCUMENTS})


def initialize_session_state():
    """
    初期化データの用意
    """
    if "messages" not in st.session_state:
        # 「表示用」の会話ログを順次格納するリストを用意
        st.session_state.messages = []
        # 「LLMとのやりとり用」の会話ログを順次格納するリストを用意
        st.session_state.chat_history = []


def get_loader(file_path, ext):
    """拡張子に応じた適切なローダーを取得する"""
    if ext == ".csv":
        return EmployeeCSVLoader(file_path, encoding="utf-8")
    
    loader_class = ct.SUPPORTED_EXTENSIONS.get(ext)
    if loader_class:
        # TextLoaderの場合、エンコーディングを指定
        if loader_class == TextLoader:
            return loader_class(file_path, encoding="utf-8")
        return loader_class(file_path)
    
    return None


def load_documents_from_path(path):
    """指定されたパスからドキュメントを再帰的に読み込む"""
    documents = []
    logger = logging.getLogger(ct.LOGGER_NAME)
    logger.info(f"データソース探索開始: {path}")
    
    for root, _, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()
            
            loader = get_loader(file_path, file_ext)
            if loader:
                try:
                    docs = loader.load()
                    documents.extend(docs)
                    logger.info(f"読み込み成功: {file_path} ({len(docs)}件)")
                except Exception as e:
                    logger.error(f"読み込み失敗: {file_path}, エラー: {e}")
    return documents


def load_data_sources():
    """
    RAGの参照先となるデータソースの読み込み
    """
    logger = logging.getLogger(ct.LOGGER_NAME)
    
    # 1. ファイルベースのドキュメントを読み込む
    docs_all = load_documents_from_path(ct.RAG_TOP_FOLDER_PATH)

    # 2. Webベースのドキュメントを読み込む
    web_docs_all = []
    if hasattr(ct, 'WEB_URL_LOAD_TARGETS') and ct.WEB_URL_LOAD_TARGETS:
        logger.info(f"Web読み込み開始: {len(ct.WEB_URL_LOAD_TARGETS)}件のURL")
        for web_url in ct.WEB_URL_LOAD_TARGETS:
            try:
                loader = WebBaseLoader(web_url)
                web_docs = loader.load()
                web_docs_all.extend(web_docs)
                logger.info(f"Web読み込み成功: {web_url}")
            except Exception as e:
                logger.error(f"Web読み込みエラー {web_url}: {e}")
    else:
        logger.info("WEB_URL_LOAD_TARGETSが未設定または空のため、Web読み込みをスキップ")
    
    # ファイルとWebのドキュメントを結合
    docs_all.extend(web_docs_all)
    logger.info(f"総読み込み完了: 合計{len(docs_all)}件のドキュメント")

    return docs_all


def adjust_string(s):
    """
    Windows環境でRAGが正常動作するよう調整
    
    Args:
        s: 調整を行う文字列
    
    Returns:
        調整を行った文字列
    """
    # 調整対象は文字列のみ
    if type(s) is not str:
        return s

    # OSがWindowsの場合、Unicode正規化と、cp932（Windows用の文字コード）で表現できない文字を除去
    if sys.platform.startswith("win"):
        s = unicodedata.normalize('NFC', s)
        s = s.encode("cp932", "ignore").decode("cp932")
        return s
    
    # OSがWindows以外の場合はそのまま返す
    return s