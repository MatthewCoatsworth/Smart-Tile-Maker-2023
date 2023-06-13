"""This Python file contains a graphical user interface (GUI) tool for generating texture names and images using the Stable Diffusion (SD) and GPT-3 models."""
# Import necessary packages
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QFormLayout, 
                             QLineEdit, QPushButton, QGroupBox, QFileDialog, 
                             QMainWindow, QMessageBox)
from PyQt5.QtCore import QUrl
from requests.exceptions import RequestException
from PyQt5.QtGui import QDesktopServices
from PIL import Image, PngImagePlugin
import openai
import os
import requests
import io
import base64
import sys



# folder_path = os.path.join(os.path.expanduser("~"), "images")
folder_path = os.path.join(os.path.expanduser("~"), "Smart-Tile-Maker")
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# Initialize the OpenAI API key
key = ""
# Check if the environment variable OPENAI_API_KEY is present
if "OPENAI_API_KEY" in os.environ:
    # If environment variable is present, assign its value to the key variable
    key = "OS_KEY"
    # Set the OpenAI API key using the value from the environment variable
    openai.api_key = os.environ["OPENAI_API_KEY"]
else:
    # If the environment variable is not present, assign a placeholder -
    # value to the key variable
    key = "USER_KEY"


class SDImageGenerator:
    """A class that generates images using the Stable Diffusion (SD) model.

    Attributes:
    - file_name (str): The name of the file to save the generated image.
    - input (str): The input prompt for generating the image.

    Methods:
    - generate_image(): Sends a request to a local SD server with the provided
    input and saves the generated image.
    """

    def __init__(self, file_name, input):
        """Initializes the SDImageGenerator object with the provided file_name
        and input.

        Parameters:
        - file_name (str): The name of the file to save the generated image.
        - input (str): The input prompt for generating the image.
        """
        self.file_name = file_name
        self.input = input

    def generate_image(self):
        """Sends a request to a local server running Stable Diffusion (SD) 
        with the provided input and saves the generated image.
        """
        # Link to SD
        url = "http://127.0.0.1:7860"

        # Settings and variables for SD
        payload = {
            "prompt": self.input,
            "seed": -1,
            "batch_size": 1,
            "n_iter": 1,
            "steps": 20,
            "cfg_scale": 7,
            "width": 512,
            "height": 512,
            "tiling": True
        }

        global folder_path

        # Sets the models to one trained on textures
        option_payload = {
            "sd_model_checkpoint": "TextureDiffusion_10.ckpt [ded387e0f3]"
        }

        stop = False

        error_occurred = False  # Variable to track if an error occurred

        while not stop:
            try:
                response = requests.get(url)
                response.raise_for_status()
                stop = True
            except RequestException as e:
                print(f"There was an issue with your request: {e}")
                error_occurred = False #True
                if error_occurred:  # Display error dialog only once
                    show_error_dialog()
                    error_occurred = True
                stop = True

            else:
                stop = True
                # Send a request to the specified URL with the option payload
                response = requests.post(
                    url=f'{url}/sdapi/v1/options', json=option_payload)
                response = requests.post(
                    url=f'{url}/sdapi/v1/txt2img', json=payload)
                # Convert the response to JSON format
                r = response.json()
                # Process each image in the response
                for i in r['images']:
                    # Open the image and decode it from base64
                    image = Image.open(io.BytesIO(base64.b64decode(i.split(",", 1)[0])))
                    # Prepare the payload for PNG info request
                    png_payload = {
                        "image": "data:image/png;base64," + i
                    }
                    # Send a POST request to obtain PNG info for the image
                    response2 = requests.post(
                        url=f'{url}/sdapi/v1/png-info', json=png_payload)

                    # Create a PNG info object
                    pnginfo = PngImagePlugin.PngInfo()
                    # Add the obtained info as text metadata to the image
                    pnginfo.add_text("parameters", response2.json()["info"])
                    # Save the image with the provided file_name and PNG info
                    print(os.path.join(folder_path, f"{self.file_name}.png"))
                    image.save(rf"{os.path.join(folder_path, f'{self.file_name}.png')}", pnginfo=pnginfo)


class GPTGenerator:
    """A class that generates texture names using the GPT-3 model.

    Attributes:
    - user_input_var (str): The user input variable for GPT generation.
    - user_key_var (str): The user's personal OpenAI key.

    Methods:
    - ask_gpt(text: str) -> str: Generates GPT outputs based on the given 
      text prompt.
    - generate_texture_names() -> list: Generates texture names based on user
      input.
    """
    def __init__(self, user_input_var, user_key_var):
        """Initializes the GPTGenerator object with the 
        provided user_input_var and user_key_var.

        Parameters:
        - user_input_var (str): The user input variable for GPT generation.
        - user_key_var (str): The user's personal OpenAI key.
        """
        self.user_input_var = user_input_var
        self.user_key_var = user_key_var

    def ask_gpt(self, text):
        """Generates GPT outputs based on the given text prompt.

        Parameters:
        - text (str): The prompt for generating GPT outputs.

        Returns:
        - str: The generated GPT output text.
        """

        openai.api_key = self.user_key_var
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=text,
            temperature=0.6,
            max_tokens=150
        )
        return response.choices[0].text

    def generate_texture_names(self):
        """Generates texture names based on user input.

        Returns:
        - list: The generated texture names.
        """
        texture_names = []

        for i in range(5):
            prompt = f"in one word name a material used in {self.user_input_var}"
            if i > 0:
                prompt += f" other than these {texture_names[:i]}"

            texture_names.append(self.ask_gpt(prompt))
            sd_generator = SDImageGenerator(f"Texture{i}", texture_names[i])
            sd_generator.generate_image()

        return texture_names

# Create the UI for user input
if __name__ == "__main__":
    # Create app window
    app = QApplication(sys.argv)
    # Create the main window
    window = QMainWindow()
    # Create a widget to hold the UI elements
    w = QWidget()
    # Set the size of the widget
    w.resize(1000, 500)
    # Set the window title
    window.setWindowTitle("Image Generation Tool")

    # Set the layout
    layout = QFormLayout()

    # box1
    group_box1 = QGroupBox("Required input! This must be filled out", w)
    group_box1.setFixedSize(400, 400)
    # list1
    form_layout1 = QFormLayout(group_box1)

    # Create label and text field for the user to input the theme
    label1 = QLabel('Enter setting or theme (e.g., zombie '
                    'apocalypse/space ship) \nif left blank generic texstures will be used')
    edit1 = QLineEdit()

    # Create label & text field for a user to input an personal OpenAI key
    label2 = QLabel('Enter your OpenAI key. Click <a href="https://cubic-plier-2dd.notion.site/Help-f53d1d8bd1064b90bbf6a86ee3768d25?pvs=4">here</a> for help getting one.')
    edit2 = QLineEdit()
    label2.setOpenExternalLinks(True)



    label3 = QLabel('Click here to chose an outpu direcory. <a href="https://cubic-plier-2dd.notion.site/Help-f53d1d8bd1064b90bbf6a86ee3768d25?pvs=4">Help</a>')
    label3.setOpenExternalLinks(True)
    # Create a button for the user to select the output folder
    btnloc = QPushButton('Select Folder', window)
    btnloc.setGeometry(150, 80, 100, 30)


    def issue_check():
        try:
            edit2.text().encode('latin-1')
        except UnicodeEncodeError:
            show_error_dialog()
            return False
        else:
            # test to see if OpenAI Key is correct and show message if not
            header = {"Authorization": "Bearer " + edit2.text()}  
            try:
                response = requests.get("https://api.openai.com/v1/models", headers=header)
                response.raise_for_status()
            except RequestException:
                show_error_dialog()
                return False
            else:
                return True






    def browse_folder():
        """Opens a folder selection dialog to choose the output folder path."""
        global folder_path
        folder_dialog = QFileDialog()
        select_folder_path = folder_dialog.getExistingDirectory(window, 
                                                                'Select a folder')
        if select_folder_path != '':
            folder_path = select_folder_path
        print('Selected Folder:', select_folder_path)

    btnloc.clicked.connect(browse_folder)

    # Create a button to generate GPT outputs
    btn1 = QPushButton('Generate')


    def generate_textures():
        """Generates texture names and saves the generated images using the
        SD function.
        """
        test = issue_check()
        if test: 


            user_input_var = edit1.text()
            # converts input for key to latin-1(comptable with Open AI)
     #       user_key_var = edit2.text.encode('utf-8')
            user_key_var = edit2.text()
            gpt_generator = GPTGenerator(user_input_var, user_key_var)
            texture_names = gpt_generator.generate_texture_names()
            print(texture_names)

    btn1.clicked.connect(generate_textures)
    btn1.move(200, 200)



    edit1.returnPressed.connect(generate_textures)
    edit2.returnPressed.connect(generate_textures)

    def open_help_url():
        """Opens the help URL in the default web browser."""
        help_url = QUrl("https://cubic-plier-2dd.notion.site/Help-f53d1d8bd1064b90bbf6a86ee3768d25?pvs=4")
        QDesktopServices.openUrl(help_url)


    def show_error_dialog():
        """Shows a warning dialog box indicating a connection error with the
        Stable Diffusion (SD) server.
        """
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText('The app failed to connect to either Stable Diffusion or ChatGPT. \n'
                        'Make sure Stable Diffusion is running on your computer and you enterd '
                        'a valid Open AI key.')
        helpbtn = QPushButton('Get Help')
        helpbtn.clicked.connect(open_help_url)
        

        msg_box.setWindowTitle("Warning")
        msg_box.addButton(helpbtn, QMessageBox.ActionRole)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    # Add widgets to the layout
    form_layout1.addRow(label1)
    form_layout1.addRow(edit1)
    form_layout1.addRow(label2)
    form_layout1.addRow(edit2)
    form_layout1.addRow(label3)
    form_layout1.addRow(btnloc)
    form_layout1.addRow(btn1)
    layout.addRow(group_box1)

    # Set the layout for the main window
    w.setLayout(layout)

    # Set the central widget for the main window
    window.setCentralWidget(w)

    # Show the main window
    window.show()

    # Execute the app
    sys.exit(app.exec_())
