import ast
import sys


def count_code_lines(file_path):
    """
    Counts lines of code excluding comments and docstrings.
    :param file_path: Path to the Python file.
    :return: Number of lines of code (excluding comments and docstrings).
    """
    try:
        with open(file_path) as f:
            lines = f.readlines()
        code_lines = 0
        inside_multiline_comment = False

        for line in lines:
            stripped = line.strip()
            # Skip empty lines
            if not stripped:
                continue
            # Handle multiline comments or docstrings
            if stripped.startswith('"""') or stripped.startswith("'''"):
                # Toggle multiline comment flag if it's not inline
                if (stripped.endswith('"""') or stripped.endswith("'''")) and len(stripped) > 3:
                    continue
                inside_multiline_comment = not inside_multiline_comment
                continue
            if inside_multiline_comment:
                continue
            # Skip single-line comments
            if stripped.startswith('#'):
                continue
            code_lines += 1

        print(f"Total lines of code (excluding comments and docstrings): {code_lines}")
        return code_lines
    except Exception as e:
        print(f"Error processing file: {e}")
        return None


if __name__ == "__main__":
    # Replace this with the path to your Python file
    file_path = "lines-to-count.txt"
    count_code_lines(file_path)
