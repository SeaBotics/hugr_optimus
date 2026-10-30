import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'hugr_sim'

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
    description='Fossen-based Hydrodynamic Marine Simulation for Hugr Optimus ASV',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'fossen_sim_node = hugr_sim.fossen_sim_node:main',
        ],
    },
)
