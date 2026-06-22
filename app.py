import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw
import numpy as np

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

# 🔥【超奥の手】JavaScriptを使って、カメラ映像(video)を見つけ次第、その直上にラインを動的挿入する
st.components.v1.html("""
<script>
function injectGuideLines() {
    // Streamlitのカメラコンポーネント内にあるvideo要素をすべて探す
    const videos = parent.document.querySelectorAll('video');
    
    videos.forEach((video) => {
        // すでにガイド線が挿入済みならスキップ
        if (video.parentElement.querySelector('.js-guide-line')) return;
        
        // 親要素の配置を基準(relative)にする
        video.parentElement.style.position = 'relative';
        
        // カメラの直上に重ねるオーバーレイ要素を作成
        const overlay = parent.document.createElement('div');
        overlay.className = 'js-guide-line';
        overlay.style.position = 'absolute';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100%';
        overlay.style.height = '100%';
        overlay.style.pointerEvents = 'none'; // クリック（シャッター）を邪魔しない
        overlay.style.zIndex = '9999';
        
        // このカメラが「タブ1（正面）」か「タブ2（真横）」かを判定
        // Streamlitの大タブの構造を解析して線を切り替える
        const isSideView = video.closest('.stTabs') && video.closest('[data-baseweb="tab-panel"]')?.id?.includes('tabpanel-1');
        
        if (!isSideView) {
            // 🔴 正面用：中央に赤い水平線
            const line = parent.document.createElement('div');
            line.style.position = 'absolute';
            line.style.top = '50%';
            line.style.left = '0';
            line.style.width = '100%';
            line.style.height = '4px';
            line.style.backgroundColor = 'rgba(255, 0, 0, 0.6)';
            overlay.appendChild(line);
        } else {
            // 🟡 真横用：中央に垂直の背 ＋ 29度の斜線
            // 垂直の背
            const verticalLine = parent.document.createElement('div');
            verticalLine.style.position = 'absolute';
            verticalLine.style.top = '15%';
            verticalLine.style.left = '50%';
            verticalLine.style.width = '2px';
            verticalLine.style.height = '45%';
            verticalLine.style.backgroundColor = 'rgba(255, 255, 0, 0.6)';
            overlay.appendChild(verticalLine);
            
            // 29度のしのぎ面ガイド
            const slantLine = parent.document.createElement('div');
            slantLine.style.position = 'absolute';
            slantLine.style.top = '35%';
            slantLine.style.left = '50%';
            slantLine.style.width = '40%';
            slantLine.style.height = '4px';
            slantLine.style.backgroundColor = 'rgba(255, 255, 0, 0.75)';
            slantLine.style.transformOrigin = 'top left';
            slantLine.style.transform = 'rotate(29deg)';
            overlay.appendChild(slantLine);
        }
        
        // video要素のすぐ後ろ（手前側）にオーバーレイを挿入
        video.parentElement.appendChild(overlay);
    });
}

// カメラの起動にはラグがあるため、定期的に画面を監視して線を埋め込む（1秒毎）
setInterval(injectGuideLines, 1000);
</script>
""", height=0)

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
    st.info("📸 画面のカメラ映像に重なっている【赤い水平線】に、刃先をピタッと重ねて撮影してください！")
    
    sub_tab1, sub_tab2 = st.tabs(["📸 その場でカメラ撮影", "📂 保存したファイルを出す"])
    
    with sub_tab1:
        camera_image1 = st.camera_input("カメラに刃先を映してシャッターを押そう", key="cam_v1")
        if camera_image1:
            img = Image.open(camera_image1).convert("RGB")
            draw = ImageDraw.Draw(img)
            w, h = img.size
            draw.line([(0, h // 2), (w, h // 2)], fill=(255, 0, 0), width=6)
            st.image(img, caption="🔴 撮影完了！赤い基準線とのズレを最終確認しよう", use_container_width=True)
            image_to_analyze = img
            active_mode = "刃先の正面（直線度・左右の傾きチェック）"
            
    with sub_tab2:
        uploaded_file1 = st.file_uploader("刃先の画像ファイルを選んでね", type=["jpg", "jpeg", "png"], key="file_v1")
        if uploaded_file1:
            img = Image.open(uploaded_file1).convert("RGB")
            draw = ImageDraw.Draw(img)
            w, h = img.size
            draw.line([(0, h // 2), (w, h // 2)], fill=(255, 0, 0), width=6)
            st.image(img, caption="🔴 基準線（水平）とのズレを確認しよう", use_container_width=True)
            image_to_analyze = img
            active_mode = "刃先の正面（直線度・左右の傾きチェック）"

# --- 👁️ 【大タブ2】しのぎ面チェック（真横） ---
with view_tab2:
    st.markdown("### 🛠️ 真横からしのぎ面の『丸刃・研ぎ角』を見よう")
    st.info("📸 画面のカメラ映像に重なっている【黄色の29度ガイド】の傾きに、刃の『しのぎ面』を重ねて撮影してください！")
    
    sub_tab3, sub_tab4 = st.tabs(["📸 その場でカメラ撮影", "📂 保存したファイルを出す"])
    
    with sub_tab3:
        camera_image2 = st.camera_input("カメラに刃先を映してシャッターを押そう", key="cam_v2")
        if camera_image2:
            img = Image.open(camera_image2).convert("RGB")
            draw = ImageDraw.Draw(img)
            w, h = img.size
            
            center_x, center_y = int(w * 0.5), int(h * 0.7)
            angle_rad = np.radians(29)
            end_x1 = int(center_x + h * 0.5 * np.tan(angle_rad))
            end_y1 = int(center_y - h * 0.5)
            
            draw.line([(center_x, center_y), (end_x1, end_y1)], fill=(255, 255, 0), width=6)
            draw.line([(center_x, center_y), (center_x, 0)], fill=(255, 255, 0), width=3)
            
            st.image(img, caption="🟡 撮影完了！29度ガイドとのズレを最終確認しよう", use_container_width=True)
            image_to_analyze = img
            active_mode = "刃先の真横（しのぎ面の丸み・29度角チェック）"
            
    with sub_tab4:
        uploaded_file2 = st.file_uploader("刃先の画像ファイルを選んでね", type=["jpg", "jpeg", "png"], key="file_v2")
        if uploaded_file2:
            img = Image.open(uploaded_file2).convert("RGB")
            draw = ImageDraw.Draw(img)
            w, h = img.size
            
            center_x, center_y = int(w * 0.5), int(h * 0.7)
            angle_rad = np.radians(29)
            end_x1 = int(center_x + h * 0.5 * np.tan(angle_rad))
            end_y1 = int(center_y - h * 0.5)
            
            draw.line([(center_x, center_y), (end_x1, end_y1)], fill=(255, 255, 0), width=6)
            draw.line([(center_x, center_y), (center_x, 0)], fill=(255, 255, 0), width=3)
            
            st.image(img, caption="🟡 29度ガイドとのズレを確認しよう", use_container_width=True)
            image_to_analyze = img
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