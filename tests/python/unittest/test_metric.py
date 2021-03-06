# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import mxnet as mx
import numpy as np
import json

def check_metric(metric, *args, **kwargs):
    metric = mx.metric.create(metric, *args, **kwargs)
    str_metric = json.dumps(metric.get_config())
    metric2 = mx.metric.create(str_metric)

    assert metric.get_config() == metric2.get_config()

def test_metrics():
    check_metric('acc', axis=0)
    check_metric('f1')
    check_metric('perplexity', -1)
    check_metric('pearsonr')
    check_metric('nll_loss')
    composite = mx.metric.create(['acc', 'f1'])
    check_metric(composite)

def test_nll_loss():
    metric = mx.metric.create('nll_loss')
    pred = mx.nd.array([[0.2, 0.3, 0.5], [0.6, 0.1, 0.3]])
    label = mx.nd.array([2, 1])
    metric.update([label], [pred])
    _, loss = metric.get()
    expected_loss = 0.0
    expected_loss = -(np.log(pred[0][2].asscalar()) + np.log(pred[1][1].asscalar())) / 2
    assert loss == expected_loss

def test_acc():
    pred = mx.nd.array([[0.3, 0.7], [0, 1.], [0.4, 0.6]])
    label = mx.nd.array([0, 1, 1])
    metric = mx.metric.create('acc')
    metric.update([label], [pred])
    _, acc = metric.get()
    expected_acc = (np.argmax(pred, axis=1) == label).sum().asscalar() / label.size
    assert acc == expected_acc

def test_f1():
    microF1 = mx.metric.create("f1", average="micro")
    macroF1 = mx.metric.F1(average="macro")

    assert np.isnan(macroF1.get()[1])
    assert np.isnan(microF1.get()[1])

    # check divide by zero
    pred = mx.nd.array([[0.9, 0.1],
                        [0.8, 0.2]])
    label = mx.nd.array([0, 0])
    macroF1.update([label], [pred])
    microF1.update([label], [pred])
    assert macroF1.get()[1] == 0.0
    assert microF1.get()[1] == 0.0
    macroF1.reset()
    microF1.reset()

    pred11 = mx.nd.array([[0.1, 0.9],
                          [0.5, 0.5]])
    label11 = mx.nd.array([1, 0])
    pred12 = mx.nd.array([[0.85, 0.15],
                          [1.0, 0.0]])
    label12 = mx.nd.array([1, 0])
    pred21 = mx.nd.array([[0.6, 0.4]])
    label21 = mx.nd.array([0])
    pred22 = mx.nd.array([[0.2, 0.8]])
    label22 = mx.nd.array([1])

    microF1.update([label11, label12], [pred11, pred12])
    macroF1.update([label11, label12], [pred11, pred12])
    assert microF1.num_inst == 4
    assert macroF1.num_inst == 1
    # f1 = 2 * tp / (2 * tp + fp + fn)
    fscore1 = 2. * (1) / (2 * 1 + 1 + 0)
    np.testing.assert_almost_equal(microF1.get()[1], fscore1)
    np.testing.assert_almost_equal(macroF1.get()[1], fscore1)

    microF1.update([label21, label22], [pred21, pred22])
    macroF1.update([label21, label22], [pred21, pred22])
    assert microF1.num_inst == 6
    assert macroF1.num_inst == 2
    fscore2 = 2. * (1) / (2 * 1 + 0 + 0)
    fscore_total = 2. * (1 + 1) / (2 * (1 + 1) + (1 + 0) + (0 + 0))
    np.testing.assert_almost_equal(microF1.get()[1], fscore_total)
    np.testing.assert_almost_equal(macroF1.get()[1], (fscore1 + fscore2) / 2.)

def test_perplexity():
    pred = mx.nd.array([[0.8, 0.2], [0.2, 0.8], [0, 1.]])
    label = mx.nd.array([0, 1, 1])
    p = pred.asnumpy()[np.arange(label.size), label.asnumpy().astype('int32')]
    perplexity_expected = np.exp(-np.log(p).sum()/label.size)
    metric = mx.metric.create('perplexity', -1)
    metric.update([label], [pred])
    _, perplexity = metric.get()
    assert perplexity == perplexity_expected

def test_pearsonr():
    pred = mx.nd.array([[0.7, 0.3], [0.1, 0.9], [1., 0]])
    label = mx.nd.array([[0, 1], [1, 0], [1, 0]])
    pearsonr_expected = np.corrcoef(pred.asnumpy().ravel(), label.asnumpy().ravel())[0, 1]
    metric = mx.metric.create('pearsonr')
    metric.update([label], [pred])
    _, pearsonr = metric.get()
    assert pearsonr == pearsonr_expected

def test_single_array_input():
    pred = mx.nd.array([[1,2,3,4]])
    label = pred + 0.1

    mse = mx.metric.create('mse')
    mse.update(label, pred)
    _, mse_res = mse.get()
    np.testing.assert_almost_equal(mse_res, 0.01)

    mae = mx.metric.create('mae')
    mae.update(label, pred)
    mae.get()
    _, mae_res = mae.get()
    np.testing.assert_almost_equal(mae_res, 0.1)

    rmse = mx.metric.create('rmse')
    rmse.update(label, pred)
    rmse.get()
    _, rmse_res = rmse.get()
    np.testing.assert_almost_equal(rmse_res, 0.1)

if __name__ == '__main__':
    import nose
    nose.runmodule()
