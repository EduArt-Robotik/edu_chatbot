import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'edu_chatbot_wakeword'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'models'), glob(os.path.join('models', '*.onnx*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Hannes Duske',
    maintainer_email='hannes.duske@eduart-robotik.com',
    description='Generic ROS2 wakeword activation.',
    license='BSD-3-Clause',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'edu_chatbot_wakeword_node = edu_chatbot_wakeword.edu_chatbot_wakeword_node:main'
        ],
    },
)
