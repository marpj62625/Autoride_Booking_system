import os
from PIL import Image, ImageOps

def generate_playstore_assets():
    desktop_path = r"C:\Users\patri\OneDrive\Desktop"
    logo_path = os.path.join(desktop_path, "Autoride-logo.png")
    
    if not os.path.exists(logo_path):
        # Fallback to frontend directory logo
        logo_path = r"C:\Users\patri\OneDrive\Desktop\AutorideSystem2sides\AutorideSystem\frontend\Autoride-logo.png"
        
    if not os.path.exists(logo_path):
        print("Error: Autoride-logo.png not found!")
        return
        
    print(f"Loading logo from: {logo_path}")
    logo = Image.open(logo_path)
    
    # 1. Generate 512x512 App Icon
    # Create a 512x512 white or transparent canvas
    icon_size = (512, 512)
    # We will use white background to make it look clean, or transparent if original has transparency
    # Let's keep original format (RGBA)
    icon_canvas = Image.new("RGBA", icon_size, (255, 255, 255, 0))
    
    # Resize logo to fit inside 512x512 with some padding (e.g., 400x400)
    logo_resized = logo.copy()
    logo_resized.thumbnail((420, 420), Image.Resampling.LANCZOS)
    
    # Center the logo on the 512x512 canvas
    offset = ((512 - logo_resized.width) // 2, (512 - logo_resized.height) // 2)
    icon_canvas.paste(logo_resized, offset, logo_resized if logo_resized.mode == 'RGBA' else None)
    
    icon_output_path = os.path.join(desktop_path, "Autoride_PlayStore_Icon.png")
    icon_canvas.save(icon_output_path, "PNG")
    print(f"Saved Play Store Icon (512x512) to: {icon_output_path}")
    
    # 2. Generate 1024x500 Feature Graphic
    # Play Store feature graphic has a 1024x500 size. Let's use Autoride's green background gradient style.
    feature_size = (1024, 500)
    # Background color: #00B14F (Autoride green)
    feature_canvas = Image.new("RGBA", feature_size, (0, 177, 79, 255))
    
    # Resize logo to fit nicely in the feature graphic (e.g., height of 280)
    logo_feature = logo.copy()
    logo_feature.thumbnail((600, 280), Image.Resampling.LANCZOS)
    
    # Center the logo on the 1024x500 canvas
    offset_feature = ((1024 - logo_feature.width) // 2, (500 - logo_feature.height) // 2)
    feature_canvas.paste(logo_feature, offset_feature, logo_feature if logo_feature.mode == 'RGBA' else None)
    
    feature_output_path = os.path.join(desktop_path, "Autoride_PlayStore_Feature.png")
    feature_canvas.save(feature_output_path, "PNG")
    print(f"Saved Play Store Feature Graphic (1024x500) to: {feature_output_path}")

if __name__ == "__main__":
    generate_playstore_assets()
