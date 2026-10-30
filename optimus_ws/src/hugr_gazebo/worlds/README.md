# Maritime Competition Worlds

Contains simulation worlds for the Hugr Optimus ASV.

## Files

* **`circuit_world.sdf`**: Competition buoy field with:
  * Sun lighting and water plane.
  * **Gate 1**: Red buoy at $(8, 2)$ and Green buoy at $(8, -2)$.
  * **Gate 2**: Red buoy at $(18, 3)$ and Green buoy at $(18, -1)$.
  * **Pivot Buoy**: Yellow turnaround buoy at $(28, 0)$.
  * Hugr Optimus catamaran spawned at the origin $(0, 0)$.

## How to Test

Validate syntax:
```bash
gz sdf -k circuit_world.sdf