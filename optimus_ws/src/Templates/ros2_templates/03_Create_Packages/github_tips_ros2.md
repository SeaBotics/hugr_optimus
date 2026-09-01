# Why Exclude ROS 2 Build Artifacts in Git

## The Problem
* **Platform Incompatibility:** Binaries in `build/` and `install/` are compiled for the specific local machine architecture, OS version, and library paths. Pushing them breaks execution on any other system.
* **Redundancy:** `colcon` generates these files deterministically from source code. Storing them bloats repository size unnecessarily.
* **Conflict State:** Hardcoded absolute paths inside compiled artifacts trigger linker and path resolution errors when cloned to a different user directory.

## The Solution (`.gitignore`)
* **`build/`:** Excluded because intermediate object files and compiler caches are machine-local.
* **`install/`:** Excluded because final executables and setup scripts must be generated locally via `colcon build` to match the target environment's absolute workspace paths.
* **`log/`:** Excluded because execution logs contain local timestamps, hardware metrics, and transient run data irrelevant to source history.

# Procedure
In the root of the workspace create a file: .gitignore

Insert:
/build/
/install/
/log/
__pycache__/
*.egg-info/
.vscode/
.idea/
.colcon*
*.pyc
*.pyo