import os
import runpy

script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "math-wizard.py")
runpy.run_path(script, run_name="__main__")
