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

# 🔥【超重要】CSSを使って、それぞれのカメラ画面（cam_v1 / cam_v2）の上に固有のリアルタイムラインを重ねる
st.markdown("""
<style>
/* --- 共通設定: カメラ入力の親要素を相対配置にして重なり順を制御 --- */
div[data-testid="stCameraInput"] {
    position: relative;
}

/* --- ① タブ1（正面・cam_v1）用の赤い水平線 --- */
/* key="cam_v1" のカメラ入力の後ろに疑似要素で赤線を配置 */
div:has(> div[data-testid="stCameraInput"] button[key="cam_v1"])::after {
    content: "";
    position: absolute;
    top: 52%; /* Take Photoボタンとの兼ね合いで中央付近に微調整 */
    left: 0;
    width: 100%;
    height: 4px;
    background-color: rgba(255, 0, 0, 0.6); /* 透過度60%の赤線 */
    z-index: 99;
    pointer-events: none;
}

/* --- ② タブ2（真横・cam_v2）用の黄色の29度くさび線（180度反転・右下がり） --- */
/* 背（垂直線） */
div:has(> div[data-testid="stCameraInput"] button[key="cam_v2"])::after {
    content: "";
    position: absolute;
    top: 15%;
    left: 50%;
    width: 2px;
    height: 45%;
    background-color: rgba(255, 255, 0, 0.5); /* 透過度50%の黄線 */
    z-index: 98;
    pointer-events: none;
}
/* しのぎ面（右下がりの斜線） */
div:has(> div[data-testid="stCameraInput"] button[key="cam_v2"])::before {
    content: "";
    position: absolute;
    top: 35%;
    left: 50%;
    width: 35%;
    height: 4px;
    background-color: rgba(255, 255, 0, 0.7); /* 透過度70%の太い黄線 */
    z-index: 99;
    transform: rotate(29deg); /* 29度右下がりに傾ける */
    transform-origin: top left;
    pointer-events: none;
}
</style>
""", unsafe_allow_html=True)

st.title("🪓 刃研ぎAI達人診断システム")
st.caption("幾何学的な『職人の基準線』と『AI達人の言葉』を見比べて、自分の研ぎ方のクセを探究しよう！")

# 💡 達人プロンプト
SYS_PROMPT = """
あなたは中学校の技術家庭科（技術分野）における、木工用刃物（カンナやノミ）の「刃研ぎ」の達人先生です。
中学生の生徒が撮影した刃先の拡大画像（顕微鏡写真）を見て、温かく丁寧な言葉遣いでアドバイスを【3つの構成】で教えてください。

【注意点】
AIであるあなたの診断は100%完璧ではありません。文末は「〜に見えます」「〜の可能性があります」という確率的な表現に限定してください。
必ず【数値的な指標（例：あと〇mm、〇往復、〇度など）】を交えて、100〜150文字程度で優しくアドバイスしてください。

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
    st.info("📸 画面に見えている【赤い水平線】に、刃先をピタッと重ねて撮影してください！")
    
    sub_tab1, sub_tab2 = st.tabs(["📸 その場でカメラ撮影", "📂 保存したファイルを出す"])
    
    with sub_tab1:
        camera_image1 = st.camera_input("カメラに刃先を映してシャッターを押そう", key="cam_v1")
        if camera_image1:
            img = Image.open(camera_image1)
            img_array = np.array(img)
            h, w, _ = img_array.shape
            cv2.line(img_array, (0, int(h * 0.5)), (w, int(h * 0.5)), (255, 0, 0), 4)
            st.image(img_array, caption="🔴 撮影完了！基準線とのズレを最終確認しよう", use_container_width=True)
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
    st.info("📸 画面に見えている【黄色の29度ガイド】の傾きに、刃の『しのぎ面』を重ねて撮影してください！")
    
    sub_tab3, sub_tab4 = st.tabs(["📸 その場でカメラ撮影", "📂 保存したファイルを出す"])
    
    with sub_tab3:
        camera_image2 = st.camera_input("カメラに刃先を映してシャッターを押そう", key="cam_v2")
        if camera_image2:
            img = Image.open(camera_image2)
            img_array = np.array(img)
            h, w, _ = img_array.shape
            
            # 撮影後画像への確定線（右下がりの適正研ぎ角29度）
            center_x, center_y = int(w * 0.5), int(h