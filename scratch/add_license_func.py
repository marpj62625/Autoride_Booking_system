with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

# Add viewLicenseImage function right before the closing </script> tag
# Find a good injection point - after the last function definition
func_code = """
    function viewLicenseImage(url) {
        var modal = document.getElementById('licensePreviewModal');
        var img = document.getElementById('licensePreviewImg');
        if (modal && img) {
            img.src = url;
            modal.style.display = 'flex';
        }
    }
"""

# Insert before </script>
# Find the last </script> tag
idx = content.rfind('</script>')
if idx >= 0:
    content = content[:idx] + func_code + '\n' + content[idx:]
    with open('admin_mobile/www/index.html', 'w', encoding='latin-1') as f:
        f.write(content)
    print("SUCCESS: viewLicenseImage function added")
else:
    print("ERROR: Could not find </script> tag")
