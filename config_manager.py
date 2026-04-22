import os
import json
import sys

CONFIG_FILENAME = "config.json"

DEFAULT_CONFIG = {
    "api_key": "",
    "last_parent_dir": "",
    "current_project_dir": ""
}


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def config_path():
    return os.path.join(app_dir(), CONFIG_FILENAME)


def load_config():
    path = config_path()

    if not os.path.exists(path):
        return DEFAULT_CONFIG.copy()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            config = DEFAULT_CONFIG.copy()
            config.update(data)
            return config
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config):
    path = config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_api_key():
    return load_config().get("api_key", "").strip()


def set_api_key(api_key):
    config = load_config()
    config["api_key"] = api_key.strip()
    save_config(config)


def get_last_parent_dir():
    return load_config().get("last_parent_dir", "").strip()


def set_last_parent_dir(folder):
    config = load_config()
    config["last_parent_dir"] = folder.strip()
    save_config(config)


def get_current_project_dir():
    return load_config().get("current_project_dir", "").strip()


def set_current_project_dir(folder):
    config = load_config()
    config["current_project_dir"] = folder.strip()
    save_config(config)


def clear_current_project_dir():
    config = load_config()
    config["current_project_dir"] = ""
    save_config(config)