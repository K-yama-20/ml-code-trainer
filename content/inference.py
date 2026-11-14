"""PT09: train/eval modes, BatchNorm statistics and gradient-free inference.

Every result includes a case-dependent value (outputs, statistics or the
fixture's starting mode), so a hard-coded mode flag cannot pass."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "PT09"
LESSONS = load_lessons(__file__)


def fixed_linear(model_expr, weight, bias, x, extra=""):
    return (f"model = {model_expr}\nwith torch.no_grad():\n    model[0].weight.copy_(torch.tensor({weight!r}))\n"
            f"    model[0].bias.copy_(torch.tensor({bias!r}))\n{extra}x = torch.tensor({x!r})")


ALTERNATIVES = {
    1: ["model = nn.Dropout(0.5)\nmodel.train(False)", "model = nn.Sequential(nn.Linear(1, 1), nn.Dropout(0.2))\nmodel.train(True)\nmodel.train(False)"],
    2: ["x = torch.tensor([0.0, -1.0, 5.0])", "x = torch.tensor(2.5)"],
    3: ["model = nn.Sequential(nn.Dropout(0.5))", "model = nn.Sequential(nn.Linear(1, 2), nn.BatchNorm1d(2), nn.ReLU(), nn.Dropout(0.3), nn.Linear(2, 1))"],
    4: ["model = nn.Linear(2, 1)\nwith torch.no_grad():\n    model.weight.copy_(torch.tensor([[-1.0, 0.0]]))\n    model.bias.fill_(0.0)\n"
        "x = torch.tensor([[3.0, 9.0]])",
        "model = nn.Linear(2, 1)\nwith torch.no_grad():\n    model.weight.copy_(torch.tensor([[0.5, 0.5]]))\n    model.bias.fill_(-1.0)\n"
        "x = torch.tensor([[2.0, 2.0], [4.0, 0.0], [0.0, 0.0]])"],
    5: ["x = torch.tensor([[0.5]], requires_grad=True)", "x = torch.tensor([3.0, 0.0, -1.0], requires_grad=True)"],
    6: ["model = nn.BatchNorm1d(1)\nx = torch.tensor([[0.0], [2.0], [4.0]])", "model = nn.BatchNorm1d(3)\nx = torch.tensor([[1.0, 1.0, 0.0], [3.0, 1.0, 4.0]])"],
    7: ["model = nn.Dropout(0.5)\nmodel.train(False)\nx = torch.tensor([4.0])",
        "model = nn.Sequential(nn.Dropout(0.1))\nmodel.train(True)\nx = torch.tensor([[1.0, -1.0], [0.0, 2.0]])"],
    8: ["model = nn.BatchNorm1d(1)\nwith torch.no_grad():\n    model.running_mean.copy_(torch.tensor([2.0]))\n    model.running_var.copy_(torch.tensor([1.0]))\n"
        "x = torch.tensor([[2.0], [5.0]])",
        "model = nn.BatchNorm1d(2)\nx = torch.tensor([[1.0, -1.0], [3.0, 0.0]])"],
    9: ["model = nn.BatchNorm1d(1)\nx = torch.tensor([[2.0], [4.0], [9.0]])",
        "model = nn.BatchNorm1d(2)\nwith torch.no_grad():\n    model.running_mean.copy_(torch.tensor([10.0, -10.0]))\n"
        "x = torch.tensor([[0.0, 0.0], [0.0, 2.0]])"],
    10: ["model = nn.BatchNorm1d(1)\nx = torch.tensor([[5.0], [7.0]])",
         "model = nn.BatchNorm1d(3)\nwith torch.no_grad():\n    model.running_mean.copy_(torch.tensor([1.0, 2.0, 3.0]))\n"
         "x = torch.tensor([[9.0, 9.0, 9.0], [0.0, 0.0, 0.0]])"],
    11: [fixed_linear("nn.Sequential(nn.Linear(2, 2), nn.Dropout(0.5))", [[1.0, 1.0], [1.0, -1.0]], [0.0, 0.5], [[1.0, 0.0], [0.0, 1.0]]),
         fixed_linear("nn.Sequential(nn.Linear(1, 3), nn.Dropout(0.9))", [[1.0], [-1.0], [0.0]], [0.0, 0.0, 0.5], [[2.0], [-2.0], [0.25]])],
    12: ["model = nn.Linear(1, 1)\nwith torch.no_grad():\n    model.weight.fill_(-1.0)\n    model.bias.fill_(0.0)\nx = torch.tensor([[3.0]])",
         "model = nn.Linear(1, 1)\nwith torch.no_grad():\n    model.weight.fill_(0.5)\n    model.bias.fill_(2.0)\nx = torch.tensor([[2.0], [4.0], [-4.0]])"],
    13: [fixed_linear("nn.Sequential(nn.Linear(2, 2), nn.Dropout(0.5))", [[1.0, 0.0], [0.0, 1.0]], [0.0, 0.0], [[1.0, 0.0], [0.0, 1.0]],
                      "model.train()\n") + "\ny = torch.tensor([0, 1])",
         fixed_linear("nn.Sequential(nn.Linear(1, 2), nn.Dropout(0.5))", [[1.0], [-1.0]], [0.0, 0.0], [[1.0], [-1.0], [2.0]],
                      "model.train()\n") + "\ny = torch.tensor([1, 1, 1])"],
    14: [fixed_linear("nn.Sequential(nn.Linear(2, 2), nn.ReLU(), nn.Dropout(0.5))", [[0.0, 1.0], [1.0, 0.0]], [1.0, 1.0], [[-3.0, 2.0]]),
         fixed_linear("nn.Sequential(nn.Linear(1, 3), nn.ReLU(), nn.Dropout(0.2))", [[1.0], [-1.0], [2.0]], [0.0, 0.0, -1.0], [[1.0], [-2.0]])],
    15: ["model = nn.BatchNorm1d(1)\ntrain_x = torch.tensor([[0.0], [0.0]])\ntest_x = torch.tensor([[1.0]])",
         "model = nn.BatchNorm1d(2)\ntrain_x = torch.tensor([[1.0, 10.0], [3.0, 30.0], [5.0, 20.0]])\ntest_x = torch.tensor([[3.0, 20.0], [0.0, 0.0]])"],
    16: ["x = torch.tensor([1.0, 2.0], requires_grad=True)\nenabled = True", "x = torch.tensor([[0.5], [-0.5]], requires_grad=True)\nenabled = False"],
    17: [fixed_linear("nn.Sequential(nn.Linear(2, 1), nn.Dropout(0.5))", [[2.0, -1.0]], [0.5], [[1.0, 1.0]]),
         fixed_linear("nn.Sequential(nn.Linear(1, 1), nn.Dropout(0.9))", [[-1.0]], [0.0], [[4.0], [0.0], [-2.0]])],
    18: [fixed_linear("nn.Sequential(nn.Linear(1, 1), nn.Dropout(0.5))", [[-2.0]], [0.0], [[1.0], [2.0]], "model.train(True)\n"),
         fixed_linear("nn.Sequential(nn.Linear(2, 1), nn.Dropout(0.5))", [[1.0, 1.0]], [-1.0], [[0.5, 0.5]], "model.train(False)\n")],
}

_PRELUDE = """
import numpy as np
def _np(t):
    return np.asarray(t.tolist(), dtype=np.float64).reshape(tuple(t.shape))
def _f(a):
    return torch.from_numpy(np.array(a, dtype=np.float64, order="C")).to(torch.float32)
def _lin(layer, data):
    return _np(data) @ _np(layer.weight).T + _np(layer.bias)
def _bn_train(data):
    a = _np(data)
    return (a - a.mean(axis=0)) / np.sqrt(a.var(axis=0) + 1e-5)
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "expected = (model.training, False)",
    2: "expected = _f(_np(x))",
    3: "expected = [False for _ in model]",
    4: "expected = (_f(_lin(model, x)), False)",
    5: "expected = (_f(_np(x) * 2), False)",
    6: "expected = _f(_bn_train(x))",
    7: "expected = (_f(_np(x)), model.training)",
    8: "expected = _f((_np(x) - _np(model.running_mean)) / np.sqrt(_np(model.running_var) + 1e-5))",
    9: "expected = _f(0.9 * _np(model.running_mean) + 0.1 * _np(x).mean(axis=0))",
    10: "expected = _f(_np(model.running_mean))",
    11: "expected = torch.tensor(_lin(model[0], x).argmax(axis=1), dtype=torch.int64)",
    12: "expected = (_f(_lin(model, x)), False)",
    13: "expected = (float(np.mean(_lin(model[0], x).argmax(axis=1) == _np(y))), True)",
    14: "expected = _f(np.maximum(_lin(model[0], x), 0))",
    15: ("_t = _np(train_x)\n_rm = 0.1 * _t.mean(axis=0)\n_rv = 0.9 + 0.1 * _t.var(axis=0, ddof=1)\n"
         "expected = _f((_np(test_x) - _rm) / np.sqrt(_rv + 1e-5))"),
    16: "expected = (_f(_np(x) * 3), enabled)",
    17: "expected = (_f(_lin(model[0], x)), [True, False])",
    18: "expected = (_f(_lin(model[0], x)), model.training)",
}.items()}

RULES = {
    1: {"required": "call:eval"},
    2: {"required": "call:eval"},
    3: {"required": "call:eval"},
    4: {"required": "call:inference_mode"},
    5: {"required": "call:no_grad"},
    6: {"required": "call:train"},
    7: {"required": 'all:["call:eval", "call:train"]'},
    8: {"required": "call:eval"},
    9: {"required": "call:train"},
    10: {"required": "call:eval"},
    11: {"required": 'all:["call:eval", "call:no_grad"]'},
    12: {"required": "call:no_grad"},
    13: {"required": 'all:["call:eval", "call:train"]'},
    14: {"required": "call:eval"},
    15: {"required": 'all:["call:eval", "call:train"]'},
    16: {"required": "call:set_grad_enabled"},
    17: {"required": "call:eval"},
    18: {"required": "FunctionDef"},
}

WRONG = {
    1: ["model.eval()\nresult = (model.training, model.training)", "before = model.training\nmodel.train()\nresult = (before, model.training)"],
    2: ["dropout = nn.Dropout(0.5)\ndropout.eval()\nresult = dropout(x) * 2"],
    3: ["model.eval()\nresult = [m.training for m in model.modules()]"],
    4: ["with torch.inference_mode():\n    out = model(x)\nresult = (out, True)"],
    5: ["out = nn.Identity().eval()(x * 2)\nresult = (out, out.requires_grad)"],
    6: ["model.eval()\nresult = model(x)"],
    7: ["was_training = model.training\nmodel.eval()\nwith torch.no_grad():\n    out = model(x)\nmodel.train()\nresult = (out, model.training)"],
    8: ["model.train()\nresult = model(x)"],
    9: ["model.eval()\nmodel(x)\nresult = model.running_mean.clone()\nmodel.train()"],
    10: ["model.train()\nmodel(x)\nresult = model.running_mean.clone()\nmodel.eval()"],
    11: ["model.eval()\nwith torch.no_grad():\n    logits = model(x)\nresult = logits.argmax(dim=0)"],
    12: ["def predict(x):\n    return model(x)\n\n\nout = predict(x)\nresult = (out, out.requires_grad)"],
    13: ["model.eval()\nwith torch.no_grad():\n    pred = model(x).argmax(dim=1)\naccuracy = (pred == y).float().mean().item()\nresult = (accuracy, model.training)\nmodel.train()"],
    14: ["model.eval()\nwith torch.no_grad():\n    result = model[0](x)"],
    15: ["model.eval()\nwith torch.no_grad():\n    result = model(test_x)\nmodel.train()"],
    16: ["with torch.set_grad_enabled(not enabled):\n    out = x * 3\nresult = (out, out.requires_grad)"],
    17: ["model.train()\nwith torch.no_grad():\n    out = model(x)\nresult = (out, [m.training for m in model.children()])"],
    18: ["def predict(model, x):\n    model.eval()\n    with torch.no_grad():\n        out = model(x)\n    model.train()\n    return out\n\n\nresult = (predict(model, x), model.training)"],
}


def compile_inference(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
