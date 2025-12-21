import torch
import torch.nn as nn

class RiskClassifier(nn.Module):
    def __init__(self):
        super(RiskClassifier, self).__init__()
        # Input: Age, HR, Temp, O2, BP_Sys (5 features)
        self.layer1 = nn.Linear(5, 16)
        self.relu = nn.ReLU()
        self.layer2 = nn.Linear(16, 8)
        self.output = nn.Linear(8, 1)
        self.sigmoid = nn.Sigmoid()
        
        # Manually initialize weights to simulate a "trained" model for logic
        # High HR (idx 1) and Low O2 (idx 3) should increase risk
        with torch.no_grad():
            self.layer1.weight.data.fill_(0.01)
            self.layer1.weight.data[0][1] = 0.5  # Weight for HR
            self.layer1.weight.data[0][3] = -0.5 # Weight for O2 (lower is bad)
            # Bias tweaks
            self.output.bias.data.fill_(-2.0) # Baseline low risk

    def forward(self, x):
        x = self.layer1(x)
        x = self.relu(x)
        x = self.layer2(x)
        x = self.relu(x)
        x = self.output(x)
        return self.sigmoid(x)

    def predict(self, age, hr, temp, o2, bp_sys):
        """Returns a risk score between 0.0 and 1.0"""
        # Normalize inputs roughly
        inputs = torch.tensor([[
            age / 100.0,
            hr / 200.0,
            temp / 42.0,
            o2 / 100.0,
            bp_sys / 200.0
        ]], dtype=torch.float32)
        
        with torch.no_grad():
            score = self.forward(inputs)
        return score.item()
