# Hugr Optimus - Gazebo Model

This folder contains the Gazebo Harmonic model for the Hugr Optimus catamaran.

This should be change with the right parameters of the boat. !!!!!!

## Files

* **`model.config`**: Model metadata (tells Gazebo the name, author, and version).
* **`model.sdf`**: Main simulation file. Defines:
  * **Physics**: 28 kg mass, 3D CAD mesh, and water drag.
  * **4 Motors**: Two forward thrusters (M1, M2) and two lateral thrusters (M3, M4).
  * **Sensors**: Front camera (`/camera/image_raw`), IMU, and GPS.

## How to Test

Run this command to check for syntax errors:

```bash
gz sdf -k model.sdf