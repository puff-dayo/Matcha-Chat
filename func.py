import json

import requests
import os
import zipfile
import subprocess
import threading

temp_dir = os.path.join(os.getcwd(), 'temp')
os.makedirs(temp_dir, exist_ok=True)

pkgs_dir = os.path.join(os.getcwd(), 'pkgs')
os.makedirs(pkgs_dir, exist_ok=True)

models_dir = os.path.join(os.getcwd(), 'models')
os.makedirs(models_dir, exist_ok=True)


def get_response(prompt, stop_sequence, n_predict=512, temperature=0.95):
    url = "http://127.0.0.1:35634/completion"
    headers = {"Content-Type": "application/json"}
    data = {
        "prompt": prompt,
        "n_predict": n_predict,
        "stop": stop_sequence,
        "temperature": temperature
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
    command = [
        pkgs_dir + '/server',
        '-m', models_dir + '/Wizard-Vicuna-7B-Uncensored.Q5_K_M.gguf',
        '--host', '127.0.0.1',
        '--port', '35634',
        '-t', str(thread_count),
        '-c', str(cache_size),
        '-ngl', str(gpu_layers)
    ]

    process = subprocess.Popen(command)
    process.wait()

    if process.returncode != 0:
        print("Server exited with error code:", process.returncode)



def run_server(thread_count, cache_size, gpu_layers):
    server_thread = threading.Thread(target=run_server_func, args=(thread_count, cache_size, gpu_layers))
    server_thread.daemon = True
    server_thread.start()
