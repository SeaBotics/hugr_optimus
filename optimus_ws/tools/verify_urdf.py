#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse("src/hugr_description/urdf/hugr.urdf")
root = tree.getroot()

links = [l.attrib["name"] for l in root.findall("link")]
joints = [(j.attrib["name"], j.find("parent").attrib["link"], j.find("child").attrib["link"]) for j in root.findall("joint")]

print("Total links:", len(links))
print("Links present:")
for l in links:
    print(f"  - {l}")

print("\nJoint connections (Parent -> Child):")
for j, p, c in joints:
    print(f"  - {j}: {p} -> {c}")
