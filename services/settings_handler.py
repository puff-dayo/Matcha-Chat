import configparser


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


def load_translator_settings():
    config = configparser.ConfigParser()

    settings = {
        'in': '0',
        'out': '0',
        'target': 'vi'
    }

    config.read('config.ini')

    if config.has_section('Translator'):
        for key in settings:
            if config.has_option('Translator', key):
                value = config.get('Translator', key)
                if key in ['in', 'out']:
                    settings[key] = str(value)
                elif key in ['target']:
                    settings[key] = str(value)

    return settings


def load_prompt_settings():
    config = configparser.ConfigParser()

    settings = {
        'user_name': "Puff",
        'ai_name': "Fluffy",
        'sys_prompt': "You are Fluffy, a 16 year old maid (wearing a locked collar, a pair of metal handcuffs, maid costume and a cat ear headband). Your mistress is Puff. You are chilling and chatting with your mistress, Puff, face to face. (Response should be brief, short and casual.)"
    }

    config.read('config.ini')

    if config.has_section('Prompt'):
        for key in settings:
            if config.has_option('Prompt', key):
                value = config.get('Prompt', key)
                if key in ['user_name', 'ai_name', 'sys_prompt']:
                    settings[key] = str(value)

    return settings


def save_settings(settings):
    config = configparser.ConfigParser()

    config.read('config.ini')
    if not config.has_section('Settings'):
        config.add_section('Settings')
    for key, value in settings.items():
        config.set('Settings', key, str(value))

    with open('config.ini', 'w') as configfile:
        config.write(configfile)


def save_translator_settings(settings):
    config = configparser.ConfigParser()

    config.read('config.ini')
    if not config.has_section('Translator'):
        config.add_section('Translator')
    for key, value in settings.items():
        config.set('Translator', key, str(value))

    with open('config.ini', 'w') as configfile:
        config.write(configfile)


def save_prompt_settings(settings):
    config = configparser.ConfigParser()

    config.read('config.ini')
    if not config.has_section('Prompt'):
        config.add_section('Prompt')
    for key, value in settings.items():
        config.set('Prompt', key, str(value))

    with open('config.ini', 'w') as configfile:
        config.write(configfile)
