from .models import SearchQuery
from .tasks import get_submission_by_id
from jf_reddit.settings import development as settings
from praw.models import MoreComments
from praw.models.comment_forest import CommentForest
from typing import List, Dict, Optional

import datetime
import json
import os
import praw
import queue
import random
import string
import time
import wget


def download_results(query: SearchQuery, form_data: Dict[str, list], sub_ids: List[str]):
    letters = string.ascii_lowercase
    tmp_dirname = ''.join(random.choice(letters) for i in range(10))
    tmp_path = os.path.join(settings.MEDIA_ROOT, tmp_dirname)

    if form_data.get('get_submission_data'):
        sub_fields = form_data.get('submission_field_options')
        generate_submissions_file(query, sub_ids, sub_fields, tmp_path)

    if form_data.get('get_comment_data'):
        com_fields = form_data.get('comment_field_options')
        com_sort = form_data.get('comment_sort_option')
        com_limit = form_data.get('comment_limit', None)
        generate_comments_files(sub_ids, com_fields, com_sort, com_limit, tmp_path)
    
    if form_data.get('get_external_data'):
        get_external_files(sub_ids, tmp_path)

    return tmp_dirname

def generate_submissions_file(query: SearchQuery, ids: List[str], field_opts: List[str], tmp_path: str):

    sort = query.praw_sort if query.praw_sort else query.psaw_sort
    json_data = {
        "search_query": {
            "terms": query.terms,
            "subreddit": query.subreddit,
            "syntax": query.syntax,
            "sort": sort,
            "time_filter": query.time_filter,
            "start_date": query.start_date if query.start_date else '',
            "end_date": query.end_date if query.end_date else ''
        },
        "submissions": []
    }
    for id_ in ids:
        sub = get_submission_by_id(id_)

        # Request submission data to get non-lazy submission.
        # This is necessary to access all submission fields.
        unlazify = sub.title

        all_fields = vars(sub)
        sub_info = {field:all_fields[field] for field in field_opts}
        
        # Convert UTC to date, complete the permalink, and replace deleted authors.
        if sub_info.get('created_utc', None):
            sub_info['created_utc'] = str(datetime.datetime.fromtimestamp(sub_info.get('created_utc')))
        if sub_info.get('permalink', None):
            sub_info['permalink'] = 'https://www.reddit.com' + sub_info.get('permalink')
        if sub_info.get('author', 'not found') is None:
            sub_info['author'] = '[Deleted]'

        json_data["submissions"].append(sub_info)
    
    fullpath = get_submissions_path(query, tmp_path)
    write_json(fullpath, json_data)

def generate_comments_files(ids: List[str], field_opts: List[str], sort: str, limit: Optional[int], tmp_path: str):
    for id_ in ids:
        sub = get_submission_by_id(id_)
        sub.comment_sort = sort

        # Set up initial data with basic submission info
        json_data = {
            "submission": {
                "title": sub.title,
                "subreddit": sub.subreddit,
                "permalink": 'https://www.reddit.com' + sub.permalink,
                "url": sub.url,
                "comment_sort": sort
            }
        }
        fullpath = get_comments_path(sub.title, limit, tmp_path)

        # If the user did not give a limit, get as many comments as possible
        gen_limit = limit if limit else 100000

        comment_dict = get_comments(sub.comments, field_opts, gen_limit, id_)
        json_data["comments"] = [comment_dict]
        write_json(fullpath, json_data)

def replace_more_comments(comments: CommentForest):
    """Replace PRAW's MoreComments objects with a list of comments as they are encountered."""
    for top_comment in comments:
        if isinstance(top_comment, MoreComments):
            yield from replace_more_comments(top_comment.comments())
        else:
            yield top_comment

def get_comments(comments: CommentForest, field_opts: List[str], limit: int, sub_id: str) -> Dict[str, dict]:
    """Get all comments/replies and format in a hierarchy."""

    count = 0
    all_comments_dict = {}
    comment_queue = queue.Queue()
    comment_queue.put(comments)

    while not comment_queue.empty():
        coms = comment_queue.get()
        for comment in replace_more_comments(coms):
            count += 1
            if comment.replies:
                comment_queue.put(comment.replies)
            c_id = comment.id

            # Remove leading t3_ or t1_ from parent id
            parent_id = comment.parent_id.split('_')[-1]

            all_fields = vars(comment)
            comment_info = {field:all_fields[field] for field in field_opts}

            # Replace deleted authors and convert UTC to date.
            if comment_info.get('author', 'not found') is None:
                comment_info['author'] = '[Deleted]'
            if comment_info.get('created_utc', None):
                comment_info['created_utc'] = str(datetime.datetime.fromtimestamp(comment_info.get('created_utc')))
        
            if parent_id == sub_id:
                comment_info['replies'] = []
                all_comments_dict[c_id] = comment_info
            elif parent_id in all_comments_dict.keys():
                comment_info['replies'] = []
                all_comments_dict[parent_id]['replies'].append({c_id: comment_info})
            else:
                for all_comment_infos in all_comments_dict.values():
                    for replies in all_comment_infos['replies']:
                        if parent_id in replies.keys():
                            replies[parent_id]['replies'].append({c_id: comment_info})
            if count >= limit:
                return all_comments_dict

    return all_comments_dict

def get_external_files(ids: List[str], tmp_path: str):
    """Download external data (images)."""
    for id_ in ids:
        sub = get_submission_by_id(id_)
        if not sub:
            continue

        ext_url = sub.url
        if ext_url.endswith(('png', 'jpg', 'jpeg', 'gif')):
            fullpath = get_external_path(ext_url, tmp_path)
            try:
                wget.download(ext_url, fullpath)
            except:
                continue

def get_submissions_path(query: SearchQuery, tmp_path: str) -> str:
    """Construct a file name from the SearchQuery object."""
    sort = query.praw_sort if query.praw_sort else query.psaw_sort
    if query.terms:
        term = "search-'"+ query.terms + "'"
        filename = '-'.join([query.subreddit, term, sort, str(query.limit)])
    else:
        filename = '-'.join([query.subreddit, sort, str(query.limit)])
    if query.time_filter:
        if query.time_filter == 'all':
            filename += '-all'
        else:
            filename += '-past-' + query.time_filter

    filename += '.json'
    filename = remove_illegal_chars(filename)
    dir_path = os.path.join(tmp_path, 'submissions')
    os.makedirs(dir_path, exist_ok=True)
    
    fullpath = os.path.join(dir_path, filename)
    return fullpath

def get_comments_path(title: str, limit: Optional[int], tmp_path: str) -> str:
    dir_path = os.path.join(tmp_path, 'comments')
    os.makedirs(dir_path, exist_ok=True)
    filename = title[:40]
    if limit:
        filename += '-' + str(limit)
    else: 
        filename += '-all'
    filename += '.json'
    filename = remove_illegal_chars(filename)
    fullpath = os.path.join(dir_path, filename)
    return fullpath

def get_external_path(external_url: str, tmp_path: str) -> str:
    filename = external_url.split('/')[-1]
    filename = remove_illegal_chars(filename)
    dirpath = os.path.join(tmp_path, 'images')
    os.makedirs(dirpath, exist_ok=True)
    fullpath = os.path.join(dirpath, filename)
    return fullpath

def remove_illegal_chars(filename: str) -> str:
    illegal_chars = [char for char in '!@#$%&*?:|=+~`}{][><\\/"']
    legal_name = ['_' if char in illegal_chars else char for char in filename]
    return "".join(legal_name)

def write_json(fullpath: str, data: Dict[str, list]):
    with open(fullpath, 'w') as f:
            json.dump(data, f, default=str, indent=4)
