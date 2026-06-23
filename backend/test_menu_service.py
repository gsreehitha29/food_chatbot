import sys
import os
from services.menu_service import get_all_restaurants

print("Calling get_all_restaurants():")
res = get_all_restaurants()
print("Result:")
import pprint
pprint.pprint(res)
