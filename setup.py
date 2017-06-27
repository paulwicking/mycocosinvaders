try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

config = {
	'description': 'Another Python Space Invader Clone',
	'author': 'wowsuchnamaste',
	'url': 'http://github.com/wowsuchnamaste/mycocosinvaders',
	'download_url': 'http://github.com/wowsuchnamaste/mycocosinvaders',
	'author_email': 'wowsuchnamaste@users.github.com',
	'version': '0.1'
	'install_requires': ['nose'],
	'packages': ['mycocosinvaders'],
	'scripts': [],
	'name': 'mycocosinvaders'
}

setup(**config, install_requires=['pyglet'])
