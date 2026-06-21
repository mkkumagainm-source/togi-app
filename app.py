import streamlit as st
import google.generativeai as genai
from PIL import Image
import numpy as np
import cv2

# 🔑 APIキーを設定
api_key = st.secrets["GEMINI_API_KEY"]

# APIの初期化
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    st.warning("APIキーが設定されていません。")

# 🖥️ 画面のデザイン設定
st.set_page_config(page_title="刃研ぎAI達人診断", page_icon="🪓", layout="centered")

st.title("🪓 刃研ぎAI達人診断システム")
st.caption("幾何学的な『職人の基準線』と『AI達人の言葉』を見比べて、自分の研ぎ方のクセを探究しよう！")

# 💡 達人プロンプト
SYS_PROMPT = """
あなたは中学校の技術家庭科（技術分野）における、木工用刃物（カンナやノミ）の「刃研ぎ」の達人先生です。
中学生の生徒が撮影した刃先の拡大画像（顕微鏡写真）を見て、温かく丁寧な言葉遣いでアドバイスを【3つの構成】で教えてください。

【注意点】
AIであるあなたの診断は100%完璧ではありません。光の反射などで誤診する可能性もあるため、文末は「〜に見えます」「〜の可能性があります」という確率的な表現に限定してください。

生徒たちが「次に手元をどう動かせばいいか」を具体的にイメージできるよう、必ず【数値的な指標（例：あと〇mm、〇往復、〇度など）】を交えて、100〜150文字程度で優しくアドバイスしてください。

以下の3つの構成（見出し）で出力してください：

■ 1. 達人の目（現在の状態を分析）
■ 2. 修正の目安（数値を使った具体的な目標値）
■ 3. 次のアクション（手元の動かし方のイメージと問いかけ）
"""

# 🗂️ 職人の2つの目を切り替える大タブ
view_tab1, view_tab2 = st.tabs(["👁️ 第1の目：刃線チェック（正面）", "👁️ 第2の目：しのぎ面チェック（真横）"])

image_to_analyze = None
active_mode = ""

# --- 👁️ 【大タブ1】刃線チェック（正面） ---
with view_tab1:
    st.markdown("### 🛠️ 正面から刃先の『直線度・片研ぎ』を見よう")
    
    # 🌟① 撮影前にラインのイメージを持たせるための「事前ガイド表示」
    st.markdown("#### 📸 撮影のコツ：画面のちょうど【真ん中】に刃先を水平に合わせて撮影してください。")
    
    # ダミーのプレビュー線を生成して見せる（生徒への視覚的指示）
    preview_line1 = np.ones((100, 500, 3), dtype=np.uint8) * 240
    cv2.line(preview_line1, (0, 50), (500, 50), (255, 0, 0), 4)
    st.image(preview_line1, caption="【狙う位置】この青い水平線に刃先を重ねるイメージで撮ろう！", use_container_width=True)

    sub_tab1, sub_tab2 = st.tabs(["📸 その場でカメラ撮影", "📂 保存したファイルを出す"])
    
    with sub_tab1:
        camera_image1 = st.camera_input("カメラに刃先を映してシャッターを押そう", key="cam_v1")
        if camera_image1:
            img = Image.open(camera_image1)
            img_array = np.array(img)
            h, w, _ = img_array.shape
            # 撮影された画像の中央に「青い水平線」を上書き
            cv2.line(img_array, (0, int(h * 0.5)), (w, int(h * 0.5)), (255, 0, 0), 4)
            st.image(img_array, caption="🔴 基準線（水平）とのズレを確認しよう", use_container_width=True)
            image_to_analyze = Image.fromarray(img_array)
            active_mode = "刃先の正面（直線度・左右の傾きチェック）"
            
    with sub_tab2:
        uploaded_file1 = st.file_uploader("刃先の画像ファイルを選んでね", type=["jpg", "jpeg", "png"], key="file_v1")
        if uploaded_file1:
            img = Image.open(uploaded_file1)
            img_array = np.array(img)
            h, w, _ = img_array.shape
            cv2.line(img_array, (0, int(h * 0.5)), (w, int(h * 0.5)), (255, 0, 0), 4)
            st.image(img_array, caption="🔴 基準線（水平）とのズレを確認しよう", use_container_width=True)
            image_to_analyze = Image.fromarray(img_array)
            active_mode = "刃先の正面（直線度・左右の傾きチェック）"

# --- 👁️ 【大タブ2】しのぎ面チェック（真横） ---
with view_tab2:
    st.markdown("### 🛠️ 真横からしのぎ面の『丸刃・研ぎ角』を見よう")
    
    # 🌟② 180度反転させた「事前ガイド表示」
    st.markdown("#### 📸 撮影のコツ：画面の【中央から右下】に向かう黄色の傾きに、刃の『しのぎ面』を合わせて撮影してください。")
    
    # 180度反転させた（右下がりの29度）プレビュー線を生成して見せる
    preview_line2 = np.ones((150, 500, 3), dtype=np.uint8) * 240
    # 右下がりの線を計算
    cv2.line(preview_line2, (250, 30), (250, 130), (255, 255, 0), 2) # 垂直背
    cv2.line(preview_line2, (250, 130), (350, 30), (255, 255, 0), 4) # 180度反転（右下がり斜面）
    st.image(preview_line2, caption="【狙う位置】この黄色の傾き（29度）に、刃の斜面を重ねるイメージで撮ろう！", use_container_width=True)

    sub_tab3, sub_tab4 = st.tabs(["📸 その場でカメラ撮影", "📂 保存したファイルを出す"])
    
    with sub_tab3:
        camera_image2 = st.camera_input("カメラに刃先を映してシャッターを押そう", key="cam_v2")
        if camera_image2:
            img = Image.open(camera_image2)
            img_array = np.array(img)
            h, w, _ = img_array.shape
            
            # 🌟② 180度反転（右下がりの適正研ぎ角29度）ラインを上書き描画
            center_x, center_y = int(w * 0.5), int(h * 0.7)
            angle_rad = np.radians(29)
            # 反転させるため、xの計算を「マイナス」から「プラス」に変更（右下がりに）
            end_x1 = int(center_x + h * 0.5 * np.tan(angle_rad))
            end_y1 = int(center_y - h * 0.5)
            
            cv2.line(img_array, (center_x, center_y), (end_x1, end_y1), (255, 255, 0), 4) # 180度反転斜線
            cv2.line(img_array, (center_x, center_y), (center_x, 0), (255, 255, 0), 2)     # 垂直の背
            
            st.image(img_array, caption="🟡 29度ガイドとのズレを確認しよう", use_container_width=True)
            image_to_analyze = Image.fromarray(img_array)
            active_mode = "刃先の真横（しのぎ面の丸み・29度角チェック）"
            
    with sub_tab4:
        uploaded_file2 = st.file_uploader("刃先の画像ファイルを選んでね", type=["jpg", "jpeg", "png"], key="file_v2")
        if uploaded_file2:
            img = Image.open(uploaded_file2)
            img_array = np.array(img)
            h, w, _ = img_array.shape
            
            # 🌟② ファイルアップロード側も同様に180度反転
            center_x, center_y = int(w * 0.5), int(h * 0.7)
            angle_rad = np.radians(29)
            end_x1 = int(center_x + h * 0.5 * np.tan(angle_rad))
            end_y1 = int(center_y - h * 0.5)
            
            cv2.line(img_array, (center_x, center_y), (end_x1, end_y1), (255, 255, 0), 4)
            cv2.line(img_array, (center_x, center_y), (center_x, 0), (255, 255, 0), 2)
            
            st.image(img_array, caption="🟡 29度ガイドとのズレを確認しよう", use_container_width=True)
            image_to_analyze = Image.fromarray(img_array)
            active_mode = "刃先の真横（しのぎ面の丸み・29度角チェック）"

# 🚀 診断ボタンの設置（共通）
st.write("---")
if image_to_analyze:
    st.success(f"【{active_mode}】の画像の準備ができました！")
    st.warning("⚠️ **生徒のみなさんへ:** 達人AIも光の反射などで時々間違えます。上の正確な基準線や、自分の目、手触りと比べて『本当かな？』と確かめてみよう！")
    
    if st.button("🧙‍♂️ 達人先生に診断してもらう", type="primary"):
        with st.spinner("達人先生が刃先をじっくり見ています..."):
            try:
                custom_prompt = f"現在の撮影視点：{active_mode}\n\n{SYS_PROMPT}"
                response = model.generate_content([custom_prompt, image_to_analyze])
                
                st.balloons()
                st.subheader("🧙‍♂️ 達人先生からのアドバイス")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"診断中にエラーが発生しました: {e}")
else:
    st.info("上のいずれかのタブから、カメラ撮影またはファイル選択で刃先の画像を用意してください。")