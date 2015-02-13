#!/usr/bin/env python
# -*- coding: utf-8 -*-

# WidgetQuestions.py
#
# Copyright (C) 2015 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# Provides a rotating list of questions pulled from Kano
#

import os
import json
import csv
from kano.network import is_internet
from kano_profile.tracker import track_data

#
# TODO : This is fake test data, it should come from Kano networked API
#
fake_questions = '''
[
    {
        "priority": 98,
        "text": "Who are you?"
    },
    {
        "priority": 99,
        "text": "Where do you live"
    },
    {
        "priority": 100,
        "text": "How old are you?"
    }
]
'''


class WidgetPrompts:
    '''
    Implements a rotating list of Questions for the Desktop Widget.
    The questions come from Kano over a networked API.
    Questions which have been responded and sent are removed from the rotation.
    In case all questions have been responded, a default one will be presented
    '''
    def __init__(self):
        # The default prompt is used in the unlikely event there are no more questions to be answered
        self.default_prompt = 'What would you add to KanoOS?'
        self.prompts_file = '/usr/share/kano-feedback/media/widget/prompts.json'
        self.cached_response_file = os.path.join(os.path.expanduser('~'), '.feedback-widget-sent.csv')
        self.prompts = None
        self.current_prompt_idx = -1
        self.current_prompt = None

    def load_prompts(self):
        # Try to get the questions from Kano Network
        if is_internet() : self.prompts = self._load_remote_prompts()
        if not self.prompts:
            # Otherwise from a local file
            self.prompts = self._load_local_prompts()

        self.current_prompt = self._get_next_prompt()

    def get_current_prompt(self):
        # call this method to obtain the current question to display to the user
        return self.current_prompt

    def mark_current_prompt_and_rotate(self):
        # the current prompt has been responded, flag it accordingly so we do not use it again
        self._cache_mark_responded(self.current_prompt)

        # add the question to the tracker
        track_data("feedback-widget", {"question": self.current_prompt, "response": "y"})

        # And moves to the next available one
        self.current_prompt = self._get_next_prompt()
        return self.current_prompt

    def _load_remote_prompts(self):
        #
        # TODO: Call the Kano API that returns the real Feedback Questions list
        #
        try:
            preloaded = json.loads(fake_questions)
            prompts = sorted(preloaded, key=lambda k: k['priority'])
            return prompts
        except:
            raise
            return None

    def _load_local_prompts(self):
        try:
            with open(self.prompts_file, 'r') as f:
                prompts = json.loads(f.read())
                prompts = sorted(prompts, key=lambda k: k['priority'])
            return prompts
        except:
            return None

    def _get_next_prompt(self):
        # Jump to the next available question that has not been answered yet
        next_prompt = None
        iterations = 0
        try:
            while iterations < len(self.prompts):

                # Jump to the next prompt in the circular queue
                self.current_prompt_idx += 1
                if self.current_prompt_idx == len(self.prompts):
                    self.current_prompt_idx = 0

                next_prompt = self.prompts[self.current_prompt_idx]['text']

                # prompt has not been answered yet, take it!
                if not self._cache_is_prompt_responded(next_prompt):
                    return next_prompt

                iterations += 1

            # There are no more available questions, provide a default one
            next_prompt = self.default_prompt

        except:
            next_prompt = self.default_prompt

        return next_prompt

    def _cache_mark_responded(self, prompt):
        # A cached CSV file to remember what has been responded
        with open(self.cached_response_file, 'ab') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow([prompt])

    def _cache_is_prompt_responded(self, prompt):
        # Find out if a question has been responded
        with open(self.cached_response_file) as csvfile:
            reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            for row in reader:
                if prompt == row[0]:
                    # This question has already been answered, search for next one
                    return True

        return False
