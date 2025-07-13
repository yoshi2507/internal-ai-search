from langchain_core.document_loaders import BaseLoader
from langchain.schema import Document
import pandas as pd
import os
import logging
import csv

class EmployeeCSVLoader(BaseLoader):
    """
    社員名簿CSV専用のローダー
    各行を個別のドキュメントとして処理し、部署での検索を最適化
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.logger = logging.getLogger("company_inner_search_app")

    def load(self):
        """CSVファイルを読み込み、構造化検索用のメタデータを追加"""
        documents = []
        
        # 🔥 新機能: 部署別インデックスを作成
        department_index = {}
        
        try:
            self.logger.info(f"CSV読み込み開始: {self.file_path}")
            
            with open(self.file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                
                for i, row in enumerate(rows):
                    # 既存のドキュメント作成処理
                    employee_info = []
                    metadata = {
                        "source": self.file_path,
                        "row_number": i + 1,
                        "type": "employee_record"
                    }
                    
                    # 各列の情報を処理
                    for column in row.keys():
                        value = row[column]
                        if value:  # 空でない値を処理
                            employee_info.append(f"{column}: {value}")
                            
                            # 重要な情報をメタデータに追加
                            if column == "部署" or column == "所属部署":
                                metadata["department"] = str(value)
                            elif column == "社員名" or column == "氏名" or column == "名前":
                                metadata["employee_name"] = str(value)
                            elif column == "役職":
                                metadata["position"] = str(value)
                    
                    # 検索しやすい形式でテキストを作成
                    page_content = "\n".join(employee_info)
                    
                    # 部署情報を強調（検索精度向上のため）
                    if "department" in metadata:
                        # 🔥 修正: 人事部データの検索優先度を上げる
                        department = metadata['department']
                        if "人事部" in department:
                            # 人事部の場合、より強い検索キーワードを追加
                            page_content = f"【人事部所属社員】【人事部メンバー】【人事部スタッフ】\n【{department}所属】\n{page_content}\n人事部門勤務 人事担当者 人事関係者"
                        else:
                            page_content = f"【{department}所属】\n{page_content}"
                    
                    document = Document(
                        page_content=page_content,
                        metadata=metadata
                    )
                    documents.append(document)
                    
                    # 🔥 新機能: 部署別インデックスに追加
                    department = row.get('部署', '').strip()
                    if department:
                        if department not in department_index:
                            department_index[department] = []
                        department_index[department].append({
                            'employee_id': row.get('社員ID', ''),
                            'name': row.get('氏名（フルネーム）', ''),
                            'document_index': i
                        })
                
                # 🔥 新機能: 部署別サマリードキュメントを作成
                for dept, employees in department_index.items():
                    summary_content = f"""
【{dept}完全名簿】【{dept}全員リスト】【{dept}所属者一覧】
部署名: {dept}
所属人数: {len(employees)}名
所属員:
"""
                    for emp in employees:
                        summary_content += f"- {emp['employee_id']}: {emp['name']}\n"
                    
                    # 人事部の場合、さらに強力なキーワードを追加
                    if "人事部" in dept:
                        summary_content += f"""
【人事部門完全リスト】【人事部全社員】【人事部全メンバー】
人事部総員数: {len(employees)}名
COMPLETE_HR_ROSTER FULL_HR_LIST ALL_HR_MEMBERS
"""
                    
                    summary_doc = Document(
                        page_content=summary_content,
                        metadata={
                            "source": self.file_path,
                            "document_type": "department_summary",
                            "department": dept,
                            "employee_count": len(employees)
                        }
                    )
                    documents.append(summary_doc)
                
                self.logger.info(f"CSV読み込み成功: {len(rows)}行")
                self.logger.info(f"部署サマリー作成: {len(department_index)}部署")
                for dept, employees in department_index.items():
                    self.logger.info(f"{dept}: {len(employees)}名")
                    
        except Exception as e:
            self.logger.error(f"CSV読み込みエラー: {e}")
        
        return documents