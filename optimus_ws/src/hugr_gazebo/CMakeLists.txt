cmake_minimum_required(VERSION 3.8)
project(hugr_gazebo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY launch worlds models config
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS scripts/thruster_bridge.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
