import os

EXCLUDED_DIRS = {'.venv', '.git', '__pycache__', '.idea', '.mypy_cache', '.pytest_cache', 'build', 'dist'}

def print_tree(startpath, indent=""):
    for item in sorted(os.listdir(startpath)):
        if item in EXCLUDED_DIRS:
            continue

        path = os.path.join(startpath, item)
        if os.path.isdir(path):
            print(f"{indent}📁 {item}")
            print_tree(path, indent + "    ")
        else:
            print(f"{indent}📄 {item}")

if __name__ == "__main__":
    root = os.path.dirname(os.path.abspath(__file__))  # usa el directorio actual
    print_tree(root)
