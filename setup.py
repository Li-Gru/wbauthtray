from setuptools import setup

APP = ['main.py']
DATA_FILES = [('', ['img'])]
OPTIONS = {
    'iconfile': 'img/icon.png',
    'includes': [
        'desktop_notifier','desktop_notifier.resources',
        'httpx',
        'rumps',
        'pyyaml',
        'pyperclip',
        'rubicon-objc',
        'anyio._backends','anyio._backends._asyncio'],
    'excludes': ['setuptools','setuptools._vendor'],
    'plist': {
      'LSUIElement': True,
      'CFBundleName': 'WBAuthTray',
      'CFBundleDisplayName': 'WBAuthTray',
      'CFBundleVersion': '0.0.1',
      'CFBundleShortVersionString': '0.0.1',
    },
    'emulate_shell_environment': True
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
