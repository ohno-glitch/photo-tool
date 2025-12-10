import streamlit as st
from rembg import remove
from PIL import Image, ImageEnhance, ImageFilter
import io

st.set_page_config(page_title="Product Studio AI", page_icon="📸", layout="wide")

# スタイル設定
st.markdown("""
<style>
    .stButton>button { width: 100%; background-color: #FF4B4B; color: white; font-weight: bold; border-radius: 10px; }
    .stDownloadButton>button { width: 100%; background-color: #00CC96; color: white; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# 影をつける関数
def add_shadow(image, x_offset, y_offset, blur_radius, shadow_opacity):
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    w, h = image.size
    canvas_w, canvas_h = w + 200, h + 200
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

# メイン画面
st.title("📸 Product Studio AI")
st.markdown("スマホ写真をアップロードして、**白背景・影付き**に変換します。")

with st.sidebar:
    st.header("🛠 調整オプション")
    shadow_opacity = st.slider("影の濃さ (%)", 0, 100, 60)
    blur_radius = st.slider("影のぼかし", 0, 50, 20)
    y_offset = st.slider("影の位置 (上下)", -50, 100, 30)
    x_offset = st.slider("影の位置 (左右)", -50, 50, 0)
    brightness = st.slider("明るさ補正", 0.5, 1.5, 1.05, 0.05)

uploaded_file = st.file_uploader("画像をアップロード", type=["png", "jpg", "jpeg"])

if uploaded_file:
    input_image = Image.open(uploaded_file).convert("RGBA")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original")
        st.image(input_image, use_column_width=True)
    
    with st.spinner("AIが加工中..."):
        no_bg = remove(input_image)
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(no_bg)
            no_bg = enhancer.enhance(brightness)
        final_img = add_shadow(no_bg, x_offset, y_offset, blur_radius, shadow_opacity)
        
        bg = Image.new("RGB", final_img.size, (255, 255, 255))
        bg.paste(final_img, (0, 0), final_img)

    with col2:
        st.subheader("Result")
        st.image(bg, use_column_width=True)
        buf = io.BytesIO()
        bg.save(buf, format="PNG")
        st.download_button("画像をダウンロード", buf.getvalue(), "studio_photo.png", "image/png")