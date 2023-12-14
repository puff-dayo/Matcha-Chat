# Matcha Chat

<img src="https://github.com/puff-dayo/matcha-chat/assets/84665734/5401d53a-2265-4038-a812-e9c2bd28afa4" width="64" />



## Introduction

**Matcha Chat** is a **GUI** chat app for **Windows OS** designed to chat with a **local language model AI**, built with a [Python](https://www.python.org/) backend and a [Pyside](https://pypi.org/project/PySide6/) front end.

The app interface allows for **easy** clicks installation of [llama.cpp](https://github.com/ggerganov/llama.cpp) , [Wizard Vicuna](https://huggingface.co/TheBloke/Wizard-Vicuna-7B-Uncensored-GGUF) and **visual ability** from [llava](https://huggingface.co/jartine/llava-v1.5-7B-GGUF/), with message sending, system configuration, and management of character cards.

**How to update: simply replace the .exe file.**



## Features

- **Easy-to-use installation**: Download essential files and start a chat with just some pushes of button. Configure settings easily.
- **Character management**: Load and save character cards(json). 
- **Hardware acceration support**: Choose between openBLAS and cuBLAS.
- **Highly efficient**: The GUI component of the software is consuming only ~64MB of RAM, which is a significant resource saving compared to a web UI running in Chrome.
- **Vision ability**: ✨Send images into your chat with AI✨.

<img src="https://github.com/puff-dayo/Matcha-Chat/assets/84665734/ab0c23cb-0303-496d-995b-497308c83a70"/>




## Installation Guide

--- Hardware requirements ---

Devices with <u>8GB of installed RAM</u> can run in text-only mode.

Devices with <u>8GB of spare RAM</u> can chat with images.

More than 8GB of VRAM is required to use GPU acceleration

### Step 1: Get the executable

Download the built binary executable file for x64 Windows OS from [Release](https://github.com/puff-dayo/matcha-chat/releases/), and place it in an empty folder.

### Step 2: The first click

> [!CAUTION]
> Using GPU or setting more GPU layers ≠ Faster speed!
> Choose **CPU Acceleration** unless you have a STRONG enough GPU.

#### CPU Acceleration

Click on the upper button "*1. Download llama.cpp*" to install Llama.cpp with openBLAS support.

#### GPU Acceleration

Directly click on the button "*Enable GPU acceleration*" located below the buttons, instead of the upper one,to install Llama with cuBLAS support.

Before lauching the llama.cpp service, make sure to set the number of layers to be loaded into the GPU (default is 0).

### Step 3: The second click

After completing the installation with step 2, proceed with the following steps:



1. Use button "*2. Download a model*" to download the model.
2. Afterward, use "*3. Launch Llama server*" to launch.



Once you have configured all three stpes, you only need to press "*3. Launch Llama server*" to start the llama every time you run it.



## Other Useful Infomation

### Run from source

Before running Matcha Chat, ensure you have Python installed. Clone the repository to your local machine:

```powershell
git clone https://github.com/puff-dayo/Matcha-Chat.git
```

Navigate to the cloned directory and install the required packages, then lauch the GUI:

```powershell
pip install -r requirements.txt
python matcha_gui.py
# or py matcha-gui.py if you are using Powershell
```

### Compile your own binary file....

If you like to~

```powershell
nuitka --onefile --disable-console --plugin-enable=pyside6 --windows-icon-from-ico=PATH-TO-ICON matcha_gui.py
```
