def load_docx_files():
    """Docxファイルを読み込む"""
    docx_files = get_docx_file_list()  # DOCXファイルのリストを取得
    documents = []  # Documentオブジェクトのリスト

    for file_path in docx_files:
        try:
            text = extract_text_from_docx(file_path)  # DOCXファイルからテキストを抽出
            
            # 🔥 修正: 議事録ファイルの場合、メタデータでタイプを明示
            metadata = {"source": file_path}
            if "議事録" in file_path or "ミーティング" in file_path:
                metadata["document_type"] = "meeting_minutes"
                # 人事部という言葉が含まれていても、実際の人事部員データではないことを明示
                text = f"【会議議事録】{text}"
            
            doc = Document(page_content=text, metadata=metadata)
            documents.append(doc)
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    return documents