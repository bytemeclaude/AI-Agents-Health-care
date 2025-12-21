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
            # Ensure the first neuron in layer 1 pays attention to HR and O2
            self.layer1.weight.data[0][1] = 2.0  # Positive weight for HR (Higher HR -> Higher activation)
            self.layer1.weight.data[0][3] = -2.0 # Negative weight for O2 (Lower O2 -> Higher activation if we consider 1-O2, but here input is O2)
                                                # Wait, O2 input is 0.98. If weight is negative, high O2 -> lower activation.
                                                # Low O2 -> less negative -> higher activation relative to high O2. Correct.

            # Ensure the signal propagates through layer 2
            self.layer2.weight.data.fill_(0.1)
            self.layer2.weight.data[0][0] = 1.0 # Pass the first neuron of layer 1 through

            # Ensure the output layer picks it up
            self.output.weight.data.fill_(0.1)
            self.output.weight.data[0][0] = 1.0

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
