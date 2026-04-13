# -*- coding: utf-8 -*-
import os
os.chdir(r'C:/Users/DZ/Desktop/CodexDB/tmp')
import pandas as pd

# Read attractions data
attractions = pd.read_csv("C:/Users/DZ/Desktop/CodexDB/tmp/attractions.csv")

# Filter attractions in Linzhi and sort by rating in descending order
linzhi_attractions = attractions[attractions["address"].str.contains("林芝")]
top_attractions = linzhi_attractions.sort_values("rating", ascending=False).head()

# Select columns 'name' and 'address' for the top attractions
result = top_attractions[["name", "address"]]

# Write result to 'result.csv' with header
result.to_csv("result.csv", index=False, header=["景点名称", "地址"])