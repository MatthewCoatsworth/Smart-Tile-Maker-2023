"""This Python file implements a graphical user interface (GUI) tool for generating texture names and images. The tool utilizes the Stable Diffusion (SD) model and GPT-3 model to quickly produce texstures.

The GUI allows users to enter a setting or theme as a prompt, and the tool generates texture names based on the input using the GPT-3 model. It then utilizes the SD model to generate corresponding texture images.

The generated images are saved in a designated output folder, and users can also customize the output directory. The tool requires an OpenAI API key for authentication.

Note: Before generating textures, ensure the necessary requirements are met, such as valid API connection, folder availability, and proper input text encoding.

Author: Matthew C
Date: 15/16/2023
"""

# Import necessary packages
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QFormLayout,
                             QLineEdit, QPushButton, QGroupBox, QFileDialog,
                             QMainWindow, QMessageBox, QVBoxLayout)
from PyQt5.QtCore import QUrl, QDir
from requests.exceptions import RequestException
from PyQt5.QtGui import QDesktopServices
from PIL import Image, PngImagePlugin
import openai
import os
import requests
import io
import base64
import sys

# URL for Stable Diffusion (SD) model API
SD_URL = "http://127.0.0.1:7860"

# Create a folder path for storing generated images
folder_path = os.path.join(os.path.expanduser("~"), "Smart-Tile-Maker")
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# Set the API key for OpenAI
key = ""
# Check if the OpenAI API key is provided as an environment variable
if "OPENAI_API_KEY" in os.environ:
    # Set key type as "OS_KEY" if environment variable is present
    key = "OS_KEY"
    # Set OpenAI API key from environment variable
    openai.api_key = os.environ["OPENAI_API_KEY"]
else:
    # Set key type as "USER_KEY" if environment variable is not present
    key = "USER_KEY"


class SDImageGenerator:
    """Class that generates images using the Stable Diffusion model.

    Attributes:
    - file_name (str): The name of the output file.
    - input (str): The input prompt for generating the image.

    Methods:
    - generate_image(): Generates an image using the Stable Diffusion model.
    """

    def __init__(self, file_name, input):
        """Initializes the SDImageGenerator object.

        Args:
        - file_name (str): The name of the output file.
        - input (str): The input prompt for generating the image.
        """
        # Set the file name attribute
        self.file_name = file_name
        # Set the input attribute
        self.input = input

    def generate_image(self):
        """Generates an image using the Stable Diffusion model."""
        # Set the payload for the Stable Diffusion API request
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

        # Use the global folder_path variable
        global folder_path
        # Use the global SD_URL variable
        global SD_URL

        # Sets the models to one trained on textures
        option_payload = {
            "sd_model_checkpoint": "TextureDiffusion_10.ckpt [ded387e0f3]"
        }

        # Send a POST request to set the options for Stable Diffusion
        response = requests.post(
            url=f'{SD_URL}/sdapi/v1/options', json=option_payload)
        # Send a POST request to generate the image using Stable Diffusion
        response = requests.post(
            url=f'{SD_URL}/sdapi/v1/txt2img', json=payload)
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
                url=f'{SD_URL}/sdapi/v1/png-info', json=png_payload)

            # Create a PNG info object
            pnginfo = PngImagePlugin.PngInfo()
            # Add the obtained info as text metadata to the image
            pnginfo.add_text("parameters", response2.json()["info"])
            # Save the image with the provided file_name and PNG info
            print(os.path.join(folder_path, f"{self.file_name}.png"))
            image.save(rf"{os.path.join(folder_path, f'{self.file_name}.png')}", pnginfo=pnginfo)


class GPTGenerator:
    """Class that generates texture names using the GPT-3 model.

    Attributes:
    - user_input_var (str): The user input variable.
    - user_key_var (str): The user key variable.

    Methods:
    - ask_gpt(text): Sends a text prompt to the GPT-3 model and returns the generated response.
    - generate_texture_names(): Generates texture names using the GPT-3 model.
    """

    def __init__(self, user_input_var, user_key_var):
        """Initializes the GPTGenerator object.

        Args:
        - user_input_var (str): The user input variable.
        - user_key_var (str): The user key variable.
        """
        self.user_input_var = user_input_var
        self.user_key_var = user_key_var

    def ask_gpt(self, text):
        """Sends a text prompt to the GPT-3 model and returns the generated response.

        Args:
        - text (str): The prompt text.

        Returns:
        - str: The generated response from the GPT-3 model.
        """
        # Send a text prompt to the GPT-3 model
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=text,
            temperature=0.6,
            max_tokens=150
        )
        # Return the generated response from the GPT-3 model
        return response.choices[0].text

    def generate_texture_names(self):
        """Generates texture names using the GPT-3 model.

        Returns:
        - list: A list of generated texture names.
        """
        # Initialize an empty list to store the generated texture names
        texture_names = []
        # loop 5 times to generate 5 texture names using the GPT-3 model
        for i in range(5):
            # The prompt text that is sent to GPT
            prompt = f"only reply with a one word answer. Name a single material used in {self.user_input_var}"
            # Add previously generated texture names each prompt sent to GPT to stop it from makeing duplicate texstures
            if i > 0:
                prompt += f" other than these {texture_names[:i]}"
            # Use the ask_gpt method to generate a texture name based on the prompt
            texture_names.append(self.ask_gpt(prompt))
            # Generate an image using the SDImageGenerator class
            sd_generator = SDImageGenerator(f"Texture{i}", "PBR, " + texture_names[i])
            sd_generator.generate_image()

        # Return the list of generated texture names
        return texture_names

# Create the UI for user input
if __name__ == "__main__":
    """Entry point of the program that launches the graphical user interface (GUI) application
    for generating texture names and images. It creates the main window, sets up the user interface
    components, and handles the generation of textures based on user input.
    """
    def generate_textures():
        """Generates textures using the GPTGenerator class and saves the generated images."""
        global key
        print(key)
        # Set the OpenAI API key if it is the default user key
        if key == "USER_KEY":
            openai.api_key = key_edit.text()
            user_key_var = key_edit.text()
        else:
            user_key_var = os.environ["OPENAI_API_KEY"]
        print(openai.api_key)
        # Perform the necessary checks before generating textures
        test = issue_check()
        if test:
            user_input_var = promt_edit.text()
            user_key_var = key_edit.text()
            gpt_generator = GPTGenerator(user_input_var, user_key_var)
            texture_names = gpt_generator.generate_texture_names()
            print(texture_names)

    def issue_check():
        """Performs various checks to ensure the necessary requirements are met for image generation.

        Returns:
        - boolean: True if all checks pass, False otherwise.
        """
        # Declare global variables
        global SD_URL
        global folder_path

        # Check if the folder path exists
        if not QDir(folder_path).exists():
            # Show an error dialog for the folder
            show_error_dialog("The folder you selected dose not exsist. Try selecting a diffrent folder")
            return False
        # Check if the SD_URL is accessible
        try:
            response = requests.get(SD_URL)
            response.raise_for_status()
        except RequestException:
            show_error_dialog("Faild to connect to SD. Make sure you have it running on your computor")
            return False

        # Check if the input text can be encoded in Latin-1
        try:
            key_edit.text().encode('latin-1')
        except UnicodeEncodeError:
            show_error_dialog("Your Open AI key contaned ivalid Characters. Make sure you enter a valid key click 'Get help' to learn how to get one")
            return False

       # Check if the OpenAI key can be encoded in Latin-1
        try:
            okey = openai.api_key
            okey.encode('latin-1')
        except UnicodeEncodeError:
            show_error_dialog("Your Open AI key contaned ivalid Characters. Make sure you enter a valid key click 'Get help' to learn how to get one")
            return False

        # Check the API connection and authentication
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt="test",
                temperature=0.6,
                max_tokens=150)
        except openai.error.APIError:
            show_error_dialog("There was an error connecting to Open AI. Make sure you enter a valid key click 'Get help' to learn how to get one \n(APIError)")
            return False
        except openai.error.APIConnectionError:
            show_error_dialog("There was an error connecting to Open AI. Make sure you enter a valid key click 'Get help' to learn how to get one \n(APIConnectionError)")
            return False
        except openai.error.RateLimitError:
            show_error_dialog("There was an error connecting to Open AI. Make sure you enter a valid key click 'Get help' to learn how to get one \nYou are out of creditds you can get more from OpenAI\n(RateLimitError)")
            return False
        except openai.error.AuthenticationError:
            show_error_dialog("There was an error connecting to Open AI. Make sure you enter a valid key click 'Get help' to learn how to get one \n(AuthenticationError)")
            return False
        return True

    def browse_folder():
        """Opens a file dialog to browse and select an output folder for saving generated images."""
        global folder_path
        # Open a file dialog to select a folder
        folder_dialog = QFileDialog()
        select_folder_path = folder_dialog.getExistingDirectory(window,
                                                                'Select a folder')
        # Update the folder path if a folder is selected
        if select_folder_path != '':
            folder_path = select_folder_path
        print('Selected Folder:', select_folder_path)

    def open_help_url():
        """Opens the URL for the help documentation."""

        help_url = QUrl("https://cubic-plier-2dd.notion.site/Help-f53d1d8bd1064b90bbf6a86ee3768d25?pvs=4")
        QDesktopServices.openUrl(help_url)

    def show_error_dialog(message):
        """Displays an error dialog with the given message.

        Args:
        - message (str): The error message to display.
        """
        # Create an error message box
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        # Set the error message and create a help button
        msg_box.setText(message)

        help_btn = QPushButton('Get help')
        help_btn.clicked.connect(open_help_url)

        # Set the title, add the help button, and set the standard buttons
        msg_box.setWindowTitle("Warning")
        msg_box.addButton(help_btn, QMessageBox.ActionRole)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    # Initialize the application
    app = QApplication(sys.argv)

    # Create the main window
    window = QMainWindow()

    # Create a widget
    w = QWidget()

    window.setCentralWidget(w)

    # Set the window title
    window.setWindowTitle("Image Generation Tool")

    # Create a layout for the widget
    layout = QFormLayout()

    # Create a group box for the required input
    group_box1 = QGroupBox("Required input! This must be filled out", w)

    # Create a form layout for the group box
    form_layout1 = QFormLayout(group_box1)

    # Create a label for the first text field
    prompt_lable = QLabel('Enter setting or theme (e.g., zombie '
                            'apocalypse/spaceship) \nIf left blank generic textures will be genarated.')

    # Create a text edit field for the prompt
    promt_edit = QLineEdit()

    # Set a maximum length for the prompt text
    promt_edit.setMaxLength(150)

    # Create a label for the OpenAI key
    key_lable = QLabel('Enter your OpenAI key. Click <a href="https://cubic-plier-2dd.notion.site/Help-f53d1d8bd1064b90bbf6a86ee3768d25?pvs=4">here</a> for help getting one.')
    key_edit = QLineEdit()

    # Enable opening external links in the key label
    key_lable.setOpenExternalLinks(True)

    # Create a label for info on browsing the output directory
    browse_lable = QLabel('Click here to choose an output directory'
                            '\nIf no selection is made, a Smart Tile Maker folder will be created in the user directory.')
    browse_lable.setOpenExternalLinks(True)
    # Create a button for browsing the directory
    browse_btn = QPushButton('Select folder', window)

    # Connect the browse_folder function when the browse button is clicked
    browse_btn.clicked.connect(browse_folder)

    # Create a button for generating textures
    genarate_btn = QPushButton('Generate textures')

    # Connect the generate_textures function when the generate button is clicked
    genarate_btn.clicked.connect(generate_textures)

    # Connect the generate_textures function to the returnPressed signals of the edit fields
    promt_edit.returnPressed.connect(generate_textures)
    key_edit.returnPressed.connect(generate_textures)

    help_btn = QPushButton('Get help')
    help_btn.clicked.connect(open_help_url)

    # Add the labels, edit fields, button, and group box to the form layout
    form_layout1.addRow(prompt_lable)
    form_layout1.addRow(promt_edit)
    form_layout1.addRow(key_lable)
    form_layout1.addRow(key_edit)
    form_layout1.addRow(browse_lable)
    form_layout1.addRow(browse_btn)
    form_layout1.addRow(help_btn)
    form_layout1.addRow(genarate_btn)

    # Add the group box to the main layout
    layout.addRow(group_box1)

    # Set the layout for the widget
    w.setLayout(layout)

    # Set the widget as the central widget for the main window
    window.setCentralWidget(w)

    # Set a minimum size for the window
    window.setMinimumSize(400, 400)

    # Show the main window
    window.show()

    # Execute the application
    sys.exit(app.exec_())
