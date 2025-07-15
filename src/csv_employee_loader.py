import os
import pandas as pd
from langchain_core.documents import Document

class EmployeeCSVLoader:
    def __init__(self, file_path, encoding="utf-8-sig"):
        self.file_path = file_path
        self.encoding = encoding

    def _detect_department_column(self, df):
        """部署に該当する列を検出する（明示候補 → 自動推測）"""
        possible_keys = ["部署", "部署名", "部門", "department"]
        for key in possible_keys:
            if key in df.columns:
                return key

        # 自動判定：列のいずれかに「◯◯部」という値が含まれていたら部署列とみなす
        for col in df.columns:
            if df[col].astype(str).str.contains(r".+部").any():
                return col

        raise ValueError(f"部署に該当する列が見つかりません（候補: {possible_keys}）")

    def _create_summary_document(self, df, dept_col):
        """部署別の社員数サマリーをDocumentで返す"""
        dept_summary = df[dept_col].value_counts().to_dict()
        summary_text = "社員数の部署別内訳は以下の通りです：\n"
        for dept, count in dept_summary.items():
            summary_text += f"- {dept}: {count}名\n"

        return Document(
            page_content=summary_text,
            metadata={
                "source": os.path.basename(self.file_path),
                "type": "summary"
            }
        )

    def _create_employee_documents(self, df, dept_col):
        """社員ごとのDocumentをリストで返す"""
        documents = []
        for idx, row in df.iterrows():
            row_data = ", ".join(f"{col}: {row[col]}" for col in df.columns)
            metadata = {
                "source": os.path.basename(self.file_path),
                "type": "employee",
                "department": row.get(dept_col, ""),
                "employee_id": idx
            }
            documents.append(Document(
                page_content=row_data,
                metadata=metadata
            ))
        return documents

    def load(self):
        documents = []
        try:
            df = pd.read_csv(self.file_path, encoding=self.encoding)
            df.columns = df.columns.str.strip()

            dept_col = self._detect_department_column(df)

            # ✅ サマリードキュメントを追加
            summary_doc = self._create_summary_document(df, dept_col)
            documents.append(summary_doc)

            # ✅ 社員ドキュメントを追加
            employee_docs = self._create_employee_documents(df, dept_col)
            documents.extend(employee_docs)

        except Exception as e:
            print(f"[ERROR] CSV読み込みに失敗: {self.file_path} → {e}")

        return documents