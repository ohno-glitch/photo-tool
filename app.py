import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# --- ページ設定 ---
st.set_page_config(page_title="AI Product Generator", page_icon="🍌", layout="wide")

# --- APIキーの読み込み（Secretsから） ---
# GitHubにキーを書かずに、安全に読み込みます
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except FileNotFoundError:
    st.error("APIキーが設定されていません。Streamlit CloudのSecretsに 'GEMINI_API_KEY' を設定してください。")
    st.stop()

# --- 生成設定 ---
# ※ここでモデルを指定します。
# もし 'gemini-2.5' が使えない場合は 'gemini-1.5-flash' などに変更してください
VISION_MODEL = "gemini-1.5-flash" 
IMAGE_MODEL = "imagen-3.0-generate-001" # 画像生成用モデル

st.title("🍌 Nano Banana Pro (GenAI Version)")
st.markdown("スマホ写真をアップロードすると、AIが**「正面向き・白背景」**の商品画像として再生成します。")

# --- メイン処理 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📤 オリジナル写真")
    uploaded_file = st.file_uploader("商品画像をアップロード", type=["png", "jpg", "jpeg"])

if uploaded_file:
    input_image = Image.open(uploaded_file)
    with col1:
        st.image(input_image, use_column_width=True)

    # 生成ボタン
    if st.button("✨ 正面向きで生成する", type="primary"):
        with col2:
            st.subheader("🎨 AI生成結果")
            status_text = st.empty()
            
            try:
                # 1. 画像の説明文（プロンプト）を作る
                status_text.info("👀 商品を観察中... (Gemini 1.5 Flash)")
                
                vision_model = genai.GenerativeModel(VISION_MODEL)
                prompt_instruction = """
                Describe this product in extreme detail. 
                Focus on the brand logo, colors, materials, and shape.
                Do NOT describe the background or angle. Just the object itself.
                """
                response = vision_model.generate_content([prompt_instruction, input_image])
                description = response.text
                
                # 2. 画像を生成する
                status_text.info("🖌️ 正面アングルで描画中... (Imagen 3)")
                
                imagen_model = genai.GenerativeModel(IMAGE_MODEL)
                
                # 「正面向き、白背景」という指示を追加
                generation_prompt = f"""
                Professional product photography of {description}.
                Front view, perfectly centered, facing forward directly.
                Pure white background. Soft studio lighting. 4k resolution.
                Minimalist, clean.
                """
                
                # 画像生成を実行
                result = imagen_model.generate_images(
                    prompt=generation_prompt,
                    number_of_images=1,
                    aspect_ratio="1:1",
                    safety_filter="block_only_high",
                )
                
                # 表示
                generated_image = result.images[0]._pil_image
                st.image(generated_image, use_column_width=True)
                status_text.success("✨ 完成しました！")
                
                # ダウンロードボタン
                buf = io.BytesIO()
                generated_image.save(buf, format="PNG")
                st.download_button("画像を保存", buf.getvalue(), "ai_product.png", "image/png")

            except Exception as e:
                status_text.error("エラーが発生しました")
                st.error(f"詳細: {e}")
                
                if "Quota exceeded" in str(e):
                    st.warning("⚠️ 無料枠の上限を超えたか、このモデルへのアクセス権がありません。Google Cloudで課金設定を確認してください。")
                elif "not found" in str(e):
                    st.warning(f"⚠️ モデル {IMAGE_MODEL} が見つかりません。APIキーが対応していない可能性があります。")
