cmake_minimum_required(VERSION 3.10)
project(edu_chatbot_msgs)

if(POLICY CMP0148)
  cmake_policy(SET CMP0148 OLD)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "action/Query.action"
)

ament_package()
