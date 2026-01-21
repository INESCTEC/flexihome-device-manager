import os
from prance import ResolvingParser
from pathlib import Path

dir_path = Path(os.path.abspath(__file__)).parent
print(dir_path)
spec_path = os.path.join(dir_path.parent, "openapi", "openapi.yaml")
print(spec_path)

parser = ResolvingParser(spec_path)

DeviceSchema = parser.specification['components']['schemas']['Device']
UserDeviceListSchema = parser.specification['components']['schemas']['UserDeviceList']
NotDisturbSchema = parser.specification['components']['schemas']['NotDisturb']

