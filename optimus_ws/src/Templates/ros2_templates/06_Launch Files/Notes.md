The ros2 launch files are usually made in either .xml and .py | or .yaml (not used practically)
Usually called name.launch.filetype
Can create a structure, order, yam files etc.

- .xml files are much simpler than python files. (use me)
- .py files may only in special cases, where even a hybdrid xml strcuture cannot be used.
- rather import advanced single case launch files in python into the .xml
- Use the: <include file="$(find-pkg-share package_name)/launch/launch_file" />
- .py syntax is complicated, and not better in practice.

- Maybe looking into namespaces for grouping nodes is beneficiary.

# Run it with:
`ros2 launch <packagename> <launch file>`

pid is process id

Where to create laucnh file:
Dedicated package is best practice

`ros2 pkg create <name_bringup> --build-type`
 Usually have:
 - package.xml
Add <exec_depend> for the nodes

 - CMakeLists.txt

install(DIRECTORY
    launch
    DESTINATION share/${package_name}/
)

 and a folder -> Launch
 Delete rest

 # Remapping and loading parameters in launch file
 Files can be remapped or changed parameters when launching the files
`<remap>`
`<param>`
