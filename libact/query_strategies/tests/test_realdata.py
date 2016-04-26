"""
This module uses real world dataset to test the active learning algorithms.
Since creating own artificial dataset for test is too time comsuming so we would
use real world data, fix the random seed, and compare the query sequence each
active learning algorithm produces.
"""
import random
import os
import unittest

from numpy.testing import assert_array_equal
import numpy as np

from libact.base.dataset import Dataset, import_libsvm_sparse
from libact.models import LogisticRegression
from libact.query_strategies import *


def run_qs(trn_ds, qs, truth, quota):
    ret = []
    for _ in range(quota):
        ask_id = qs.make_query()
        trn_ds.update(ask_id, truth[ask_id])

        ret.append(ask_id)
    return np.array(ret)


class RealdataTestCase(unittest.TestCase):

    def setUp(self):
        dataset_filepath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'datasets/heart_scale')
        self.X, self.y = import_libsvm_sparse(
            dataset_filepath).format_sklearn()
        self.quota = 10

    def test_quire(self):
        trn_ds = Dataset(self.X,
                         np.concatenate([self.y[:5], [None] * (len(self.y) - 5)]))
        qs = QUIRE(trn_ds)
        qseq = run_qs(trn_ds, qs, self.y, self.quota)
        assert_array_equal(
            qseq, np.array([117, 175, 256, 64, 103, 118, 180, 159, 129, 235]))

    def test_quire_mykernel(self):
        def my_kernel(X, Y):
            return np.dot(X, Y.T)
        np.random.seed(1126)
        trn_ds = Dataset(self.X,
                         np.concatenate([self.y[:5], [None] * (len(self.y) - 5)]))
        qs = QUIRE(trn_ds, kernel=my_kernel)
        qseq = run_qs(trn_ds, qs, self.y, self.quota)
        assert_array_equal(
            qseq, np.array([9, 227, 176, 110,  52, 117, 228, 205, 103, 175]))

    def test_RandomSampling(self):
        trn_ds = Dataset(self.X,
                         np.concatenate([self.y[:5], [None] * (len(self.y) - 5)]))
        qs = RandomSampling(trn_ds, random_state=1126)
        qseq = run_qs(trn_ds, qs, self.y, self.quota)
        assert_array_equal(
            qseq, np.array([150, 16, 122, 157, 233, 160, 114, 163, 155, 56]))

    def test_HintSVM(self):
        trn_ds = Dataset(self.X,
                         np.concatenate([self.y[:5], [None] * (len(self.y) - 5)]))
        qs = HintSVM(trn_ds, random_state=1126)
        qseq = run_qs(trn_ds, qs, self.y, self.quota)
        assert_array_equal(
            qseq, np.array([24, 235, 228, 209, 18, 143, 119, 90, 149, 207]))

    def test_QueryByCommittee(self):
        trn_ds = Dataset(self.X,
                         np.concatenate([self.y[:10], [None] * (len(self.y) - 10)]))
        qs = QueryByCommittee(trn_ds,
                              models=[LogisticRegression(C=1.0),
                                      LogisticRegression(C=0.01),
                                      LogisticRegression(C=100)],
                              random_state=1126)
        qseq = run_qs(trn_ds, qs, self.y, self.quota)
        assert_array_equal(
            qseq, np.array([267, 210, 229, 220, 134, 252, 222, 142, 245, 228]))

    def test_UcertaintySamplingLc(self):
        random.seed(1126)
        trn_ds = Dataset(self.X,
                         np.concatenate([self.y[:10], [None] * (len(self.y) - 10)]))
        qs = UncertaintySampling(trn_ds, method='lc',
                                 model=LogisticRegression())
        qseq = run_qs(trn_ds, qs, self.y, self.quota)
        assert_array_equal(
            qseq, np.array([145, 66, 82, 37, 194, 60, 191, 211, 245, 131]))

    def test_UcertaintySamplingSm(self):
        random.seed(1126)
        trn_ds = Dataset(self.X,
                         np.concatenate([self.y[:10], [None] * (len(self.y) - 10)]))
        qs = UncertaintySampling(trn_ds, method='sm',
                                 model=LogisticRegression())
        qseq = run_qs(trn_ds, qs, self.y, self.quota)
        assert_array_equal(
            qseq, np.array([145, 66, 82, 37, 194, 60, 191, 211, 245, 131]))

    def test_ActiveLearningByLearning(self):
        trn_ds = Dataset(self.X,
                         np.concatenate([self.y[:10], [None] * (len(self.y) - 10)]))
        qs = ActiveLearningByLearning(trn_ds, T=self.quota,
                                      query_strategies=[
                                          UncertaintySampling(
                                              trn_ds, model=LogisticRegression()),
                                          HintSVM(trn_ds, random_state=1126)],
                                      model=LogisticRegression(),
                                      random_state=1126
                                      )
        qseq = run_qs(trn_ds, qs, self.y, self.quota)
        assert_array_equal(
            qseq, np.array([173, 103, 133, 184, 187, 147, 251, 83, 93, 33]))


if __name__ == '__main__':
    unittest.main()
