"""
``revscoring train_test -h``
::

    Trains and tests a scorer model.  This utility expects to get a file of
    tab-separated feature values and labels from which to construct a model.

    Usage:
        train_test -h | --help
        train_test <scorer_model> <features> [<language>] [-p=<kv>]...
                   [--version=<vers>]
                   [--values-labels=<path>]
                   [--model-file=<path>]
                   [--label-type=<type>]

    Options:
        -h --help               Prints this documentation
        <scorer_model>          Classpath to an the MLScorerModel to construct
                                and train
        <features>              Classpath to an list of features to use when
                                constructing the model
        -p --parameter=<kv>     A key-value argument pair to use when
                                constructing the scorer_model.
        --version=<vers>        A version to associate with the model
        --values-labels=<path>  Path to a file containing feature values and
                                labels [default: <stdin>]
        --model-file=<math>     Path to write a model file to
                                [default: <stdout>]
        --label-type=<type>     Interprets the labels as the appropriate type
                                (int, float, str, bool) [default: str]
"""
import json
import pprint
import random
import sys

import docopt
from tabulate import tabulate

from .util import encode, import_from_path


def main(argv=None):
    args = docopt.docopt(__doc__, argv=argv)

    ScorerModel = import_from_path(args['<scorer_model>'])
    features = import_from_path(args['<features>'])
    if args['<language>'] is not None:
        language = import_from_path(args['<language>'])
    else:
        language = None

    version = args['--version']

    model_kwargs = {}
    for parameter in args['--parameter']:
        key, value = parameter.split("=")
        model_kwargs[key] = json.loads(value)

    scorer_model = ScorerModel(features, language=language, version=version,
                               **model_kwargs)

    if args['--values-labels'] == "<stdin>":
        values_labels_file = sys.stdin
    else:
        values_labels_file = open(args['--values-labels'], 'r')

    if args['--model-file'] == "<stdout>":
        model_file = sys.stdout.buffer
    else:
        model_file = open(args['--model-file'], 'wb')

    decode_label = DECODERS[args['--label-type']]

    feature_labels = read_value_labels(values_labels_file,
                                       scorer_model.features,
                                       decode_label)

    run(feature_labels, model_file, scorer_model)

DECODERS = {
    'int': lambda v: int(v),
    'float': lambda v: float(v),
    'str': lambda v: str(v),
    'bool': lambda v: v in ("True", "true", "1", "T", "y", "Y")
}

def read_value_labels(f, features, decode_label):
    for line in f:
        parts = line.strip().split("\t")
        values = parts[:-1]
        label = parts[-1]

        label = decode_label(label)

        feature_values = []
        for feature, value in zip(features, values):

            if feature.returns == bool:
                feature_values.append(value == "True")
            else:
                feature_values.append(feature.returns(value))

        yield feature_values, label

def run(feature_labels, model_file, scorer_model):

    feature_labels = list(feature_labels)
    random.shuffle(feature_labels)

    test_set_size = int(0.6*len(feature_labels))
    test_set = feature_labels[:test_set_size]
    train_set = feature_labels[test_set_size:]

    scorer_model.train(train_set)

    stats = scorer_model.test(test_set)

    possible = list(set(actual for _, actual in stats['table'].keys()))
    possible.sort()

    sys.stderr.write("Accuracy: {0}\n\n".format(stats['accuracy']))
    if 'auc' in stats['roc']:
        sys.stderr.write("ROC-AUC: {0}\n\n".format(stats['roc']['auc']))
    else:
        sys.stderr.write("ROC-AUC:\n")


        table_data = [[comparison_label, stats['roc'][comparison_label]['auc']]
                      for comparison_label in possible]
        sys.stderr.write(tabulate(table_data))
        sys.stderr.write("\n\n")


    table_data = []

    for actual in possible:
        table_data.append([actual] +
                          [stats['table'].get((predicted, actual), 0)
                           for predicted in possible])
    sys.stderr.write(tabulate(table_data, headers=possible))
    sys.stderr.write("\n\n")

    scorer_model.dump(model_file)
