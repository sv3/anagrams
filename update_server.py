#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import git
from flask import request, abort
import hmac
import hashlib


def is_valid_signature(x_hub_signature, data, private_key):
    # x_hub_signature and data are from the webhook payload
    # private key is your webhook secret
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)            


def gitpullserver(w_secret):
    abort_code = 418
    # Do initial validations on required headers
    required_headers = ['X-Github-Event', 'X-Github-Delivery', 'X-Hub-Signature', 'User-Agent']
    if not all(reqd_header in request.headers for reqd_header in required_headers):
        abort(abort_code)
    if not request.is_json:
        abort(abort_code)
    ua = request.headers.get('User-Agent')
    if not ua.startswith('GitHub-Hookshot/'):
        abort(abort_code)

    event = request.headers.get('X-GitHub-Event')
    if event != "push":
        return json.dumps({'msg': "Wrong event type"})

    x_hub_signature = request.headers.get('X-Hub-Signature')
    # webhook content type should be application/json for request.data to have the payload
    # request.data is empty in case of x-www-form-urlencoded
    if not is_valid_signature(x_hub_signature, request.data, w_secret):
        print('Deploy signature failed: {sig}'.format(sig=x_hub_signature))
        abort(abort_code)

    payload = request.get_json()
    if payload is None:
        print('Deploy payload is empty: {payload}'.format(
            payload=payload))
        abort(abort_code)

    if payload['ref'] != 'refs/heads/master':
        return json.dumps({'msg': 'Not master; ignoring'})

    repo = git.Repo('.')

    if repo.active_branch.name != 'master':
        return json.dumps({'msg': 'Server not on master; ignoring'})

    origin = repo.remotes.origin
    pull_info = origin.pull()

    if len(pull_info) == 0:
        return json.dumps({'msg': "Didn't pull any information from remote!"})
    if pull_info[0].flags > 128:
        return json.dumps({'msg': "Didn't pull any information from remote!"})

    commit_hash = pull_info[0].commit.hexsha
    build_commit = 'build_commit = "{commit_hash}"'.format(commit_hash=commit_hash)
    print(str(build_commit))
    return 'Updated Anagrams server to commit {commit}'.format(commit=commit_hash)
