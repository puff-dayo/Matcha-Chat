# Matcha Chat

<img src="https://github.com/puff-dayo/matcha-chat/assets/84665734/5401d53a-2265-4038-a812-e9c2bd28afa4" width="64" />

# MatchaChat 2 Development Branch

**<Warning: Matcha Chat 2 is currently under development!>**

Everything is under development. Expect bugs and errors.

Thank you for your support.

**</Warning: Matcha Chat 2 is currently under development!>**

---

## Introduction

**Matcha Chat** is a **GUI** chat app wrapping [llama.cpp](https://github.com/ggerganov/llama.cpp) for **Windows OS** designed to chat with a **local language model**, built with a [Python](https://www.python.org/) and [Pyside6](https://pypi.org/project/PySide6/).

The app interface allows for **easy** installation of llama.cpp, some models from [TheBloke](https://huggingface.co/TheBloke/) and **visual ability** from [llava](https://huggingface.co/jartine/llava-v1.5-7B-GGUF/) (WIP as for version 2), with message sending, system configuration, [whisper](https://github.com/ggerganov/whisper.cpp/) voice input and management of character cards.

## Features/Roadmaps

- **[✔] Easy-to-use installation**
- **[✔] Character management**
- **[✔] Hardware acceration support**: clBlast for CPU/GPU hybrid inference.
- **[✔] Native GUI**: Not running in a browser or Electron.
- **Vision ability**: WIP.
- **Voice input**：Speak your own language in your voice with auto translation to English, WIP.
- **[✔] Built-in translator**
- **[✔] Wrapped LongLM support**

❤️ All data stores and computes on your local machine, powered by multiple LLM models.


## Installation Guide

--- Hardware requirements ---

Devices with <u>2/4/8GB of installed RAM</u> can run in text-only mode for a 1B/3B/7B model.

You need an additional <u>4GB of spare RAM</u> to chat with images.

Really much VRAM is required to use GPU acceleration. Set gpu_layers to 0 unless your PC is **strong**.

### Step 1: Get the executable

Download the built binary executable file for x64 Windows OS from [Release](https://github.com/puff-dayo/matcha-chat/releases/), and place it in any empty folder.

### Step 2: Click the download buttons

Download the llama.cpp backend, and your favorite models.

### Step 3: Click the red triangle button to launch 
Viola!

## FAQ (Maybe)

**Q:** How to manually add .gguf model?<br>
**A:** Place model files into ./models folder, and go to settings in MatchaChat.

**Q:** Is larger model better?<br>
**A:** No, it depends on your task, and the model itself. The LLM field is advancing so rapidly that it only takes days for the list of "best" models to refresh. However, note that leader boards are not entirely trustworthy, and many test ratings are distorted.

**Q**: There are so many parameters that I don't understand how to set them!<br>
**A**: Hover your mouse over the slider of the slider bar to see the tips.

**Q:** How to contribute?<br>
**A:** Fork and modify the code, raise an issue, or kiss Setsuna goodnight.

## Other Useful Information

### Run from source

Before running Matcha Chat, ensure you have Python 3.10 and all requirements installed.

```powershell
pip install -r requirements.txt
python matcha_gui.py
# or py matcha-gui.py if you are using Powershell
```

### Compile your own binary file....

If you like to~

```powershell
nuitka --standalone --show-progress --onefile --disable-console --plugin-enable=pyside6 --windows-icon-from-ico=.\icon.ico --output-dir=build_output main_window.py
```

### Dev machine infos

**Processor:** Intel Core m3-6Y30 (2C4T)<br>
**Graphics adapter:** Intel HD Graphics 515<br>
**Memory:** Dual-Channel 2x8 GB<br>