"""
Main entrypoint `sgrun`.
"""
import os
import sys
from distutils import spawn


def main():
    """
    The first code run when invoking the sgrun command, e.g. `sgrun python my_application.py --port 8080`.
    - Prepends the sgrun/bootstrap directory to PYTHONPATH
    - Executes the commandline, stripping `sgrun`, e.g. `python my_application.py --port 8080`
    - In our new execution, Python will run `sgrun/bootstrap/sitecustomize.py` before running our application code.
    """
    sitecustomize_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))

    python_path = os.getenv("PYTHONPATH")

    if python_path:
        os.environ["PYTHONPATH"] = "{}{}{}".format(
            sitecustomize_dir, os.path.pathsep, python_path
        )
    else:
        os.environ["PYTHONPATH"] = sitecustomize_dir

    executable = sys.argv[1]
    executable = spawn.find_executable(executable)

    os.execl(executable, executable, *sys.argv[2:])


if __name__ == "__main__":
    main()
