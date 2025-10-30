from openai import OpenAI
import os
import base64
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEYが.envファイルに設定されていません")

client = OpenAI(api_key=api_key)

def load_role_from_file():
    """ロール設定をrole_fx.txtから読み込む"""
    try:
        with open("role_fx.txt", "r", encoding="utf-8") as role_file:
            role_content = role_file.read().strip()
        print("✓ ロール設定を 'role_fx.txt' から読み込みました。")
        return role_content
    except FileNotFoundError:
        print("⚠ role_fx.txt が見つかりません。デフォルトロールを使用します。")
        return "あなたは為替チャートを分析するエキスパートです。"

def get_image_mime_type(file_path):
    """ファイル拡張子からMIMEタイプを取得"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.png':
        return 'image/png'
    elif ext in ['.jpg', '.jpeg']:
        return 'image/jpeg'
    elif ext == '.gif':
        return 'image/gif'
    elif ext == '.webp':
        return 'image/webp'
    else:
        return 'image/png'  # デフォルト

def analyze_chart(image_path, analysis_prompt):
    try:
        # ロール設定を読み込み
        role_content = load_role_from_file()
        
        # 画像の存在確認
        if not os.path.exists(image_path):
            return f"エラー: 画像ファイルが見つかりません: {image_path}"
        
        # 画像のMIMEタイプを取得
        mime_type = get_image_mime_type(image_path)
        
        # 画像をbase64エンコードで読み込み
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        # ChatGPT APIを呼び出す（Vision APIを使用）
        response = client.chat.completions.create(
            model="gpt-4o",  # gpt-4oを使用（画像解析対応）
            messages=[
                {"role": "system", "content": role_content},
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text",
                            "text": analysis_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        # 応答を取得
        reply = response.choices[0].message.content
        return reply
    except Exception as e:
        return f"エラーが発生しました: {e}"
    
if __name__ == "__main__":
    print("=== チャート分析AI ===")
    
    # 使用するファイルのパス設定
    chart_image_path = input("分析したいチャート画像のパスを入力してください: ").strip()
    if not chart_image_path:
        chart_image_path = "./chart_image.png"
        print(f"デフォルトパスを使用します: {chart_image_path}")

    if not os.path.exists(chart_image_path):
        print(f"エラー: 画像ファイルが見つかりません: {chart_image_path}")
        exit(1)

    mime_type = get_image_mime_type(chart_image_path)
    with open(chart_image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')

    # チャットループ（プロンプトのみ）
    while True:
        prompt = input("\n分析のプロンプトを入力してください（終了するには「終了」と入力）: ").strip()
        if prompt.lower() == "終了":
            print("チャート分析を終了します。")
            break
        if not prompt:
            prompt = "このチャートの主要なトレンドとパターンを特定してください。"
            print(f"デフォルトプロンプトを使用します: {prompt}")

        # ユーザーの入力を履歴に追加
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}}
            ]
        })

        # API呼び出し
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=1000
            )
            reply = response.choices[0].message.content
            print("\n=== チャート分析結果 ===")
            print(reply)

            # 応答も履歴に追加
            messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            print(f"エラーが発生しました: {e}")