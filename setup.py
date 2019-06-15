from setuptools import setup
from re import match, S

with open('discord_party.py', 'r') as f:
    contents = f.read()
    longdesc = match('^"""(.*?)"""', contents, S).group(1)
    version = match(r'[\s\S]*__version__[^\'"]+[\'"]([^\'"]+)[\'"]', contents).group(1)
    del contents

with open('README.rst', 'w') as f2:
    f2.write(longdesc)

setup(
    name="discord-party",
    version=version,
    description="Handle Discord Rich Presence party logic with ease.",
    long_description=longdesc,
    url="https://github.com/Kenny2github/discord-party",
    author="Ken Hilton",
    license="MIT",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Communications :: Chat',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='discord rpc presence party',
    py_modules=["discord_party"],
    install_requires=['pypresence==3.3.2', 'six'],
    python_requires='>=3.7',
)
