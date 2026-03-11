from handler import lambda_handler

import time

# Record the start time
start_time = time.perf_counter()

time.sleep(2)

# Record the end time
end_time = time.perf_counter()

# Calculate the elapsed time
elapsed_time = end_time - start_time

print(elapsed_time)
if elapsed_time > 1:
    print()

print(lambda_handler(event={"hello": "world"}))
