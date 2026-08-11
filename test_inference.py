import sys, os
import torch
import numpy as np
import joblib

sys.path.insert(0, "./ml")
from inference import ForecastModel

model = ForecastModel("./ml/artifacts")
scaler = model.scalers.get("SIND-001-PZ")

# dummy data
x = np.linspace(500, 520, 24).reshape(-1, 1)
x_scaled = scaler.transform(x).flatten()

node_feat = torch.zeros((len(model.well_list), 8))
adj = torch.eye(len(model.well_list))
idx = model.well_list.index("SIND-001-PZ")

mean, std = model._forward_mc(
    torch.FloatTensor(x_scaled).unsqueeze(0).unsqueeze(-1),
    node_feat, adj, [idx], ["Other"], n_samples=5
)
print("Mean scaled:", mean)
print("Mean inverted:", scaler.inverse_transform(mean.reshape(-1,1)).flatten())
