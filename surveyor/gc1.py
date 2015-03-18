import os
import posixpath
import pandas as pd
import numpy as np
import yaml
import argparse
import formencode
from formencode import validators
from PySide import QtGui


class ValidVersion(validators.FancyValidator):
    messages = {
        'wrong_length': 'A version must be 1 character long.',
        'letters_only': 'Versions must use letters only (e.g., "A", "B", "C")'
    }

    def _convert_to_python(self, value, state):
        return value.strip().upper()

    def _validate_python(self, value, state):
        if len(value) != 1:
            raise validators.Invalid(
                                     self.message("wrong_length",
                                                  state), value, state)
        if not value.isalpha():
            raise validators.Invalid(
                                     self.message("letters_only",
                                                  state), value, state)


class ValidResponses(validators.FancyValidator):
    accept_iterator = True
    messages = {
        'wrong_type': 'Responses must be a valid dict',
        'toomany': 'Too many responses: There is a max of 12',
        'invalid_val': 'Valid values are: (0,1,2,3,4,5,6,7,8,9,"#", "*")'
    }

    def _convert_to_python(self, value, state):
        return value

    def _validate_python(self, value, state):
        phone_keys = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, '#', '*')
        if type(value) != dict:
            raise validators.Invalid(
                                     self.message("wrong_type",
                                                  state), value, state)
        if len(value) > 12:
            raise validators.Invalid(
                                     self.message("toomany",
                                                  state), value, state)
        for key, val in value.items():
            if val not in phone_keys:
                raise validators.Invalid(
                                         self.message("invalid_val",
                                                      state), value, state)


class ValidVariableName(validators.FancyValidator):
    import re
    min = 2
    max = 80
    alphanum_regex = re.compile(r'^\w+$')
    messages = {
        'empty': 'Name cannot be blank!',
        'too_few': 'Name must be at least %(min)i '
        'characters long',
        'too_many': 'Name must be not be over %(max)i '
        'characters long',
        'non_alphanum': 'Non-alphanumeric characters are invalid '
        r'e.g., $#@!., (underscores are OK, spaces are not)',
        'letter_start': 'The name must begin with a letter'
        }

    def _convert_to_python(self, value, state):
        # _convert_to_python gets run before _validate_python.
        return value.strip().lower()

    def _validate_python(self, value, state):
        if not value:
            raise validators.Invalid(
                                     self.message("empty",
                                                  state), value, state)
        if len(value) < self.min:
            raise validators.Invalid(
                                     self.message("too_few", state,
                                                  min=self.min), value, state)
        if len(value) > self.max:
            raise validators.Invalid(
                                     self.message("too_many", state,
                                                  max=self.max), value, state)
        non_alphanum = self.alphanum_regex.sub('', value)
        if non_alphanum:
            raise validators.Invalid(
                                     self.message("non_alphanum", state),
                                     value, state)
        if not value[0].isalpha():
            raise validators.Invalid(
                                     self.message("letter_start", state),
                                     value, state)


class ValidOnlyIf(formencode.Schema):
    question = formencode.Any(
        validators=[validators.Int(not_empty=True),
                    validators.String(not_empty=True)])
    equals = formencode.Any(
        validators=[validators.Int(not_empty=True),
                    validators.String(not_empty=True)])


class ValidQuestion(formencode.Schema):
    name = ValidVariableName(not_empty=True)
    order = validators.Int(min=1, max=50, not_empty=True)
    responses = formencode.All(validators=[
        validators.ConfirmType(type=dict, not_empty=True),
        ValidResponses(not_empty=True)]
    )
    onlyif = formencode.All(validators=[
        validators.ConfirmType(type=dict, if_missing=None, not_empty=True),
        ValidOnlyIf(if_missing=None)])
    version = ValidVersion(not_empty=True, if_missing=None)


class ValidConfig(formencode.Schema):
    # A config file must have only the two fields 'options' and 'questions'
    allow_extra_fields = False
    # 'options' must be a dict
    options = validators.ConfirmType(type=dict, not_empty=True)
    # 'questions' must be a list of valid questions
    questions = formencode.All(
        validators=[formencode.foreach.ForEach(ValidQuestion(not_empty=True)),
                    validators.ConfirmType(type=list, not_empty=True)])


def load_config(path):
    vc = ValidConfig()
    with open(path) as f:
        loaded_file = yaml.safe_load(f)
        config = vc.to_python(loaded_file)
    return(config)


def load_returns(returns_path):
    gc1_returns_regex = r'.*Day.*[.]txt$'
    gc1_date_regex = r'(\d{2}_\d{2}_\d{4})[.]txt'
    gc1_version_regex = r'version[-_.]*([A-Z])'
    gc1_columns = ['Account Number 1', 'Account Number 2',
                   'Charge', 'Contact Result', 'First Name',
                   'Last Name', 'Other 1', 'Other 2',
                   'Phone #'] + (['Q' + str(i) for i in range(21)][1:21])
    if not os.path.isdir(returns_path):
        raise Exception("You must include a valid directory")

    all_files = pd.Series(os.listdir(returns_path))
    # Filter out files using a regex to include only valid gc1 returns
    files = all_files[all_files.str.contains(gc1_returns_regex)]
    raw_dates = files.str.extract(gc1_date_regex)
    dates = ['-'.join([str(d)[-4:], str(d)[0:2], str(d)[3:5]])
             for d in raw_dates]
    versions = files.str.extract(gc1_version_regex)
    # Container for combined files
    raw = pd.DataFrame()
    for f, d, v in zip(files, dates, versions):
        print("Loading {}".format(f))
        df = pd.read_table(posixpath.join(returns_path, f),
                           dtype=np.unicode_)
        df['version'] = v
        df['date'] = d
        if not len(raw):
            raw = df
        else:
            raw = pd.concat([raw, df])
        # Create an actual time-stamp value
        ts = raw['date'] + ' ' + raw['Time']
        raw['timestamp'] = pd.to_datetime(ts,
                                          format="%Y-%m-%d %H:%M:%S %p")
        raw.reset_index(drop=True, inplace=True)
    return(raw)


def get_subquestion_index(m, mv, v_data):
    if m['onlyif']:
        if_q = 'Q' + m['onlyif']['question']
        _regex = r'^[' + m['onlyif']['equals'] + ']$'
        if_q = v_data[if_q].astype(str).str.replace(r'[.]0', '')
        ix = if_q[if_q.str.contains(_regex)].index
        if ix.isin(mv).any():
            raise Exception(("Duplicated mv indexes means that "
                            "Q{} subquestions were not mutually "
                             "exclusive.".format(m['order'])))
    else:
        ix = v_data.index
    return(ix)


def process_version(v_data, v_config, l_data, verbose, qs, pyside=True):
    valid_qs = list(set([q['order'] for q in v_config]))
    valid_qs.sort()
    for j in valid_qs:
        # extra row for pull script
        v_data.loc[:, 'blank'] = np.nan
        matches = [q for q in v_config if q['order'] == j]
        mv = pd.Index([])
        for m in matches:
            if pyside:
                QtGui.qApp.processEvents()
            if verbose:
                print('  ')
                print('------------------------------')
                print('  ')
                print("Q{} ".format(j), end="")
            if verbose and m['version']:
                print('version-{}'.format(m['version']), end='')
            if verbose and m['onlyif']:
                oif = m['onlyif']
                print(' (if Q{} == {})'.format(oif['question'],
                      oif['equals']))
            if verbose:
                print('{}'.format(m['name']))
            ix = get_subquestion_index(m, mv, v_data)
            mv = mv | ix
            # Find invalids
            _regex = ''.join([str(i) for i in m['responses'].values()])
            _regex = r'[^' + _regex + ']'
            if verbose:
                for nm, i in m['responses'].items():
                    print("{}=>{}".format(i, nm))
                print('regex={}'.format(_regex))
            q_data = v_data.loc[ix, 'Q{}'.format(j)].dropna()
            inv_ix = q_data[q_data.str.contains(_regex)].index
            while len(inv_ix):
                k = (j-1)
                if verbose:
                    print("({}) {} bad".format(
                        q_data.ix[inv_ix].dropna().str.cat(),
                        len(inv_ix)))
                while k < len(qs):
                    # eater function
                    v_data.ix[inv_ix, k] = v_data.ix[inv_ix, k+1]
                    k = k + 1
                q_data = v_data.loc[ix, 'Q{}'.format(j)].dropna()
                inv_ix = q_data[q_data.str.contains(_regex)].index
            for nm, i in m['responses'].items():
                lab_ix = q_data[q_data == str(i)].index
                l_data.loc[lab_ix, m['name']] = nm
        # PUSH
        na_ix = v_data['Q{}'.format(j)][v_data['Q{}'.format(j)].isnull()].index
        mv = mv | na_ix
        if j != 1:
            push_ix = v_data[~v_data.index.isin(mv)].index
            k = len(qs)
            if len(push_ix):
                if verbose:
                    print('!!!Push Question!!!'.format(j))
                while k > (j-1):
                    k_col = v_data.columns.values[k]
                    k_minus1 = v_data.columns.values[(k-1)]
                    v_data.loc[push_ix, k_col] = v_data.loc[push_ix, k_minus1]
                    k = k - 1
                    j_minus1 = v_data.columns.values[(j-1)]

                v_data.loc[push_ix, j_minus1] = np.nan
    return([v_data, l_data])


def call_performance_information(trans, labeled, ids, valid_qs):
    df = trans[ids].drop_duplicates(ids)
    out = {}
    # Total uniques attempted
    out['uniques'] = len(trans[ids[0]].unique())
    # Number of passes through list
    out['passes'] = trans[ids[0]].value_counts().max()
    # Total unique pickups
    out['pickups'] = len(trans[trans['Contact Result'] == 'answered']
                         [ids[0]].unique())
    answer_ids = trans[trans['Contact Result'] == 'answered'][ids[0]]
    df['pickup'] = np.where(df[ids[0]].isin(answer_ids), 1, 0)
    # Total uniques who passed verification
    out['verified'] = len(trans[trans.Q1 == '1'])
    # Remove requests
    out['removes'] = len(labeled['remove'].dropna())
    # Invalids
    inv = pd.crosstab(trans[ids[0]], trans['Contact Result'])
    mask = ((inv['answered'] == 0) & (inv['busy'] == 0) &
            (inv['fax'] == 0) & (inv['machine'] == 0) &
            (inv['noAnswer'] == 0) & (inv['invalid'] >= 1))
    out['invalids'] = len(inv[mask])
    invalid_ids = inv[mask].index
    df['invalid'] = np.where(df[ids[0]].isin(invalid_ids), 1, 0)
    # attempts
    attempts = trans[ids[0]].value_counts()
    attempts = pd.DataFrame({ids[0]: attempts.index,
                            'attempts': attempts})
    df = pd.merge(df, attempts, on=ids[0])
    # Invalids
    out['invalids'] = len(inv[mask])
    invalid_ids = inv[mask].index
    df['invalid'] = np.where(df[ids[0]].isin(invalid_ids), 1, 0)
    # Cost
    out['cost'] = trans.Charge.astype(np.float_).sum()
    trans['Charge']
    # Q completes
    out['completes'] = pd.Series([len(trans[q].dropna()) for q in valid_qs],
                                 index=valid_qs)
    # Cost per complete
    out['cost_per'] = pd.Series(out['cost'] /
                                [len(trans[q].dropna()) for q in valid_qs],
                                index=valid_qs)
    # Average Time
    out['mean_time'] = trans['Seconds'].astype(float).mean()
    out['sd_time'] = trans['Seconds'].astype(float).std()
    trans['Charge'] = trans['Charge'].astype(float)
    cost = trans[[ids[0], 'Charge']].groupby(ids[0]).sum()
    cost = pd.DataFrame({ids[0]: cost.index,
                        'cost': cost['Charge']})
    df = pd.merge(df, cost, on=ids[0])
    # Answers
    trans['answers'] = trans[valid_qs].count(axis=1)
    trans.sort(['answers'], ascending=False, inplace=True)
    answers = trans.drop_duplicates(ids)[ids+['answers']]
    df = pd.merge(df, answers, on=ids)
    # answers 2 (not exactly accurate, but good enough to sort)
    labeled['answers2'] = labeled.count(axis=1)
    labeled = labeled.sort_index(by='answers2', ascending=False)
    longest = labeled.drop_duplicates(ids)
    del longest['answers2']
    sfile = pd.merge(longest, df, on=ids)
    sfile.sort_index(by='timestamp', inplace=True)
    cols = pd.Series(ids + df.columns.tolist() + longest.columns.tolist())
    cols = cols.drop_duplicates().tolist()
    sfile = sfile[cols]
    return([sfile, out])


def macro(data, config, verbose=False):
    pd.options.mode.chained_assignment = None
    # Check to make sure no duplicated subquestions
    assert 'Account Number 1' in data
    assert 'Account Number 2' in data
    assert 'Charge' in data
    assert 'Contact Result' in data
    assert 'Phone #' in data
    assert 'Seconds' in data
    assert 'Time' in data
    opts = config['options']
    ids = []
    if 'id1' in opts:
        data[opts['id1']] = data['Account Number 1']
        ids.append(opts['id1'])
    if 'id2' in opts:
        data[opts['id2']] = data['Account Number 2']
        ids.append(opts['id2'])
    if 'id1' not in opts and 'id2' not in opts:
        data['id'] = data['Account Number 1']
        ids.append('id')
    # The yaml templates for each question
    q_template = config['questions']
    # Find all valid qs -- convert to set to find unique vals, and back to list
    valid_qs = list(set([q['order'] for q in q_template]))
    valid_qs.sort()
    valid_qs = ['Q' + str(q) for q in valid_qs]
    # Reduce to just response data
    resp_data = data.filter(regex=r'^Q\d+$')
    # Find valid questions
    cols = pd.Series(resp_data.columns.tolist()).str.replace('Q', '')
    cols = cols.astype(int)
    # Sort into ascending order (important)
    cols.sort()
    cols = ('Q' + cols.map(str)).tolist()
    # Re-order based on ascending order
    resp_data = resp_data[cols]
    # List of valid questions
    qs = resp_data.columns.tolist()
    # Prepare versions
    # if versions are all null, set them to '---'
    if 'version' not in data:
        data['version'] = '---'
    if np.all(data.version.isnull()):
        data['version'] = '---'
    # All unique versions
    versions = tuple(data.version.unique())
    # Storage containers for processed output
    raw_out, labeled_out = {}, {}
    # Base info that labels will be appended onto
    label_vars = ids + ['version']
    if 'flag1' in data:
        label_vars.append('flag1')
    if 'flag2' in data:
        label_vars.append('flag2')
    if 'timestamp' in data:
        label_vars.append('timestamp')
    elif 'Time' in data:
        data['time'] = data['Time']
        label_vars.append('time')
        if 'date' in data:
            label_vars.append('date')
    labels = data[label_vars].copy()
    # Run the macro once for each version
    for v in versions:
        if verbose:
            print("Version {}".format(v))
        # Raw response data
        v_data = resp_data[data.version == v]
        # Base label data
        l_data = labels[labels.version == v]
        v_config = [q for q in q_template
                    if q['version'] == v or not q['version']]
        raw_out[v], labeled_out[v] = process_version(v_data, v_config,
                                                     l_data, verbose, qs)
    # Combine the data sets
    raw, labeled = [], []
    for v in versions:
        if not len(raw):
            raw = raw_out[v]
            labeled = labeled_out[v]
        else:
            raw = pd.concat([raw, raw_out[v]])
            labeled = pd.concat([labeled, labeled_out[v]])
    # Transactional File; remove old data
    data = data.drop(qs, axis=1)
    trans = pd.merge(data, raw[valid_qs], left_index=True, right_index=True)
    if verbose:
        print("Removing duplicates:")
        print("Pre:  {}".format(len(trans)))
    trans.drop_duplicates(inplace=True)
    if verbose:
        print("Post: {}".format(len(trans)))
    # Call performance tracker
    sfile, cpt = call_performance_information(trans, labeled, ids, valid_qs)
    return([sfile, cpt])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process gc1 segment returns')
    parser.add_argument('-v', action='store_true', dest='verbose',
                        help='print verbose output to stdout', default=False)
    parser.add_argument('config_file', action='store',
                        help='path to config file')
    args = parser.parse_args()
    if args.verbose:
        print("Loading config file: {}".format(args.config_file))
    config = load_config(args.config_file)
    assert 'returns' in config['options']
    data = load_returns(config['options']['returns'])
    df, cpt = macro(data, config, args.verbose)
    assert 'save_as' in config['options']
    df.to_csv(config['options']['save_as'], index=False)
    if args.verbose:
        print("Saved at {}".format(config['options']['save_as']))
    if 'cpt' in config['options']:
        with open(config['options']['cpt'], "w") as text_file:
            text_file.write("{}".format(cpt))
    if args.verbose:
        print("Finished")
