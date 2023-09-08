import os
import sys

sys.path.insert(0, os.path.abspath('.'))

extensions = [
    'sphinx.ext.autodoc',
]

autodoc_modules = {
    'Device': './emulators/Device.py',
    'Medium': './emulators/Medium.py',
    'MessageStub': './emulators/MessageStub.py',
}

