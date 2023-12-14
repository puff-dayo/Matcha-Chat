import base64
import io
import json

import requests
from PIL import Image


def image_to_base64(image_path):
    with Image.open(image_path) as img:
        buffered = io.BytesIO()
        img.save(buffered, format=img.format)
        img_base64 = base64.b64encode(buffered.getvalue())
        return img_base64.decode()


def get_caption(image_path):
    url = "http://127.0.0.1:17186/completion"
    _base64data = image_to_base64(image_path)
    data = {"stream": False, "n_predict": 512, "temperature": 0.1, "stop": ["</s>", "Llama:", "User:"],
            "repeat_last_n": 256, "repeat_penalty": 1.18, "top_k": 40, "top_p": 0.5, "tfs_z": 1, "typical_p": 1,
            "presence_penalty": 0, "frequency_penalty": 0, "mirostat": 0, "mirostat_tau": 5, "mirostat_eta": 0.1,
            "grammar": "", "n_probs": 0, "image_data": [{"data": f"{_base64data}", "id": 10}], "cache_prompt": False,
            "slot_id": -1,
            "prompt": "A chat between a curious human and an artificial intelligence assistant. The assistant gives "
                      "helpful and detailed answers to the human's questions.\nUSER:[img-10]Describe everything "
                      "in this image as an alt text for blind people. If there are human characters exist, describe the"
                      "characters and their face expression, outfit, posture, age and features in detail.\nASSISTANT:"}

    json_data = json.dumps(data)

    headers = {'Content-Type': 'application/json'}

    _response = requests.post(url, headers=headers, data=json_data)

    if _response.status_code == 200:
        response_data = json.loads(_response.content)
        content = response_data['content']
        return content
    else:
        return f"Error: {_response.status_code}"


# print(get_caption("./test.jpg"))
