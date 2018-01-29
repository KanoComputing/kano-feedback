#!/usr/bin/env groovy

@Library('kanolib')
import build_deb_pkg


def repo_name = 'kano-feedback'


stage ('Build') {
    autobuild_repo_pkg "$repo_name"
}

stage ('Docs') {
    build_docs "$repo_name"
}
