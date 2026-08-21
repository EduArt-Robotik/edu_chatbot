from setuptools import find_packages, setup

package_name = 'edu_chatbot_rag'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Hannes Duske',
    maintainer_email='hannes.duske@eduart-robotik.com',
    description='ROS2 Adapter for the EduArt RAG pipeline.',
    license='BSD-3-Clause',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'edu_chatbot_rag_node = edu_chatbot_rag.edu_chatbot_rag_node:main',
            'edu_chatbot_database_update_node = edu_chatbot_rag.edu_chatbot_database_update_node:main'
        ],
    },
)
