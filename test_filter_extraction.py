from src.filter_extraction_llm import extract_filters_from_text

if __name__ == "__main__":
    user_input = "営業チームの正社員について教えて"
    print("ユーザー入力:", user_input)

    result = extract_filters_from_text(user_input)

    print("抽出されたフィルタ条件:")
    print(result)