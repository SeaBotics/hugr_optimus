import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'robot_remote_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Without these two the launch file and the config are not copied
        # into install/, and $(find-pkg-share ...) resolves to a path that
        # does not exist.
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.xml')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='julianidso',
    maintainer_email='idso.julianf@gmail.com',
    description='Xbox controller joint-space jogging for the DOFBOT arm.',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'remote_control_node ='
            ' robot_remote_control.remote_control_node:main',
        ],
    },
)