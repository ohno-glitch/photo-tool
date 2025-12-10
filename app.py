import streamlit as st
from rembg import remove
from PIL import Image, ImageEnhance, ImageFilter
import io
import requests # 画像ダウンロード用

st.set_page_config(page_title="Product Studio AI", page_icon="🎨", layout="wide")

# --- スタイル設定 ---
st.markdown("""
<style>
    .stButton>button { width: 100%; background-color: #FF4B4B; color: white; font-weight: bold; border-radius: 10px; }
    .stDownloadButton>button { width: 100%; background-color: #00CC96; color: white; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- AI背景生成関数 (Pollinations.aiを使用) ---
def generate_ai_background(prompt, width, height):
    # 日本語のプロンプトだと精度が落ちることがあるので、簡単な英語補足をつけるのがコツ
    # URLにリクエストするだけで画像が返ってくる魔法のAPI
    url = f"https://image.pollinations.ai/prompt/{prompt}?width={width}&height={height}&nologo=true&enhance=true"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content)).convert("RGBA")
        else:
            return None
    except:
        return None

# --- 画像処理関数 ---
def add_shadow(image, x_offset, y_offset, blur_radius, shadow_opacity):
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    w, h = image.size
    
    canvas_w = w + 200
    canvas_h = h + 200
    base = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
    
    shadow = image.split()[-1]
    shadow_layer = Image.new('RGBA', shadow.size, (0, 0, 0, 0))
    shadow_color = (0, 0, 0, int(255 * (shadow_opacity / 100)))
    shadow_layer.paste(Image.new('RGBA', shadow.size, shadow_color), (0,0), shadow)
    
    shadow_canvas = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
    shadow_canvas.paste(shadow_layer, (100 + x_offset, 100 + y_offset), shadow_layer)
    shadow_canvas = shadow_canvas.filter(ImageFilter.GaussianBlur(blur_radius))
    
    base.paste(shadow_canvas, (0, 0), shadow_canvas)
    base.paste(image, (100, 100), image)
    
    return base.crop(base.getbbox())

def composite_image(product_img, aspect_ratio_str, bg_type, bg_color, ai_bg_image):
    """
    商品を背景（単色 or AI画像）に合成する関数
    """
    # 比率定義
    ratios = {
        "1:1": (1, 1), "9:16": (9, 16), "16:9": (16, 9),
        "3:4": (3, 4), "4:3": (4, 3), "3:2": (3, 2),
        "2:3": (2, 3), "5:4": (5, 4), "4:5": (4, 5), "21:9": (21, 9)
    }
    
    target_w_ratio, target_h_ratio = ratios.get(aspect_ratio_str, (1, 1))
    target_aspect = target_w_ratio / target_h_ratio
    
    img_w, img_h = product_img.size
    
    # 商品の配置サイズ計算（少し余白をもたせる）
    content_w = int(img_w * 1.2)
    content_h = int(img_h * 1.2)
    content_aspect = content_w / content_h
    
    # キャンバス（背景）の絶対サイズを計算
    # 画質を保つため、商品のサイズを基準にキャンバスを広げる
    if content_aspect > target_aspect:
        final_w = content_w
        final_h = int(final_w / target_aspect)
    else:
        final_h = content_h
        final_w = int(final_h * target_aspect)
        
    # --- 背景の作成 ---
    if bg_type == "AI生成画像" and ai_bg_image is not None:
        # AI画像をキャンバスサイズにリサイズして使用
        bg = ai_bg_image.resize((final_w, final_h), Image.LANCZOS).convert("RGB")
    else:
        # 単色背景
        bg = Image.new("RGB", (final_w, final_h), bg_color)
    
    # 商品を中央に配置
    paste_x = (final_w - img_w) // 2
    paste_y = (final_h - img_h) // 2
    
    bg.paste(product_img, (paste_x, paste_y), product_img)
    
    return bg

# --- メイン画面 ---
st.title("🎨 Product Studio AI")
st.markdown("商品をアップロードし、**好きなプロンプト**で背景を作成できます。")

# サイドバー設定
with st.sidebar:
    st.header("📐 画像設定")
    aspect_ratio = st.selectbox(
        "画像比率",
        ["1:1", "9:16", "16:9", "3:4", "4:3", "3:2", "2:3", "5:4", "4:5", "21:9"]
    )
    
    st.divider()
    
    st.header("🎨 背景の設定")
    bg_type = st.radio("背景の種類", ["単色カラー", "AI生成画像"])
    
    ai_bg_image = None # 初期化
    bg_color = "#FFFFFF" # 初期化
    
    if bg_type == "単色カラー":
        bg_color = st.color_picker("背景色", "#FFFFFF")
        
    else:
        st.info("どんな背景に置きたいですか？")
        prompt_text = st.text_area("プロンプト (例: wooden table in a cafe, sunlight)", height=100)
        
        # 自動生成ボタン
        if st.button("背景を生成する 🎲"):
            if prompt_text:
                with st.spinner("AIが背景を描いています..."):
                    # 画質確保のため大きめのサイズで生成
                    ai_bg_image = generate_ai_background(prompt_text, 1024, 1024)
                    if ai_bg_image:
                        st.success("生成完了！")
                        # プレビュー表示
                        st.image(ai_bg_image, caption="生成された背景", use_column_width=True)
                    else:
                        st.error("生成に失敗しました。もう一度試してください。")
            else:
                st.warning("プロンプトを入力してください")

    st.divider()
    
    st.header("🛠 影と明るさ")
    shadow_opacity = st.slider("影の濃さ", 0, 100, 60)
    blur_radius = st.slider("影のぼかし", 0, 50, 20)
    y_offset = st.slider("影の位置 (上下)", -50, 100, 30)
    brightness = st.slider("明るさ補正", 0.5, 1.5, 1.05, 0.05)

# メインエリア
uploaded_file = st.file_uploader("商品画像をアップロード", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # 画像読み込み
    input_image = Image.open(uploaded_file).convert("RGBA")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original")
        st.image(input_image, use_column_width=True)
    
    # リアルタイム合成処理
    # ※AI背景モードのときは、背景生成ボタンが押されて ai_bg_image がある場合のみ合成
    if bg_type == "単色カラー" or (bg_type == "AI生成画像" and ai_bg_image is not None):
        with st.spinner("合成中..."):
            # 1. 背景削除
            no_bg = remove(input_image)
            
            # 2. 明るさ調整
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(no_bg)
                no_bg = enhancer.enhance(brightness)
                
            # 3. 影をつける
            product_with_shadow = add_shadow(no_bg, 0, y_offset, blur_radius, shadow_opacity)
            
            # 4. 選んだ背景（色 or AI画像）と合成
            final_image = composite_image(product_with_shadow, aspect_ratio, bg_type, bg_color, ai_bg_image)

        with col2:
            st.subheader("Result")
            st.image(final_image, use_column_width=True)
            
            # ダウンロード
            buf = io.BytesIO()
            final_image.save(buf, format="PNG")
            st.download_button(
                label="完成画像をダウンロード",
                data=buf.getvalue(),
                file_name="ai_studio_photo.png",
                mime="image/png"
            )
    elif bg_type == "AI生成画像" and ai_bg_image is None:
        with col2:
            st.info("👈 左のサイドバーでプロンプトを入力して「背景を生成」ボタンを押してください。")
