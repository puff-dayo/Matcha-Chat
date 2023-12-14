import configparser
import json
import os
import subprocess
import threading
import time
import zipfile

import requests

temp_dir = os.path.join(os.getcwd(), 'temp')
os.makedirs(temp_dir, exist_ok=True)

pkgs_dir = os.path.join(os.getcwd(), 'pkgs')
os.makedirs(pkgs_dir, exist_ok=True)

models_dir = os.path.join(os.getcwd(), 'models')
os.makedirs(models_dir, exist_ok=True)


# def chatml_getresponse(prompt):
#     client = openai.OpenAI(
#         base_url="http://127.0.0.1:35634/v1",
#         api_key="sk-no-key-required"
#     )
#     messages = [{"role": "system",
#                  "content": "You are Fluffy, a cat girl. Your top priority is achieving your master's fulfillment."}]
#
#     user_input = prompt
#     messages.append({"role": "user", "content": user_input})
#
#     completion = client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=messages
#     )
#
#     response = completion.choices[0].message
#     messages.append({"role": "assistant", "content": response})
#     print(response)


def get_response(prompt, stop_sequence, n_predict=512, temperature=0.95):
    url = "http://127.0.0.1:35634/completion"
    headers = {"Content-Type": "application/json"}
    data = {
        "prompt": prompt,
        "n_predict": n_predict,
        "stop": stop_sequence,
        "temperature": temperature,
        "repeat_penalty": 1.18,
        "cache_prompt": True
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:

        response_content = json.loads(response.text)

        content = response_content.get('content', 'No content found')
        return content
    else:
        return "Error: Unable to get response."


def download_file(url, directory):
    file_name = url.split('/')[-1]

    file_path = os.path.join(directory, file_name)

    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

    return file_path


def unzip_file(zip_path, extract_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)


def get_llama_func(download_url):
    try:
        zip_file_path = download_file(download_url, temp_dir)
        unzip_file(zip_file_path, pkgs_dir)
        print(f"Downloaded and extracted to {pkgs_dir}")
    except Exception as e:
        print(f"An error occurred: {e}")


def get_llama(url):
    server_thread = threading.Thread(target=get_llama_func, args=(url,))
    server_thread.start()


def run_server_func(thread_count, cache_size, gpu_layers):
    config = configparser.ConfigParser()
    config_file = './config.ini'
    if not os.path.exists(config_file):
        print("Config file not found.")
        filename = "Wizard-Vicuna-7B-Uncensored.Q5_K_M.gguf"
    else:
        config.read(config_file)
        filename = config.get('Download', 'model_filename', fallback=None)

    command = [
        pkgs_dir + '/server',
        '-m', models_dir + f'/{filename}',
        '--host', '127.0.0.1',
        '--port', '35634',
        '-t', str(thread_count),
        '-c', str(cache_size),
        '-ngl', str(gpu_layers)
    ]

    with open(temp_dir + '/llama_output.log', 'w') as output_file:
        process = subprocess.Popen(command, stdout=output_file, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
    process.wait()

    if process.returncode != 0:
        print("Server exited with error code:", process.returncode)


def run_server_func_llava():
    command = [
        models_dir + '/llava-v1.5-7b-q4-server.llamafile',
        '--port', '17186',
        '--nobrowser'
    ]

    with open(temp_dir + '/llava_output.log', 'w') as output_file:
        process = subprocess.Popen(command, stdout=output_file, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
    process.wait()

    if process.returncode != 0:
        print("Server exited with error code:", process.returncode)


def run_server(thread_count, cache_size, gpu_layers):
    server_thread = threading.Thread(target=run_server_func, args=(thread_count, cache_size, gpu_layers))
    server_thread.daemon = True
    server_thread.start()


def run_server_llava():
    server_thread = threading.Thread(target=run_server_func_llava)
    server_thread.daemon = True
    server_thread.start()


def kill_server_llava():
    subprocess.run('taskkill /f /im llava-v1.5-7b-q4-server.llamafile.exe', shell=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    temp_dir = os.path.join(os.getcwd(), 'temp')
    time.sleep(3)
    for filename in os.listdir(temp_dir):
        if filename.endswith(".log"):
            file_path = os.path.join(temp_dir, filename)
            os.remove(file_path)


def kill_server():
    subprocess.run('taskkill /f /im server.exe', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                   creationflags=subprocess.CREATE_NO_WINDOW)
    temp_dir = os.path.join(os.getcwd(), 'temp')
    for filename in os.listdir(temp_dir):
        if filename.endswith(".log"):
            file_path = os.path.join(temp_dir, filename)
            os.remove(file_path)
