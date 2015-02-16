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
import requests
from kano.network import is_internet
from kano_profile.tracker import track_data

#
# TODO: Below are sample responses to test the Kano Questions API
#
test_questions = '''
{  
    "questions": [
        {  
            "id": "54de0072f448cb0800041190",
            "text": "Test question one.",
            "date_created": "2015-02-13T13:47:30.045Z"
        },
        {  
            "id": "54de0072f448cb0800041191",
            "text": "Test question two.",
            "date_created": "2015-01-13T13:47:30.045Z"
        },
        {  
            "id": "54de0072f448cb0800041192",
            "text": "Test question three.",
            "date_created": "2015-03-13T13:47:30.045Z"
        }
    ]
}
'''

test_empty_questions = '''
{"questions":[]}
'''



class WidgetPrompts:
    '''
    Implements a rotating list of Questions for the Desktop Widget.
    The questions come from Kano over a networked API.
    Questions which have been responded and sent are removed from the rotation.
    In case all questions have been responded, get_current_prompt will return None
    '''
    def __init__(self):
        # The default prompt is used in the unlikely event there are no more questions to be answered
        self.kano_questions_api='http://api.kano.me/questions'
        self.cached_response_file = os.path.join(os.path.expanduser('~'), '.feedback-widget-sent.csv')
        self.prompts = None
        self.current_prompt = None
        self.current_prompt_idx = -1

    def load_prompts(self, test=False):
        # Try to get the questions from Kano Network
        if is_internet():
            if self._load_remote_prompts(test=test):
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

    def _load_remote_prompts(self, test=False):
        try:
            # TODO: Remove test mode when API is confirmed to work
            if test:
                #questions=test_empty_questions
                questions=test_questions
            else:
                questions=requests.get(self.kano_questions_api).text

            preloaded=json.loads(questions)
            prompts = sorted(preloaded['questions'], key=lambda k: k['date_created'])
            if len(prompts):
                self.prompts=prompts
                return True
            else:
                self.prompts=None
                return False
        except:
            return False

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

            # No more questions to answer
            next_prompt = None
        except:
            pass

        return next_prompt

    def _cache_mark_responded(self, prompt):
        try:
            # A cached CSV file to remember what has been responded
            with open(self.cached_response_file, 'ab') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
                writer.writerow([prompt])
            return True
        except:
            return False

    def _cache_is_prompt_responded(self, prompt):
        try:
            # Find out if a question has been responded
            with open(self.cached_response_file) as csvfile:
                reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                for row in reader:
                    if prompt == row[0]:
                        # This question has already been answered, search for next one
                        return True
        except:
            return False
