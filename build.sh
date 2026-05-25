poetry run pyinstaller kit/main.py --onefile --name kit --collect-submodules rich._unicode_data --collect-data rich._unicode_data
sudo cp -rf ./dist/kit /usr/local/bin/
