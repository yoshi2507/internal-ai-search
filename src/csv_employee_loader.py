from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
import logging
import constants as ct  # . を削除

class EmployeeCSVLoader(BaseLoader):
    """
    社員名簿CSVを読み込むためのカスタムローダー。
    以下の2種類のドキュメントを生成します。
    1. 部署ごとのサマリードキュメント
    2. 各従業員ごとの詳細ドキュメント
    """

    def __init__(self, file_path: str, encoding: str = "utf-8"):
        self.file_path = file_path
        self.encoding = encoding

    def load(self) -> list[Document]:
        logger = logging.getLogger(ct.LOGGER_NAME)
        documents = []
        try:
            df = pd.read_csv(self.file_path, encoding=self.encoding)
            
            # 1. 部署ごとのサマリードキュメントを作成
            for department, group in df.groupby('department'):
                member_list = "\n".join([f"- {row['full_name']} (社員ID: {row['employee_id']})" for _, row in group.iterrows()])
                summary_content = (
                    f"【部署名簿】\n"
                    f"部署名: {department}\n"
                    f"所属人数: {len(group)}名\n\n"
                    f"所属メンバー一覧:\n{member_list}"
                )
                documents.append(Document(
                    page_content=summary_content,
                    metadata={"source": self.file_path, "type": "department_summary", "department": department}
                ))

            # 2. 各従業員ごとの詳細ドキュメントを作成
            for _, row in df.iterrows():
                employee_content = "【従業員情報】\n"
                for col, value in row.items():
                    employee_content += f"{col}: {value}\n"
                
                documents.append(Document(
                    page_content=employee_content,
                    metadata={"source": self.file_path, "type": "employee_detail", "employee_id": row['employee_id'], "department": row['department']}
                ))
            
            logger.info(f"'{self.file_path}' から {len(documents)} 件のドキュメントを読み込みました（部署サマリー含む）。")

        except Exception as e:
            logger.error(f"CSVファイルの読み込みに失敗しました: {self.file_path}, エラー: {e}")
        
        return documents