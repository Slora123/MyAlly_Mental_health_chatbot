import base64
import os

def get_base64(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

login_base64 = get_base64("frontend/public/login-mockup.png")
bot_default_base64 = get_base64("frontend/public/assets/bot_default.png")
bot_male_base64 = get_base64("frontend/public/assets/bot_male.png")
bot_female_base64 = get_base64("frontend/public/assets/bot_female.png")

content = f"""
// Auto-generated Base64 images to bypass Hugging Face binary restrictions
export const loginMockup = "data:image/png;base64,{login_base64}";
export const botDefault = "data:image/png;base64,{bot_default_base64}";
export const botMale = "data:image/png;base64,{bot_male_base64}";
export const botFemale = "data:image/png;base64,{bot_female_base64}";
"""

with open("frontend/src/assets/images.js", "w") as f:
    f.write(content.strip() + "\\n")

print("Generated images.js with Base64 strings.")
