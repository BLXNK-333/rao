import os
import sys
import subprocess
import logging

# Настройка логгирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TARGET_BRANCH = "master"  # Название ветки, которую хотим синхронизировать


def check_git_installed():
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        logger.info("Git is installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Git is not installed or not in PATH.")
        return False


def run_command(command, cwd=None, shell=False):
    try:
        logger.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, cwd=cwd, shell=shell, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        return False


def find_virtual_env():
    for name in [".venv", "venv"]:
        if os.path.isdir(name):
            logger.info(f"Virtual environment '{name}' found.")
            return name
    logger.warning("No virtual environment found (.venv/venv).")
    return None


def sync_branch(script_dir):
    # Проверка наличия ветки
    if not run_command(["git", "rev-parse", "--verify", TARGET_BRANCH], cwd=script_dir):
        logger.warning(f"Local branch '{TARGET_BRANCH}' not found. Creating from origin.")
        if not run_command(["git", "checkout", "-b", TARGET_BRANCH, "--track",
                            f"origin/{TARGET_BRANCH}"], cwd=script_dir):
            print(f"\n❌ Failed to create and track '{TARGET_BRANCH}' from remote.")
            return False
    else:
        # Переход на ветку
        if not run_command(["git", "checkout", TARGET_BRANCH], cwd=script_dir):
            print(f"\n❌ Failed to checkout branch '{TARGET_BRANCH}'.")
            return False

    # Синхронизация с удалённой веткой
    if not run_command(["git", "fetch", "origin"], cwd=script_dir):
        print(f"\n❌ Failed to fetch from origin.")
        return False

    if not run_command(["git", "reset", "--hard", f"origin/{TARGET_BRANCH}"],
                       cwd=script_dir):
        print(f"\n❌ Failed to reset local branch to 'origin/{TARGET_BRANCH}'.")
        return False

    logger.info(f"Branch '{TARGET_BRANCH}' synchronized successfully.")
    return True


def main():
    print("=== Update Script Starting ===\n")

    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    logger.info(f"Changing working directory to: {script_dir}")
    os.chdir(script_dir)

    if not check_git_installed():
        print("\n❌ Error: Git is not installed or not in PATH.")
        input("\nPress Enter to exit...")
        return

    if not sync_branch(script_dir):
        input("\nPress Enter to exit...")
        return

    venv_name = find_virtual_env()
    if not venv_name:
        print(
            "\n❌ No virtual environment found (.venv or venv). Please create one first.")
        input("\nPress Enter to exit...")
        return

    activate_script = os.path.join(venv_name, "Scripts", "activate.bat")
    pip_path = os.path.join(venv_name, "Scripts", "pip.exe")

    if not os.path.isfile(activate_script):
        logger.error(f"Activation script not found in {venv_name}.")
        print(f"\n❌ Activation script not found in {venv_name}.")
    else:
        logger.info(f"Activating virtual environment from {activate_script}...")

    if not os.path.isfile(pip_path):
        logger.error(f"pip not found in {venv_name}.")
        print(f"\n❌ pip not found in {venv_name}.")
    else:
        if os.path.isfile("requirements.txt"):
            logger.info("Installing requirements...")
            if not run_command([pip_path, "install", "-r", "requirements.txt"]):
                print("\n❌ Failed to install requirements.")
        else:
            logger.warning(
                "requirements.txt not found. Skipping dependency installation.")

    print("\n✅ Update completed.")
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
