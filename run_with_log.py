import sys
import io

# Redirect stdout and stderr to a file
log_file = open("execution_log.txt", "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

try:
    from main import run_assignment
    run_assignment()
except Exception as e:
    print(f"Error occurred: {str(e)}")
finally:
    log_file.close()
