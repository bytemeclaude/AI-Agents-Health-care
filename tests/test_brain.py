from agent.brain import RiskClassifier
import torch

def test_risk_classifier_output_range():
    brain = RiskClassifier()
    # Test average case
    score = brain.predict(50, 80, 37, 98, 120)
    assert 0.0 <= score <= 1.0

def test_risk_classifier_high_risk():
    brain = RiskClassifier()
    # Test high risk case: High HR, Low O2
    score = brain.predict(80, 140, 39, 85, 160)
    # The current mock weights are simple, but we expect higher score for worse vitals
    # We might need to adjust expectation based on the hardcoded weights in brain.py
    # Since I can't easily calc the exact output of the NN in my head, I'll just assert it's a float.
    # But ideally we should check if risk increases.

    score_normal = brain.predict(20, 60, 37, 99, 110)
    assert score > score_normal
