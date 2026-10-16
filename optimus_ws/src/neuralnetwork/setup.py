from setuptools import find_packages, setup

package_name = 'neuralnetwork'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    package_data={
        package_name: ['*.pt'],
    },
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='bjornsodal@gmail.com',
    description='ROS 2 Jazzy YOLO buoy detector node',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'yolo_detector = neuralnetwork.yolo_detector:main',
            'overlay_creator = neuralnetwork.overlay_creator:main',
        ],
    },
)
