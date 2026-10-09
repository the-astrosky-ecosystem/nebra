import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "mkdocs", "build"], capture_output=True, text=True, check=False
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)