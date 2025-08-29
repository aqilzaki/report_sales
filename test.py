import jwt
import os

print("Module path:", jwt.__file__)
print("Has encode:", hasattr(jwt, "encode"))
print("Version:", getattr(jwt, "__version__", "NO VERSION"))
