import configparser
import os
import subprocess
import threading

import requests
from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    finished = Signal(str, int)

    def __init__(self, base_url, model, messages, temperature=0.7, penalty=1.0):
        super().__init__()
        self.base_url = base_url
        self.model = model
        self.messages = messages
        self.temperature = temperature
        self.penalty = penalty

    def run(self):
        try:
            print("OK")
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer no-key",
            }

            data = {
                "model": self.model,
                "cache_prompt": True,
                "messages": self.messages,
                "temperature": self.temperature,
                "frequency_penalty": self.penalty
            }

            response = requests.post(self.base_url, headers=headers, json=data)
            response_data = response.json()

            assistant_message = response_data['choices'][0]['message']['content']
            total_tokens_used = response_data['usage']['total_tokens']

            print(total_tokens_used)
            self.finished.emit(assistant_message, total_tokens_used)
        except Exception as e:
            print(f"Error sending message: {e}")


temp_dir = os.path.join(os.getcwd(), 'temp')
os.makedirs(temp_dir, exist_ok=True)
print(temp_dir)

models_dir = os.path.join(os.getcwd(), 'models')
os.makedirs(models_dir, exist_ok=True)
print(models_dir)

backend_dir = os.path.join(os.getcwd(), 'backend')
os.makedirs(backend_dir, exist_ok=True)


def load_settings():
    config = configparser.ConfigParser()

    settings = {
        'threads': 14,
        'capacity': 4096,
        'temperature': 0.7,
        'new_predict': 512,
        'gpu_layers': 0,
        'grp_n': 1,
        'grp_w': 512
    }

    config.read('config.ini')

    if config.has_section('Settings'):
        for key in settings:
            if config.has_option('Settings', key):
                value = config.get('Settings', key)
                if key in ['threads', 'capacity', 'new_predict', 'gpu_layers', 'grp_n', 'grp_w']:
                    settings[key] = int(value)
                elif key == 'temperature':
                    settings[key] = float(value)

    return settings


def boot_func():
    config = configparser.ConfigParser()
    config_file = './config.ini'
    if not os.path.exists(config_file):
        print("Config file not found.")
        filename = "kunoichi-7b.Q6_K.gguf"
    else:
        config.read(config_file)
        filename = config.get('LLM', 'selected_file', fallback="")
        if filename == "":
            filename = "kunoichi-7b.Q6_K.gguf"

    settings = load_settings()

    if str(settings['grp_n']) == "1":
        command = [
            backend_dir + '/server',
            '-m', models_dir + f'/{filename}',
            '--host', '127.0.0.1',
            '--port', '35634',
            '-t', str(settings['threads']),
            '-c', str(settings['capacity']),
            '-ngl', str(settings['gpu_layers']),
            '-b', '512',
            '--grp-attn-n', str(settings['grp_n']),
            '--grp-attn-w', str(settings['grp_w'])
        ]
    else:
        command = [
            backend_dir + '/server',
            '-m', models_dir + f'/{filename}',
            '--host', '127.0.0.1',
            '--port', '35634',
            '-t', str(settings['threads']),
            '-c', str(settings['capacity']),
            '-ngl', str(settings['gpu_layers']),
            '-b', '512'
        ]

    with open(temp_dir + '/llama_output.log', 'w') as output_file:
        process = subprocess.Popen(command, stdout=output_file, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
    process.wait()

    if process.returncode != 0:
        print("Server exited with error code:", process.returncode)


def boot():
    server_thread = threading.Thread(target=boot_func)
    server_thread.daemon = True
    server_thread.start()


def kill():
    result = subprocess.run(['taskkill', '/f', '/im', 'server.exe'],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW)

    if result.returncode == 0:
        pass
    else:
        print("Error: Command failed with return code", result.returncode)
