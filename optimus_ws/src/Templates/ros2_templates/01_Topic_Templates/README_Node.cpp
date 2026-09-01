//  This document describes syntax and template for a ros2 node
// Created within the src folder
// Remember ros2 cpp -> build, soruce, run

// See this: https://docs.ros.org/en/jazzy/p/rclcpp/
// See This: https://github.com/ros2/rclcpp

// Topics use .msg


// ----------- Code starts here -----------
#include "rclcpp/rclcpp.hpp"         // Including the Ros Clinet Library API for ROS2

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);        // Initialises the ROS2 communication
    
    // ROS2 uses pointers and smart pointers for everything
    auto node = std::make_shared<rclcpp::Node>("node_name");     // Create a share pointer to a node object

    RCLCPP_INFO(node->get_logger(), "Hello World"); 

    rclcpp::spin(node);              // Adds the spin function
    rclcpp::shutdown();              // Shutdown the ros2 node
    return 0;
}

// How to build the code
// Go to CMakeLists.txt -> 

// cmake_minimum_required(VERSION 3.8)
// project(my_cpp_package)

// if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
//   add_compile_options(-Wall -Wextra -Wpedantic)
// endif()

// # find dependencies
// find_package(ament_cmake REQUIRED)
// find_package(rclcpp REQUIRED)

// ---------- Adding executables ----------

// add_executable(<exe name>, src/<node file.cpp>)
// ament_target_dependencies(<exe name> rclcpp <other dependencies ...>)                   // Adding the dependencies

// add_executable(<other name>, src/<node file.cpp>)
// ament_target_dependencies(<other name> rclcpp <other dependencies ...>)                   // Adding the dependencies

// install(TARGES
//  <exe name>
//  <other exe>
//  DESTINATION lib/${PROJECT_NAME}                                                        // Installing exe in lib folder
// )


// ---------- This may be removed for cleaner build as long as it is in package.xml ----------
// if(BUILD_TESTING)
//  find_package(ament_lint_auto REQUIRED)
//  # the following line skips the linter which checks for copyrights
//  # comment the line when a copyright and license is added to all source files
//  set(ament_cmake_copyright_FOUND TRUE)
//  # the following line skips cpplint (only works in a git repo)
//  # comment the line when this package is in a git repo and when
//  # a copyright and license is added to all source files
//  set(ament_cmake_cpplint_FOUND TRUE)
//  ament_lint_auto_find_test_dependencies()
// endif()
// -------------------------------------------------------------------------------------------

// ament_package()

// After this colcon build can be run

// ---------- Template Cpp ROS2 with classes ----------
#include "rclcpp/rclcpp.hpp"                                                 // Including the Ros Clinet Library API for ROS2

class MyNode : public rclcpp::Node
{
public:
    MyNode() : Node("cpp_test"), counter_(0)
    {
        RCLCPP_INFO(this->get_logger(), "Node Initialized");                      // "this" is a pointer to the current object instance of MyNode
        
        timer_ = this->create_wall_timer(
            std::chrono::seconds(1),
            std::bind(&MyNode::timerCallback, this)
        );
    }

private:
    void timerCallback()
    {
        RCLCPP_INFO(this->get_logger(), "Hello  %d", counter_);
        counter_++;
    }
    rclcpp::TimerBase::SharedPtr timer_;
    int counter_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);        // Initialises the ROS2 communication
    
    // ROS2 uses pointers and smart pointers for everything
    auto node = std::make_shared<MyNode>();                           // Create a share pointer to a node object

    rclcpp::spin(node);                                                      // Adds the spin function
    rclcpp::shutdown();                                                      // Shutdown the ros2 node
    return 0;
}


// Only prints text to its own terminal window. It does not broadcast any data across the ROS2 network. Other nodes cannot see or hear it.
// Therefore this next example includes the core ros2 functionality of publish/subscribe

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp" // Required for std_msgs::msg::String

class MyNode : public rclcpp::Node
{
public:
    MyNode() : Node("cpp_test"), counter_(0)
    {
        RCLCPP_INFO(this->get_logger(), "Hello ROS2");

        // ---------- Publisher ----------
        publisher_ = this->create_publisher<std_msgs::msg::String>("example_topic", 10);

        // ---------- Subscriber ----------
        subscription_ = this->create_subscription<std_msgs::msg::String>(
            "example_topic",
            10,
            std::bind(&MyNode::listenerCallback, this, std::placeholders::_1)
        );

        // ---------- Timer ----------
        timer_ = this->create_wall_timer(
            std::chrono::seconds(1),
            std::bind(&MyNode::timerCallback, this)
        );
    }

private:
    void timerCallback()
    {
        auto msg = std_msgs::msg::String();
        msg.data = "Hello ROS2 Network: " + std::to_string(counter_);
        
        publisher_->publish(msg);

        RCLCPP_INFO(this->get_logger(), "Hello");
        counter_++;
    }

    void listenerCallback(const std_msgs::msg::String::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Subscribed Listener Heard: '%s'", msg->data.c_str());
    }

    // Member variables
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
    rclcpp::TimerBase::SharedPtr timer_;
    int counter_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    
    auto node = std::make_shared<MyNode>();

    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}

// using namsepace is a good tool fo rccp saving space