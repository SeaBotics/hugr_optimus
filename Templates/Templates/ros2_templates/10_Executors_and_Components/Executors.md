# Executors in ROS2
Configure callbacks in nodes

Multithreading (This is important)
## What is Multithreading


Callbacks and spin 

Directly related to the spin mechanism.

You make a package for it like all the others topics, server, actions, lifeycle nodes, gazebo etc.

Usually have
- Single threaded executor
- multi threaded executor

Executor: Handles the scheduling and execution of node callbacks (subscriptions, timers, service servers).

ROS2 Executor
An Executor is the core component in ROS2 that manages the event loop. It listens for incoming messages, service calls, and actions, and dispatches them to threads for execution.

Why It Is Important
Thread Management: Determines whether node callbacks run sequentially (single-threaded) or in parallel (multi-threaded).

Flow Control: Bridges ROS2 events and operating system threads via the spin() mechanism.

Blocking Prevention: Prevents long-running or synchronous operations in one callback from blocking others (e.g., sensor streams vs. control loops).

Executor Types
SingleThreadedExecutor:

Default behavior.

Executes all callbacks sequentially in a single thread.

Eliminates race conditions, but vulnerable to blocking.

MultiThreadedExecutor:

Executes multiple callbacks in parallel using a thread pool.

Requires explicit synchronization (e.g., ReentrantMutex) to prevent data corruption with shared state.