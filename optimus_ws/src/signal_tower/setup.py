import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'signal_tower'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Julian',
    maintainer_email='idso.julianf@gmail.com',
    description='Fail-safe visual indication of operating modes for Hugr Optimus (Task 3)',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'signal_tower_node = signal_tower.signal_tower_node:main',
            'mock_mode_publisher = signal_tower.mock_mode_publisher:main',
        ],
    },
)
