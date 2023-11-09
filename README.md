# Matcha Chat

## Introduction

**Matcha Chat** is a **GUI** chat app for **Windows OS** designed to chat with a **local language model AI**, built with a [Python](https://www.python.org/) backend and a [Pyside](https://pypi.org/project/PySide6/) front end.

The app interface allows for **easy** one-click installation of [llama.cpp](https://github.com/ggerganov/llama.cpp) and [Wizard Vicuna](https://huggingface.co/TheBloke/Wizard-Vicuna-7B-Uncensored-GGUF), message sending, system configuration, and management of character cards.

## Features

- **Easy-to-use chat interface**: A simple and intuitive chat interface.
- **One-click(s) installation**: Download essential files and start a chat with just a push of  button. Configure threading, content size, and GPU settings easily.
- **Character management**: Load and save character cards(json) for personalized chat experiences. 
- **Hardware acceration support**: Choose between openBLAS and cuBLAS.
- **Highly efficient**: The GUI component of the software is consuming only ~32MB of RAM, representing a significant resource saving compared to running a web UI in Chrome, allowing even devices with 8GB of RAM to run models quantized to 5-bit.

## Step 1: Get the executable

Download the built binary executable file for x64 Windows OS from [Release](https://somewhere).

## Step 2: The first click installation

### CPU Acceleration

Click on the upper button "*1. Download llama.cpp*" to install Llama.cpp with openBLAS support.

At least 4GB of free memory for the recommended configuration.

### GPU Acceleration

Directly click on the button "*1. Enable GPU acceleration*" located below the buttons, instead of the upper one,to install Llama with cuBLAS support.

It is recommended to have at least 4GB of free BRAM and 4GB of VRAM available.

Before lauching the llama.cp service, make sure to set the number of layers to be loaded into the GPU (default is 10).

Note: Generally, a modern graphics card is required to achieve better performance than CPU acceleration.

## Step 3: The second click installation

After completing the installation with step 2, proceed with the following steps:



1. Use button "*2. Download a model*" to download the model.
2. Afterward, use "*3. Launch Llama server" to launch.



Once you have configured all three stpes, you only need to press "*3. Launch Llama server*" to start the program for future chats.





## Screenshots

- The main window is divided into two sections: the left side for chat and the right side for quick installation, system and model configurations.
- Use the 'Send' button or Ctrl+Enter to send messages.
- The 'Clear' button clears the current message input field.



## Other Infomation

### Run from source

Before running Matcha Chat, ensure you have Python installed. Clone the repository to your local machine:

```bash
git clone [repository-url]
```

Navigate to the cloned directory and install the required packages, then lauch the GUI:

```bash
pip install -r requirements.txt
python gui.py
# or py gui.py if you are using powershell
```

### Compile your own binary file....

If you like to~

:P

```bash
nuitka --onefile --disable-console --plugin-enable=pyside6 --windows-icon-from-ico=./icon1.ico gui.py
```

