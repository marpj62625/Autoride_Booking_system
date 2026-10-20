with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Verify where #desktopCameraModal CSS starts and ends
start = text.find('/* DESKTOP LIVE CAMERA / WEBCAM MODAL */')
end = text.find('/* Small screens bookings optimization */')
print("start:", start)
print("end:", end)
print("Snippet to move:")
print(text[start:end])
