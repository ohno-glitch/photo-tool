import streamlit as st
from rembg import remove
from PIL import Image, ImageEnhance, ImageFilter
import io

st.set_page_config(page_title="Product Studio AI", page_icon="🎨", layout="wide")

# --- スタイル設定 ---
st.markdown("""
<style>
    .stButton>button { width: 100%; background-color: #FF4B4B; color: white; font-weight: bold; border-radius: 10px; }
    .stDownloadButton>button { width: 100%; background-color: #00CC96; color: white; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 画像処理関数 ---
def add_shadow(image, x_offset, y_offset, blur_radius, shadow_opacity):
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    w, h = image.size
    
    # 影が切れないようにキャンバスを少し大きくする
    canvas_w = w + 200
    canvas_h = h + 200
    base = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
    
    # 影レイヤー作成
    shadow = image.split()[-1]
    shadow_layer = Image.new('RGBA', shadow.size, (0, 0, 0, 0))
    shadow_color = (0, 0, 0, int(255 * (shadow_opacity / 100)))
    shadow_layer.paste(Image.new('RGBA', shadow.size, shadow_color), (0,0), shadow)
    
    # 影を配置してぼかす
    shadow_canvas = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
    shadow_canvas.paste(shadow_layer, (100 + x_offset, 100 + y_offset), shadow_layer)
    shadow_canvas = shadow_canvas.filter(ImageFilter.GaussianBlur(blur_radius))
    
    # 合成
    base.paste(shadow_canvas, (0, 0), shadow_canvas)
    base.paste(image, (100, 100), image)
    
    # 余白をカット（商品+影のギリギリのサイズにする）
    return base.crop(base.getbbox())

def resize_canvas_to_aspect_ratio(image, ratio_str, bg_color):
    """
    画像を、指定されたアスペクト比の背景の中央に配置する関数
    """
    # 比率の定義
    ratios = {
        "1:1": (1, 1),
        "9:16": (9, 16),
        "16:9": (16, 9),
        "3:4": (3, 4),
        "4:3": (4, 3),
        "3:2": (3, 2),
        "2:3": (2, 3),
        "5:4": (5, 4),
        "4:5": (4, 5),
        "21:9": (21, 9)
    }
    
    target_w_ratio, target_h_ratio = ratios.get(ratio_str, (1, 1))
    target_aspect = target_w_ratio / target_h_ratio
    
    img_w, img_h = image.size
    
    # 商品画像に少し余白（マージン）を持たせる (20%程度の余裕)
    # これにより、商品が画面いっぱいにパツパツになるのを防ぎます
    content_w = int(img_w * 1.2)
    content_h = int(img_h * 1.2)
    
    # 現在のコンテンツの比率
    content_aspect = content_w / content_h
    
    # キャンバスサイズを計算
    if content_aspect > target_aspect:
        # 商品が横長 → 横幅を基準に高さを決める
        final_w = content_w
        final_h = int(final_w / target_aspect)
    else:
        # 商品が縦長 → 高さを基準に横幅を決める
        final_h = content_h
        final_w = int(final_h * target_aspect)
        
    # 指定色の背景を作成
    bg = Image.new("RGB", (final_w, final_h), bg_color)
    
    # 中央に配置する座標を計算
    paste_x = (final_w - img_w) // 2
    paste_y = (final_h - img_h) // 2
    
    # 合成（透過情報を維持して貼り付け）
    bg.paste(image, (paste_x, paste_y), image)
    
    return bg

# --- メイン画面 ---
st.title("🎨 Product Studio AI")
st.markdown("スマホ写真をアップロードして、**好きなサイズ・背景色**の商品画像を作成します。")

# サイドバー設定
with st.sidebar:
    st.header("📐 画像サイズと背景")
    
    # アスペクト比選択
    aspect_ratio = st.selectbox(
        "画像サイズ (比率)",
        ["1:1", "9:16", "16:9", "3:4", "4:3", "3:2", "2:3", "5:4", "4:5", "21:9"]
    )
    
    bg_color = st.color_picker("背景色", "#FFFFFF")
    
    st.divider()
    
    st.header("🛠 影と明るさ")
    shadow_opacity = st.slider("影の濃さ (%)", 0, 100, 60)
    blur_radius = st.slider("影のぼかし", 0, 50, 20)
    y_offset = st.slider("影の位置 (上下)", -50, 100, 30)
    x_offset = st.slider("影の位置 (左右)", -50, 50, 0)
    brightness = st.slider("明るさ補正", 0.5, 1.5, 1.05, 0.05)

# ファイルアップロード
uploaded_file = st.file_uploader("画像をアップロード", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # 画像読み込み
    input_image = Image.open(uploaded_file).convert("RGBA")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original")
        st.image(input_image, use_column_width=True)
    
    with st.spinner("AIが加工中..."):
        # 1. 背景削除
        no_bg = remove(input_image)
        
        # 2. 明るさ調整
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(no_bg)
            no_bg = enhancer.enhance(brightness)
            
        # 3. 影をつける (まだ背景は透明のまま)
        product_with_shadow = add_shadow(no_bg, x_offset, y_offset, blur_radius, shadow_opacity)
        
        # 4. 指定されたアスペクト比の背景に配置
        final_image = resize_canvas_to_aspect_ratio(product_with_shadow, aspect_ratio, bg_color)

    with col2:
        st.subheader(f"Result ({aspect_ratio})")
        st.image(final_image, use_column_width=True)
        
        # ダウンロード
        buf = io.BytesIO()
        final_image.save(buf, format="PNG")
        st.download_button(
            label="画像をダウンロード",
            data=buf.getvalue(),
            file_name=f"product_{aspect_ratio.replace(':','-')}.png",
            mime="image/png"
        )
