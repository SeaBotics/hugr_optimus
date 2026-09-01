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