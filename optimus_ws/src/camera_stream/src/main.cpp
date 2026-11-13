#include "rclcpp/rclcpp.hpp"
#include "camera_stream/CameraPublisher.h"

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<CameraPublisher>());
  rclcpp::shutdown();
  return 0;
}
