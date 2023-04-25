# Import necessary packages
import openai
import os
import requests
import io
import base64
from PIL import Image, PngImagePlugin
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QFormLayout, QLineEdit, QPushButton

# Initialize the OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

# Define a function to retrieve the text and store it in the variable
def get_text():
    global UserInputVar


# Define a function to get GPT outputs
def askGPT(text):
    response = openai.Completion.create(
        engine = "text-davinci-003",
        prompt = text,
        temperature = 0.6,
        max_tokens = 150
    )
    return response.choices[0].text

# Prompt that gets sent to SD
def sd(input):

    # Link to SD 
    url = "http://127.0.0.1:7860"

    # Settings and vairables for SD
    payload = {
    "prompt": input,
    "seed": -1,
    "batch_size": 1,
    "n_iter": 1,
    "steps": 20,
    "cfg_scale": 7,
    "width": 512,
    "height": 512,
    "tiling": True
    }

    # Sets the modes to one trained on 
    option_payload = {
        "sd_model_checkpoint": "TextureDiffusion_10.ckpt [ded387e0f3]"
    }

    response = requests.post(url=f'{url}/sdapi/v1/options', json=option_payload)
    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)

    r = response.json()

    for i in r['images']:
        image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

        png_payload = {
            "image": "data:image/png;base64," + i
        }
        response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)

        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("parameters", response2.json().get("info"))
        image.save('C:/Users/matth/Desktop/texture.png', pnginfo=pnginfo)



# Define a function to generate GPT outputs and print it
def gpt():
    TextureName = ["", "", "", "", ""]
    UserInputVar = edit1.text()
    print(UserInputVar)
    TextureName[0] = askGPT(f"give 1 word relating to a material found in {UserInputVar}")
    TextureName[1] = askGPT(f"give 1 word relating to a material found in {UserInputVar} that is not {TextureName}")
    TextureName[2] = askGPT(f"give 1 word relating to a material found in {UserInputVar} that is not {TextureName}")
    TextureName[3] = askGPT(f"give 1 word relating to a material found in {UserInputVar} that is not {TextureName}")
    TextureName[4] = askGPT(f"give 1 word relating to a material found in {UserInputVar} that is not {TextureName}")

    print(TextureName)
    sd(TextureName[0])

# Create the UI for user input
if __name__ == "__main__":
    # Create app window
    app = QApplication(sys.argv)
    w = QWidget()
    w.resize(1000, 500)
    w.setWindowTitle("Imgage Generation Tool")

    # Set the layout
    layout = QFormLayout()

    # Create label and text field for user input
    label1 = QLabel('Enter setting(i.e zombie apocalypse/space ship):')
    edit1 = QLineEdit()

    # Create the variable to store the text
    UserInputVar = ''

    # Create a button to generate GPT outputs
    btn1 = QPushButton('Generate')
    btn1.clicked.connect(gpt)

    # Add widgets to the layout
    layout.addRow(label1, edit1)
    layout.addRow(btn1)
    w.setLayout(layout)

    w.show()
    sys.exit(app.exec_())




