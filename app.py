import streamlit as st
import google.generativeai as genai
from PIL import Image

# 🔑 APIキーを設定（あなたの本物のキーに書き換えてください）
api_key = st.secrets["GEMINI_API_KEY"]

# APIの初期化
if api_key:
    genai.configure(api_key=api_key)
    # 最新の2.5モデルを使用
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    st.warning("APIキーが設定されていません。")

# 🖥️ 画面のデザイン設定
st.set_page_config(page_title="刃研ぎAI達人診断", page_icon="🪓", layout="centered")

st.title("🪓 刃研ぎAI達人診断システム")
st.caption("顕微鏡で撮影した刃先の画像から、研ぎの状態をAI達人が診断します。")

# 💡 生徒が具体的に手元をイメージできる「数値入り＆丁寧な達人プロンプト」
SYS_PROMPT = """
あなたは中学校の技術家庭科（技術分野）における、木工用刃物（カンナやノミ）の「刃研ぎ」の達人先生です。
中学生の生徒が撮影した刃先の拡大画像（顕微鏡写真）を見て、温かく丁寧な言葉遣いでアドバイスを【3つの構成】で教えてください。

生徒たちが「次に手元をどう動かせばいいか」を具体的にイメージできるよう、必ず【数値的な指標（例：あと〇mm、〇往復、〇度など）】を交えて、100〜150文字程度で優しくアドバイスしてください。

以下の3つの構成（見出し）で出力してください：

■ 1. 達人の目（現在の状態を褒めつつ分析）
（例：お、しのぎ面が平らに光ってきているね！ただ、刃先から1mmほどのところに、ほんの少し丸刃の傾向が見られます。）

■ 2. 修正の目安（数値を使った具体的な目標値）
（例：今の研ぎ角（約28度）は少し立ちすぎているので、あと2度ほど寝かせて、約26度を狙うと劇的に切れ味が変わるよ。）

■ 3. 次のアクション（手元の動かし方のイメージ）
（例：砥石の上をあと10往復、刃の右側に20%くらい多めに力を意識してスーッと前後に動かしてみよう。仕上げに裏押しを2〜3回、力を入れずに引けば完璧だよ！）
"""

# 🗂️ タブ機能を使って「カメラで撮影」と「ファイルを出す」をスッキリ分ける
tab1, tab2 = st.tabs(["📸 その場でカメラ撮影", "📂 保存したファイルを出す"])

image_to_analyze = None

with tab1:
    st.write("▼ パソコンに顕微鏡を繋いで撮影する場合はこちら")
    st.info("※顕微鏡カメラが映らない場合は、ブラウザのカメラ許可設定（アドレスバーの左の鍵マーク）から、接続先カメラ（デバイス）を切り替えてみてください。")
    camera_image = st.camera_input("カメラに刃先を映してシャッターを押そう")
    if camera_image:
        image_to_analyze = Image.open(camera_image)

with tab2:
    st.write("▼ 事前に顕微鏡ソフトなどで保存した画像を使う場合はこちら")
    uploaded_file = st.file_uploader("刃先の画像ファイル（.jpg, .png）を選んでね", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image_to_analyze = Image.open(uploaded_file)
        # アップロードされた画像を画面に小さく表示
        st.image(image_to_analyze, caption="読み込んだ刃先画像", use_container_width=True)

# 🚀 診断ボタンの設置
if image_to_analyze:
    st.success("画像の準備ができました！")
    if st.button("🧙‍♂️ 達人先生に診断してもらう", type="primary"):
        with st.spinner("達人先生が刃先をじっくり見ています..."):
            try:
                # AIに画像とプロンプトを送って診断を依頼
                response = model.generate_content([SYS_PROMPT, image_to_analyze])
                
                # 🎈 診断結果をスッキリ表示
                st.balloons()
                st.subheader("🧙‍♂️ 達人先生からのアドバイス")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"診断中にエラーが発生しました: {e}")
else:
    st.info("上の「カメラ撮影」または「ファイルの選択」で刃先の画像を用意してください。")