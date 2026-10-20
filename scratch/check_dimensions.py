from PIL import Image

im = Image.open('C:/Users/patri/.gemini/antigravity/brain/4a37b002-c7b6-4ad6-9112-d5047106cdff/.user_uploaded/media_1791988308392_19203d39.jpg')
print("Landscape screenshot dimensions:", im.size)

im_p = Image.open('C:/Users/patri/.gemini/antigravity/brain/4a37b002-c7b6-4ad6-9112-d5047106cdff/.user_uploaded/media_1791988305016_32953403.jpg')
print("Portrait screenshot dimensions:", im_p.size)
