import time 
import datetime

# Get the current date
now = datetime.datetime.now()

# Format the date as "dd/mm/yyyy"
start_time = now.strftime("%d/%m/%Y")

print(f"Authorization server started on {start_time}")

keep_running = True 

while(keep_running):
    print("Basic queries")
    time.sleep(1)


if __name__ == '__main__':
    main()