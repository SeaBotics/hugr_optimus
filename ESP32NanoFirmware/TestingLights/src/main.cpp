#include <Arduino.h>
#include <ESP32Servo.h>
#include <micro_ros_platformio.h>

#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>

#include <std_msgs/msg/char.h>
#include <std_msgs/msg/int32_multi_array.h>

// Definición de Pines de LEDs
const int LED_PIN[] = {6, 7, 8, 9};
#define LED_COUNT (sizeof(LED_PIN) / sizeof(LED_PIN[0]))

#define OFF 6
#define RED 9
#define YELLOW 8
#define GREEN 7

// Definición de Pines de Motores
const int MOTOR_PINS[] = {3, 4, 11, 12};
#define MOTOR_COUNT (sizeof(MOTOR_PINS) / sizeof(MOTOR_PINS[0]))

#define PWM_STOP 1500

Servo motors[MOTOR_COUNT];

// Objetos de micro-ROS
rcl_subscription_t subscriber_led;
rcl_subscription_t subscriber_motors;
std_msgs__msg__Char msg_led;
std_msgs__msg__Int32MultiArray msg_motors;

rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;

int32_t motor_buffer[4];

void setLightColour(char command) {
  digitalWrite(OFF, HIGH);  //TODO remove it and turn it into low
  digitalWrite(RED, LOW);
  digitalWrite(YELLOW, LOW);
  digitalWrite(GREEN, LOW);

  switch (command) {
    case 'o': digitalWrite(OFF, HIGH); break;
    case 'r': digitalWrite(RED, HIGH); break;
    case 'g': digitalWrite(GREEN, HIGH); break;
    case 'y': digitalWrite(YELLOW, HIGH); break;
    default:  digitalWrite(RED, HIGH); break;
  }
}

void led_callback(const void * msgin) {
  const std_msgs__msg__Char * msg = (const std_msgs__msg__Char *)msgin;
  setLightColour(msg->data);
}

void motor_callback(const void * msgin) {
  const std_msgs__msg__Int32MultiArray * msg = (const std_msgs__msg__Int32MultiArray *)msgin;
  if (msg->data.size >= MOTOR_COUNT) {
    for (int i = 0; i < MOTOR_COUNT; i++) {
      int pwm = constrain(msg->data.data[i], 1100, 1900);
      motors[i].writeMicroseconds(pwm);
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("Starting ESP32 Nano Node...");
  // Inicialización de LEDs
  for (int i = 0; i < LED_COUNT; i++) {
    pinMode(LED_PIN[i], OUTPUT);
  }
  
  // Armado de ESCs
  for (int i = 0; i < MOTOR_COUNT; i++) {
    motors[i].attach(MOTOR_PINS[i], 1100, 1900);
    motors[i].writeMicroseconds(PWM_STOP);
  }
  delay(3500);

  // Inicialización de micro-ROS sobre Serial USB
  set_microros_serial_transports(Serial);

  allocator = rcl_get_default_allocator();
  rclc_support_init(&support, 0, NULL, &allocator);
  rclc_node_init_default(&node, "esp32_nano_node", "", &support);

  // Suscriptor de LEDs
  rclc_subscription_init_default(
    &subscriber_led,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Char),
    "/led_color"
  );

  // Suscriptor de Motores (Asignando buffer estático para evitar fugas de memoria)
  msg_motors.data.capacity = 4;
  msg_motors.data.size = 0;
  msg_motors.data.data = motor_buffer;

  rclc_subscription_init_default(
    &subscriber_motors,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32MultiArray),
    "/motor_pwms"
  );

  // Configuración del Executor (2 suscripciones)
  rclc_executor_init(&executor, &support.context, 2, &allocator);
  rclc_executor_add_subscription(&executor, &subscriber_led, &msg_led, &led_callback, ON_NEW_DATA);
  rclc_executor_add_subscription(&executor, &subscriber_motors, &msg_motors, &motor_callback, ON_NEW_DATA);
  Serial.println("Setup complete. Waiting for messages...");
}

void loop() {
  rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10));
}