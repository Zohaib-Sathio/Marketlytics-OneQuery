from datetime import datetime

ts = 1751525140.797879  # example Slack timestamp
dt = datetime.fromtimestamp(ts)

print(dt.strftime("%Y-%m-%d %H:%M:%S"))
