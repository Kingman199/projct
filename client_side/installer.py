import subprocess
import sys

# List of packages to be installed
packages = [
    'flask_session',
    'flask_socketio',
    'flask',
    'pycryptodome',
    'cryptography',
    'datetime',
    'typing',
    'mimetypes',
    'uuid',
    'base64',
    're',
    'functools'
]


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def main():
    for package in packages:
        try:
            install(package)
            print(f'Successfully installed {package}')
        except subprocess.CalledProcessError:
            print(f'Failed to install {package}')


if __name__ == "__main__":
    main()