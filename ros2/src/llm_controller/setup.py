import os
from glob import glob
from setuptools import setup

package_name = 'llm_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    install_requires=[
        'setuptools',
        'requests'
    ],
    zip_safe=True,
    maintainer='root',
    maintainer_email='root@localhost',
    description='LLM controller node',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'llm_node = llm_controller.llm_node:main',
            'robot_action_server = llm_controller.robot_action_server:main',
        ],
    },
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
)