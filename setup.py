import os
import sys
import subprocess
import logging


# Настройка логгирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_python_version():
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True,
                                text=True)
        version_str = result.stdout.strip().split()[1]
        major, minor, patch = map(int, version_str.split('.')[:3])
        if (major == 3 and minor >= 8 and patch >= 2) or (major > 3):
            logger.info(f"Python version {version_str} is acceptable.")
            return True
        else:
            logger.error(
                f"Python version {version_str} is too low. Need at least 3.8.20.")
            return False
    except Exception as e:
        logger.error(f"Error checking Python version: {e}")
        return False


def find_virtual_env():
    for name in [".venv", "venv"]:
        if os.path.isdir(name):
            logger.info(f"Virtual environment '{name}' already exists.")
            return name
    logger.info("No virtual environment found.")
    return None


def create_virtual_env(env_name=".venv"):
    try:
        logger.info(f"Creating virtual environment '{env_name}'...")
        subprocess.run([sys.executable, "-m", "venv", env_name], check=True)
        logger.info(f"Virtual environment '{env_name}' created.")
        return env_name
    except Exception as e:
        logger.error(f"Failed to create virtual environment: {e}")
        return None


def activate_and_install(env_name):
    pip_path = os.path.join(env_name, "Scripts", "pip.exe")
    python_path = os.path.join(env_name, "Scripts", "python.exe")

    try:
        # Обновляем pip
        logger.info("Upgrading pip...")
        subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip"],
                       check=True)

        # Устанавливаем зависимости
        req_file = "requirements.txt"
        if os.path.isfile(req_file):
            logger.info(f"Installing dependencies from {req_file}...")
            subprocess.run([pip_path, "install", "-r", req_file], check=True)
        else:
            logger.warning(f"{req_file} not found. Skipping dependency installation.")

        return True
    except Exception as e:
        logger.error(f"Error during setup: {e}")
        return False


def run_powershell_script(script_name="create_shortcut.ps1"):
    try:
        logger.info(f"Running PowerShell script '{script_name}'...")
        subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", script_name],
            check=True)
        logger.info("PowerShell script completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error running PowerShell script: {e}")
        return False


def main():
    print("=== Setup Script Starting ===")
    logger.info("Starting setup process...")

    if not check_python_version():
        input("\nPress Enter to exit...")
        return

    env_name = find_virtual_env()
    if not env_name:
        env_name = create_virtual_env()
        if not env_name:
            input("\nPress Enter to exit...")
            return

    if not activate_and_install(env_name):
        input("\nPress Enter to exit...")
        return

    if not run_powershell_script():
        input("\nPress Enter to exit...")
        return

    logger.info("Setup completed successfully.")
    print("\n✅ Setup finished successfully.")
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
