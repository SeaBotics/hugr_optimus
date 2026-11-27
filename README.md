# hugr_optimus

The official repository for SeaBotics Hugr Optimus. This repo is the successor to the Hugr Primus repository for legacy code.

The Hugr Optimus is a fully autonomous surface vessel, i.e. Autonomous Boat, built by students to compete in national and international competitions.

We are from the University of Agder, and open for all students in Agder.

## Contributions

In order to contribute to this repository, please read the information and guidelines below.

## Overview

```tree
hugr_optimus
├─ Dependencies         - External dependencies
├─ Documentation        - Tasks, schematics, datasheets, etc..
├─ Misc                 - Code examples: ROS2 in practice
├─ Templates            - ROS2 templates for different frameworks
├─ init.sh              - Initialization script, downloads all system dependencies unto ASV
├─ start.sh             - ROS node script, runs all ROS 2 nodes and launch files as bakcground processes
└─ optimus_ws/src/      - Main workspace for Hugr Optimus (code to run on SBC)

```
---

### Tech Stack

`hugr_optimus` is a repository that is owned, maintained and managed by the SeaBotics Student Association. The project tech stack mainly revolves around a few specific frameworks and languages, but component work may require more specialized and nuanced languages. In order to get started with development a few basics must be in order:

- Ubuntu 24.04 LTS
- ROS 2 Jazzy
- C/C++ & Python

In addition to these basics you may find downloading an IDE to be preferable for development through the project Docker container, preferably Visual Studio Code (VSC) due to its Docker integration. Hardware and Software technology and interfacing overviews are located in `Documentation/`. You may follow the setup steps below in order to set up your computer to begin developing with the code base. 

### Setup

In order to run, test and modify the code we've created a docker environment which you may run whenever you are going to access the repository code on your computer.

#### Step 1 - Download Docker

You may download Docker natively on your computer for your specific Operating System (OS) by following the links below:

- [Docker Desktop - Mac](https://docs.docker.com/desktop/setup/install/mac-install/)
- [Docker Desktop - Windows](https://docs.docker.com/desktop/setup/install/windows-install/)
- [Docker Desktop - Linux](https://docs.docker.com/desktop/setup/install/linux/)

Want to know more about what Docker is and how it works? Check out [this link](https://docs.docker.com/get-started/docker-overview/). If you are a Windows user you will have to install WSL2 and run Ubuntu 24.04 LTS on it there. To install WSL2 follow [this link](https://learn.microsoft.com/en-us/windows/wsl/install). 

#### Step 2 - Fork the repository

In order to make contributions towards the main code repository you will need to fork the main repository to your local GitHub user. In this way, when you want to merge your code with the main repository you will create a Pull Request (PR), which in turn will automatically trigger a Continous Integration (CI) pipeline which runs various tests to verify your code is valid and able to be merged without causing major issues. 

To perform the fork, follow the steps below:

--- 

Start by clicking on the dropdown next to the fork button.
![Start by clicking on the dropdown next to the fork button](Documentation/figures/fork_step1.png)

Click the create new fork button to create a new fork local to your GitHub user.
![Click the create new fork button](Documentation/figures/fork_step2.png)

Click "Create fork" again to create the fork, leave every input as standard, no need to change anything.
![Leave everything as standard and click create](Documentation/figures/fork_step3.png)

Congrats! You now have a local fork of the main repository, ready to do with as you please!

#### Step 3 - Clone the repository

To interact with the code on your local computer you must clone your fork to your computer. Cloning is typically done in two ways, through `HTTPS` or via `SSH`.

---

Click the code dropdown button.
![Click the code dropdown button](Documentation/figures/clone_step1.png)


You may copy from either HTTPS...
![You may copy from either HTTPS](Documentation/figures/clone_step2.png)

Or from SSH.
![Or SSH](Documentation/figures/clone_step3.png)

If you're going to utilize SSH, make sure to add your SSH key to your GitHub profile with read/write permissions. To get more familiar with SSH, learn how to generate a key and add it to your profile, follow [this link](https://docs.github.com/en/authentication/connecting-to-github-with-ssh).

To clone the repository to your computer, stand in the root of your `Projects/` folder and type in `git clone <link from GitHub>. You should now be able to move into your forked version of `hugr_optimus`

#### Step 4 - Run the Docker Container

In order to develop code through the Docker Container, you will need to boot it before each coding session. Run the following code in your terminal (Git Bash, Linux Terminal etc.) in order to boot up the container. Make sure you're standing in the root of the repository folder when you run the container!

`docker build -t ros2-jazzy-dev .`

Then run the next sequence of code as long as you're in the root of the repository folder:

`docker run -it -d \
  --name optimus-dev \
  -v $(pwd)/optimus_ws/src:/home/ros/optimus_ws/src \
  ros2-jazzy-dev bash`

You might need to perform the following commands to be able to run the container:

`sudo usermod -aG docker $USER && newgrp docker` 

#### Step 5 - Git and Development

When you're going to develop on your forked repository, it is important that you are connected to the standardized Docker container environment to avoid cross-platform contamination and avoiding problems of having some tools work but not others. 

After you've booted up the container you may access it through [VSCode](https://code.visualstudio.com/download?_exp_download=fb315fc982) by adding the Docker extension to VSCode and then clicking the arrows in the bottom left:

![Click the two arrown on bottom left](Documentation/figures/vs_1.png)

You must then attach to the running container:

![Attach to running container](Documentation/figures/vs_2.png)

Choose the `/optimus_dev` container for development:

![Choose correct container](Documentation/figures/vs_3.png)

You will see you're in a container when the arrows in the bottom left turn blue and the explorer highlights the source directory of the container as displayed in red here:

![Display of container environment](Documentation/figures/vs_4.png)

When you're in the container environment you may alter code and develop code as you see fit, however to push the changes you've made unto your forked repository you must exit the remote connection by clicking on the blue arrows in the bottom left and clicking the `close remote connection` button on the explorer:

![Close remote connection](Documentation/figures/vs_5.png)

You may now run your Git commands to add your edited files and push them. You may alternatively open a terminal on your computer that is not running through VSCode and utilize Git commands from there. 

When you're working with Git, make sure to sort out any git merge conflicts internally within your fork and your team. This can be done by fetching the new head of the development branch of your repository and performing a rebase before starting development and after performing development, and then comitting and pushing your code. If you have any questions regarding Git, consult one of the senior software members or you may utilize an LLM if conflicts or questions are minor.  

### Rules

...
---

> Maintained by SeaBotics Student Association
