import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

df = pd.read_excel(
    "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/DanceClip_TAG/stress_label_84.xlsx"
)
df = df.set_index("Numéro")

fig, axes = plt.subplots(3, 3, figsize=(15, 12))

ages = df["Age"].dropna()
