#include <algorithm>
#include <chrono>
#include <memory>
#include <string>
#include <cmath>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include <std_msgs/msg/header.hpp>
#include <std_msgs/msg/int32_multi_array.hpp>
#include <geometry_msgs/msg/vector3.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <sensor_msgs/msg/joy.hpp>

using namespace std::placeholders;
using namespace std::chrono_literals;

class ThrustAllocationNode : public rclcpp::Node
{
private:
    // Subscriptions and Publishers
    rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr joy_sub_;
    rclcpp::Publisher<geometry_msgs::msg::Vector3>::SharedPtr thrust_pub_;
    rclcpp::Publisher<std_msgs::msg::Int32MultiArray>::SharedPtr motor_pwm_pub_;
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_pub_;
    rclcpp::TimerBase::SharedPtr timer_;

    // Parameters
    double deadzone_;
    double max_speed_mps_;
    double max_yaw_rate_rads_;

    // Joystick commands
    double Fx_;
    double Fy_;
    double tau_;

    // PWM Constants for ESC (matches ESP32 micro-ROS firmware)
    const int PWM_NEUTRAL = 1500;
    const int PWM_RANGE = 400; // 1100 us to 1900 us

public:
    ThrustAllocationNode() : Node("thrust_allocation_node")
    {
        // Parameters
        this->declare_parameter("deadzone", 0.05);
        this->declare_parameter("max_speed_mps", 1.5);
        this->declare_parameter("max_yaw_rate_rads", 1.0);

        deadzone_ = this->get_parameter("deadzone").as_double();
        max_speed_mps_ = this->get_parameter("max_speed_mps").as_double();
        max_yaw_rate_rads_ = this->get_parameter("max_yaw_rate_rads").as_double();

        Fx_ = 0.0;
        Fy_ = 0.0;
        tau_ = 0.0;

        // Subscribe to /joy
        joy_sub_ = create_subscription<sensor_msgs::msg::Joy>(
            "/joy", 10,
            std::bind(&ThrustAllocationNode::joystickCommands, this, _1));

        // Publish to /thrust_allocation (Vector3: Fx, Fy, tau)
        thrust_pub_ = create_publisher<geometry_msgs::msg::Vector3>(
            "thrust_allocation", 10);

        // Publish to /motor_pwms for ESP32 Nano micro-ROS firmware & simulator
        motor_pwm_pub_ = create_publisher<std_msgs::msg::Int32MultiArray>(
            "/motor_pwms", 10);

        // Publish to /cmd_vel for standard ROS 2 navigation
        cmd_vel_pub_ = create_publisher<geometry_msgs::msg::Twist>(
            "/cmd_vel", 10);

        auto timer_callback = [this]() -> void {
            // 1. Publish Vector3
            auto vec_msg = geometry_msgs::msg::Vector3();
            vec_msg.x = Fx_;
            vec_msg.y = Fy_;
            vec_msg.z = tau_;
            this->thrust_pub_->publish(vec_msg);

            // 2. Publish Twist (/cmd_vel)
            auto twist_msg = geometry_msgs::msg::Twist();
            twist_msg.linear.x = Fx_ * max_speed_mps_;
            twist_msg.linear.y = Fy_ * max_speed_mps_;
            twist_msg.angular.z = tau_ * max_yaw_rate_rads_;
            this->cmd_vel_pub_->publish(twist_msg);

            // 3. Compute 4 Motor PWMs for ESP32 & Simulator
            // Motor 1 (Port Main Longitudinal): Fx - 0.5 * tau
            // Motor 2 (Starboard Main Longitudinal): Fx + 0.5 * tau
            // Motor 3 (Bow Transverse Lateral): Fy + 0.5 * tau
            // Motor 4 (Stern Transverse Lateral): Fy - 0.5 * tau
            double left_cmd = std::clamp(Fx_ - 0.5 * tau_, -1.0, 1.0);
            double right_cmd = std::clamp(Fx_ + 0.5 * tau_, -1.0, 1.0);
            double bow_cmd = std::clamp(Fy_ + 0.5 * tau_, -1.0, 1.0);
            double stern_cmd = std::clamp(Fy_ - 0.5 * tau_, -1.0, 1.0);

            int pwm_port = PWM_NEUTRAL + static_cast<int>(left_cmd * PWM_RANGE);
            int pwm_stbd = PWM_NEUTRAL + static_cast<int>(right_cmd * PWM_RANGE);
            int pwm_bow = PWM_NEUTRAL + static_cast<int>(bow_cmd * PWM_RANGE);
            int pwm_stern = PWM_NEUTRAL + static_cast<int>(stern_cmd * PWM_RANGE);

            auto pwm_msg = std_msgs::msg::Int32MultiArray();
            pwm_msg.data = {pwm_port, pwm_stbd, pwm_bow, pwm_stern};
            this->motor_pwm_pub_->publish(pwm_msg);

            // Live logging to console (throttled to 1 Hz when motors are active)
            bool is_active = (std::abs(Fx_) > 0.02 || std::abs(Fy_) > 0.02 || std::abs(tau_) > 0.02);
            static auto last_log_time = std::chrono::steady_clock::now();
            auto now = std::chrono::steady_clock::now();
            if (is_active && std::chrono::duration_cast<std::chrono::milliseconds>(now - last_log_time).count() >= 1000) {
                last_log_time = now;
                RCLCPP_INFO(this->get_logger(),
                    "[ALLOCATION -> MOTORS] PWMs: [M1(Port)=%d, M2(Stbd)=%d, M3(Bow)=%d, M4(Stern)=%d] | In: Surge=%.2f, Sway=%.2f, Yaw=%.2f",
                    pwm_port, pwm_stbd, pwm_bow, pwm_stern, Fx_, Fy_, tau_);
            }
        };

        timer_ = this->create_wall_timer(20ms, timer_callback); // 50 Hz
        RCLCPP_INFO(this->get_logger(), "Thrust Allocation Node initialized (4 Thrusters: Port, Stbd, Bow, Stern). Publishing /motor_pwms, /cmd_vel at 50 Hz");
    }

    void joystickCommands(const sensor_msgs::msg::Joy::ConstSharedPtr msg)
    {
        if (msg->axes.size() < 4) {
            return;
        }

        // Left stick Y: Forward/Backward (Surge: +1 = Forward, -1 = Backward)
        double raw_fx = msg->axes.at(1);
        // Left stick X: Lateral Sway (+1 = Port/Left, -1 = Starboard/Right)
        double raw_fy = msg->axes.at(0);
        // Right stick X: Steering / Yaw (+1 = Turn Left / CCW, -1 = Turn Right / CW)
        double raw_tau = msg->axes.at(3);

        // Deadzone application
        Fx_ = (std::abs(raw_fx) > deadzone_) ? raw_fx : 0.0;
        Fy_ = (std::abs(raw_fy) > deadzone_) ? raw_fy : 0.0;
        tau_ = (std::abs(raw_tau) > deadzone_) ? raw_tau : 0.0;
    }
};

int main(int argc, char* argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<ThrustAllocationNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}