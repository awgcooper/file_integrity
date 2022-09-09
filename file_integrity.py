#!/usr/bin/python3
# https://codereview.stackexchange.com/questions/147056/short-script-to-hash-files-in-a-directory


"""
for external dependencies run: 'pip install dill xxhash'
"""
import dill
import os.path
import xxhash
from datetime import date, datetime, timedelta
from pathlib import Path


#############################################
## description of functions and dictionaries
#############################################
"""
1. today()
- for today's files - { path-filename: [ hash, file_mtime]}
2. yesterday()
- loads results of yesterday's dictionary which has been saved to .dill file
3. newfiles, deletedfiles = files_add_del(today(), yesterday())
- convert the keys (filenames) of today's and yesterday's dicts into sets, 'today' and 'yesterday'
- then:
      newfiles = today - yesterday
      deletedfiles = yesterday - today
4. newfiles_reduced, deletedfiles_reduced = modify_dicts(newfiles, deletedfiles, yesterday())
- newfiles_reduced - iterates over files in 'newfiles' set and calculates hash
- deletedfiles_reduced - iterates over files in 'deletedfiles' set and looks up hash in 'yesterday'
- for both of these new dictionaries, key-value order is reversed from previous dictionaries to: { hash: path-filename}
5. etc
6. etc
"""

ROOT = 'D:/files'
def today():
    root_path = ROOT
    p = Path(root_path).glob('**/*')
    file_list = [ x for x in p if x.is_file() ]
    filelist_dict = dict.fromkeys(file_list)
    for filename in filelist_dict:
        hash_fn = xxhash.xxh3_128()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_fn.update(chunk)
        mod_time = datetime.fromtimestamp(os.path.getmtime(filename))
        filelist_dict.update({filename: [hash_fn.hexdigest(), mod_time]})
    return filelist_dict


# save today's dictionary to file
def save_today():
    today_dict = today()
    file_today = filebase + today_date + '.dill'
    with open(file_today, 'wb') as f:
        dill.dump(today_dict, f)


# load file from yesterday back into dictionary
def yesterday():
    file_yesterday = filebase + yesterday_date + '.dill'
    with open(file_yesterday, 'rb') as f:
        filelist_yesterday_dict = dill.load(f)
    return filelist_yesterday_dict


# compare two dictionaries looking for corrupt files
# defined as same name, same mtime, different hash
# results printed to text file
def corrupt_files(today_dict, yesterday_dict):
    corrupt = []
    for d1key, d1val in today_dict.items():
        d2val = (yesterday_dict.get(d1key))
        if d2val is None:
            pass
        elif d1val[0] != d2val[0] and d1val[1] == d2val[1]:
            corrupt.append([str(d1key), ['today', [str(d1val[0]),
                                                   str(d1val[1])]], ['yesterday', [str(d2val[0]), str(d2val[1])]]])
    return corrupt


def files_add_del(today_dict, yesterday_dict):
    today_dict_filenames = set(today_dict.keys())
    yesterday_dict_filenames = set(yesterday_dict.keys())
    newfiles_set = today_dict_filenames - yesterday_dict_filenames
    deletedfiles_set = yesterday_dict_filenames - today_dict_filenames
    return newfiles_set, deletedfiles_set


def modify_dicts(new_set, deleted_set, yesterday_dict):
    new_reduced = {}
    for key_filename in new_set:
        hash_fn = xxhash.xxh3_128()
        with open(key_filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_fn.update(chunk)
        new_reduced.update({key_filename: hash_fn.hexdigest()})
    new_reduced_reversed = dict((v,k) for k,v in new_reduced.items())

    deleted_reduced = {}
    for key_filename in deleted_set:
         deleted_reduced.update({key_filename: yesterday_dict[key_filename][0]})
    deleted_reduced_reversed = dict((v,k) for k,v in deleted_reduced.items())
    return new_reduced_reversed, deleted_reduced_reversed


def find_moved(new_reduced, deleted_reduced):
    moved_names_dict = {}
    moved_names_list = []
    moved_deleted_names_list = []
    for key in new_reduced:
        if key in deleted_reduced and deleted_reduced[key] == new_reduced[key]:
            pass
        elif key in deleted_reduced and deleted_reduced[key] != new_reduced[key]:
            moved_names_list.append(new_reduced[key])
            moved_deleted_names_list.append(deleted_reduced[key])
            moved_names_dict.update({deleted_reduced[key]: new_reduced[key]})
    moved_names = set(moved_names_list)
    moved_deleted_names = set(moved_deleted_names_list)
    netnewfiles = set(newfiles_reduced.values())
    netdeletedfiles = set(deletedfiles_reduced.values())
    new_excl_moved = netnewfiles - moved_names
    deleted_excl_moved = netdeletedfiles - moved_deleted_names
    return moved_names_dict, new_excl_moved, deleted_excl_moved


def write_report_heading(text_file):
    with open(text_file, 'w') as f:
        a = '{}{}\n{}{}\n{}'.format('Date: ', date.today().strftime("%Y-%m-%d"), 'Root Path: ', ROOT.replace("/", "\\"), 'Hash Function: XXH3(128)')
        f.write(a)
def write_to_file(text_file, heading, file_delta):
    fmt_filepath = lambda x, y: x.format(str(y).replace(str(y.anchor), ''))
    if heading == '-- CORRUPT FILES --':
        with open(text_file, 'a') as f:
            f.write('\n\n\n' + heading + '\n')
        with open(text_file, 'a') as f:
            if not file_delta:
                a = '{{ NONE }}'
                f.write(a + '\n')
            else:
                for entry in file_delta:
                    f.write(str(entry) + '\n')
    elif heading == '-- NEW FILES --' or heading == '-- DELETED FILES --':
        with open(text_file, 'a') as f:
            f.write('\n\n' + heading + '\n')
        with open(text_file, 'a') as f:
            for j in sorted(file_delta):
                a = fmt_filepath('{0}\n', j)
                f.write(a)
    elif heading == '-- MOVED FILES --':
        with open(text_file, 'a') as f:
            f.write('\n\n' + heading + '\n')
        with open(text_file, 'a') as f:
            for key, value in sorted(file_delta.items()):
                k = fmt_filepath('{0}', key)
                v = fmt_filepath('{0}', value)
                f.write('%s\t==>\t%s\n' % (k, v))


def del_files(dir, num_days):
    past_time = date.today() - timedelta(days=num_days)
    for path in Path(dir).iterdir():
        timestamp = date.fromtimestamp(path.stat().st_mtime)
        if path.is_file() and past_time > timestamp:
            path.unlink()


#################
## filenames
#################
fmt_date = lambda x: x.strftime("%Y-%m-%d")
today_date = fmt_date(date.today())
yesterday_date = fmt_date(date.today() - timedelta(days=1))
filebase = 'D:/dill/hashes_'
report = 'D:/dill/report_' + today_date + '.txt'

#################
## run functions
#################
save_today()
corrupt = corrupt_files(today(), yesterday())
newfiles, deletedfiles = files_add_del(today(), yesterday())
newfiles_reduced, deletedfiles_reduced = modify_dicts(newfiles, deletedfiles, yesterday())
moved_names_dict, new_excl_moved, deleted_excl_moved = find_moved(newfiles_reduced, deletedfiles_reduced)
write_report_heading(report)
write_to_file(report, '-- CORRUPT FILES --', corrupt)
write_to_file(report, '-- NEW FILES --', new_excl_moved)
write_to_file(report, '-- DELETED FILES --', deleted_excl_moved)
write_to_file(report, '-- MOVED FILES --', moved_names_dict)
del_files('D:/dill', 20)
