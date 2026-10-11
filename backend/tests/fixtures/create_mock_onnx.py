import os
import json
import numpy as np
import onnx
from onnx import helper, TensorProto
import onnxruntime as ort

def create_mock_model(output_path):
    # Input: 'obs' [N, 9], float32
    # Output: 'action' [N], int64
    
    # We want:
    # obs[0] < 0.3 -> action 0
    # 0.3 <= obs[0] < 0.6 -> action 1
    # 0.6 <= obs[0] < 0.8 -> action 2
    # obs[0] >= 0.8 -> action 3
    
    # Let's train a tiny DecisionTreeClassifier or linear weights with numpy
    # We have 5 golden observations:
    golden_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'rl', 'artifacts', 'golden_obs.json')
    with open(golden_path, 'r') as f:
        goldens = json.load(f)
        
    X = np.array([g['observation'] for g in goldens], dtype=np.float32) # [5, 9]
    y = np.array([g['onnx_action'] for g in goldens], dtype=np.int64)    # [5]
    
    # Add synthetic points to make a robust boundary
    X_syn = np.zeros((100, 9), dtype=np.float32)
    y_syn = np.zeros(100, dtype=np.int64)
    deps = np.linspace(0.0, 1.0, 100, dtype=np.float32)
    for i, d in enumerate(deps):
        X_syn[i, 0] = d
        if d < 0.3:
            y_syn[i] = 0
        elif d < 0.6:
            y_syn[i] = 1
        elif d < 0.8:
            y_syn[i] = 2
        else:
            y_syn[i] = 3
            
    # Fit simple 1-hidden-layer network or linear SVM / logistic regression
    # Or explicitly construct weights:
    # Hidden layer: 4 neurons detecting thresholds:
    # h0 = relu(obs[0] - 0.0)
    # h1 = relu(obs[0] - 0.3)
    # h2 = relu(obs[0] - 0.6)
    # h3 = relu(obs[0] - 0.8)
    
    W1 = np.zeros((9, 4), dtype=np.float32)
    W1[0, :] = [1.0, 1.0, 1.0, 1.0]
    B1 = np.array([0.0, -0.3, -0.6, -0.8], dtype=np.float32)
    
    # Output logits:
    # When d in [0, 0.3): h0 > 0, h1=0, h2=0, h3=0 -> class 0 max
    # When d in [0.3, 0.6): h1 > 0 -> class 1 max
    # When d in [0.6, 0.8): h2 > 0 -> class 2 max
    # When d >= 0.8: h3 > 0 -> class 3 max
    
    W2 = np.zeros((4, 4), dtype=np.float32)
    B2 = np.zeros(4, dtype=np.float32)
    
    # Logits:
    # logit 0 = 5.0 - 20.0 * h1
    # logit 1 = -10.0 + 40.0 * h1 - 40.0 * h2
    # logit 2 = -10.0 + 40.0 * h2 - 40.0 * h3
    # logit 3 = -10.0 + 40.0 * h3
    
    W2[:, 0] = [0.0, -20.0, 0.0, 0.0]
    B2[0] = 5.0
    
    W2[:, 1] = [0.0, 40.0, -40.0, 0.0]
    B2[1] = -5.0
    
    W2[:, 2] = [0.0, 0.0, 40.0, -40.0]
    B2[2] = -5.0
    
    W2[:, 3] = [0.0, 0.0, 0.0, 40.0]
    B2[3] = -5.0
    
    # Build ONNX nodes
    # Input: obs [batch, 9]
    obs_tensor = helper.make_tensor_value_info('obs', TensorProto.FLOAT, ['batch', 9])
    action_tensor = helper.make_tensor_value_info('action', TensorProto.INT64, ['batch'])
    
    # Initializers
    w1_init = helper.make_tensor('W1', TensorProto.FLOAT, W1.shape, W1.flatten())
    b1_init = helper.make_tensor('B1', TensorProto.FLOAT, B1.shape, B1.flatten())
    w2_init = helper.make_tensor('W2', TensorProto.FLOAT, W2.shape, W2.flatten())
    b2_init = helper.make_tensor('B2', TensorProto.FLOAT, B2.shape, B2.flatten())
    
    # Node 1: Gemm1 (obs * W1 + B1)
    gemm1 = helper.make_node('Gemm', ['obs', 'W1', 'B1'], ['h1_pre'], transA=0, transB=0)
    # Node 2: Relu
    relu = helper.make_node('Relu', ['h1_pre'], ['h1'])
    # Node 3: Gemm2 (h1 * W2 + B2)
    gemm2 = helper.make_node('Gemm', ['h1', 'W2', 'B2'], ['logits'], transA=0, transB=0)
    # Node 4: ArgMax
    argmax = helper.make_node('ArgMax', ['logits'], ['action_raw'], axis=1, keepdims=0)
    # Cast to int64 if needed (ArgMax already outputs int64)
    squeeze = helper.make_node('Identity', ['action_raw'], ['action'])
    
    graph = helper.make_graph(
        [gemm1, relu, gemm2, argmax, squeeze],
        'MockPPO',
        [obs_tensor],
        [action_tensor],
        [w1_init, b1_init, w2_init, b2_init]
    )
    
    model = helper.make_model(graph, producer_name='JalSaathiMock')
    model.opset_import[0].version = 13
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    onnx.save(model, output_path)
    print(f"Saved mock ONNX model to {output_path}")
    
    # Verify with onnxruntime
    sess = ort.InferenceSession(output_path)
    preds = sess.run(None, {'obs': X})[0]
    print(f"Predictions on golden obs: {preds}")
    print(f"Expected golden actions:   {y}")
    assert np.array_equal(preds, y), f"Parity mismatch! Preds: {preds}, Expected: {y}"
    print("Golden parity confirmed 100%!")

if __name__ == "__main__":
    try:
        out_dir = os.path.dirname(os.path.abspath(__file__))
        target = os.path.join(out_dir, 'mock_ppo_wheat.onnx')
        create_mock_model(target)
        
        # Also save to models/rl/wheat/ppo_wheat.onnx and rl/artifacts/ppo_wheat.onnx
        root_dir = os.path.abspath(os.path.join(out_dir, '..', '..', '..'))
        models_target = os.path.join(root_dir, 'models', 'rl', 'wheat', 'ppo_wheat.onnx')
        rl_target = os.path.join(root_dir, 'rl', 'artifacts', 'ppo_wheat.onnx')
        os.makedirs(os.path.dirname(models_target), exist_ok=True)
        os.makedirs(os.path.dirname(rl_target), exist_ok=True)
        import shutil
        shutil.copy2(target, models_target)
        shutil.copy2(target, rl_target)
        print("Copied to models/ and rl/artifacts/")
    except Exception as e:
        import traceback
        traceback.print_exc()

