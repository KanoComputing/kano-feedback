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


class WidgetPrompts:
    '''
    Implements a rotating list of Questions for the Desktop Widget.
    The questions come from Kano over a networked API.
    Questions which have been responded and sent are removed from the rotation.
    In case all questions have been responded, get_current_prompt
    will return None
    '''
    def __init__(self):
        # The default prompt is used in the unlikely event
        # there are no more questions to be answered
        self.kano_questions_api = 'http://api.kano.me/questions'
        self.cached_response_file = os.path.join(os.path.expanduser('~'),
                                                 '.feedback-widget-sent.csv')
        self.prompts = None
        self.current_prompt = None
        self.current_prompt_idx = -1

    def load_prompts(self):
        '''
        Try to get the questions from Kano Network
        '''
        if is_internet():
            if self._load_remote_prompts():
                self.current_prompt = self._get_next_prompt()

    def get_current_prompt(self):
        '''
        call this method to obtain the current question to display to the user
        '''
        return self.current_prompt

    def get_current_prompt_id(self):
        '''
        Returns the id of the current prompt
        '''
        return self.prompts[self.current_prompt_idx]['id']

    def mark_current_prompt_and_rotate(self):
        '''
        The current prompt has been responded,
        flag it accordingly so we do not use it again
        '''
        self._cache_mark_responded(self.current_prompt)

        # add the question to the tracker
        track_data("feedback_widget_response_sent", {"question": self.current_prompt,
                                                     "question_id": self.get_current_prompt_id()})

        # And moves to the next available one
        self.current_prompt = self._get_next_prompt()
        return self.current_prompt

    def _load_remote_prompts(self):
        '''
        Get the prompts/questions through a request
        '''
        try:
            # Contact Kano questions API
            questions = requests.get(self.kano_questions_api).text
            preloaded = json.loads(questions)
            prompts = sorted(preloaded['questions'], key=lambda k: k['date_created'])
            if len(prompts):
                self.prompts = prompts
                return True
            else:
                self.prompts = None
                return False
        except:
            return False

    def _get_next_prompt(self):
        '''
        Jump to the next available question that has not been answered yet
        '''
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

    def _cache_mark_responded(self, prompt, postpone=False):
        '''
        Will mark a question as being answered. If postpone is True
        A false will be set meaning it will be sent next time we are online
        '''
        try:
            # A cached CSV file to remember what has been responded
            with open(self.cached_response_file, 'ab') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
                writer.writerow([prompt, 'yes'])
            return True
        except:
            return False

    def _cache_is_prompt_responded(self, prompt):
        '''
        Find out if a question has been responded
        '''
        try:
            with open(self.cached_response_file) as csvfile:
                reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                for row in reader:
                    if prompt == row[0]:
                        # This question has already been answered,
                        # search for next one
                        return True
        except:
            return False
