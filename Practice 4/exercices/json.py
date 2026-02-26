import json

#1 Open JSON file
with open("json/sample-data.json", "r") as f:
    data = json.load(f)

#2 Print header
print("Interface Status")
print("=" * 60)
print(f"{'DN':40} {'Speed':8} {'MTU':6}")
print("-" * 60)

#3 Get interfaces list (structure from file)
interfaces = data["imdata"]

#4 Print each interface
for item in interfaces:
    iface = item["l1PhysIf"]["attributes"]

    dn = iface.get("dn", "")
    speed = iface.get("speed", "")
    mtu = iface.get("mtu", "")

    print(f"{dn:40} {speed:8} {mtu:6}")