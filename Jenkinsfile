#!/usr/bin/env groovy

@Library('kanolib')
import build_deb_pkg
import python_test_env


def repo_name = 'kano-feedback'


stage ('Test') {
    def dep_repos = [
        "kano-toolset",
        "kano-i18n",
        "kano-profile",
    ]
	python_test_env(dep_repos) { python_path_var ->
    }
}


stage ('Build') {
    autobuild_repo_pkg "$repo_name"
}

stage ('Docs') {
    build_docs "$repo_name"
}
