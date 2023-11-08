import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "package": ["tkinter", "scikit-learn","PIL","numpy"],
}

setup(
    name="PrecistionMapper",
    version="0.1",
    description="GuideGoodPart",
    #options={"build_exe": build_exe_options},
    executables=[Executable("main.py")],
)