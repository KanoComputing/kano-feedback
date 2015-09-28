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
import time
from kano.network import is_internet
from kano_profile.tracker import track_data
from kano.logging import logger


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
        self.cache_file = os.path.join(os.path.expanduser('~'),
                                       '.feedback-widget-sent.csv')

        self.prompts = None
        self.current_prompt = None
        self.current_prompt_idx = -1

    def load_prompts(self):
        '''
        Try to get the questions from Kano Network
        '''
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

    def get_current_prompt_type(self):
        '''
        Returns the type of the prompt
        '''
        if 'type' in self.prompts[self.current_prompt_idx]:
            return self.prompts[self.current_prompt_idx]['type']
        else:
            return "textInput"

    def get_current_choices(self):
        '''
        If there are slider options, return them.
        '''
        if 'choices' in self.prompts[self.current_prompt_idx]:
            return self.prompts[self.current_prompt_idx]['choices']

    def get_checkbox_max_selected(self):
        if 'max_selected' in self.prompts[self.current_prompt_idx]:
            return self.prompts[self.current_prompt_idx]['max_selected']

    def get_checkbox_min_selected(self):
        if 'min_selected' in self.prompts[self.current_prompt_idx]:
            return self.prompts[self.current_prompt_idx]['min_selected']

    def get_slider_start_value(self):
        if 'start' in self.prompts[self.current_prompt_idx]:
            return self.prompts[self.current_prompt_idx]['start']

    def get_slider_end_value(self):
        if 'end' in self.prompts[self.current_prompt_idx]:
            return self.prompts[self.current_prompt_idx]['end']

    def mark_prompt(self, prompt, answer, qid, offline=False, rotate=False):
        '''
        This function is used to cover these 3 use cases:

        1. question has been answered and sent now
        2. question is answered and saved offline
        3. offline answer has been sent and marked as "sent"

        See get_offline_answers for details on how to send offline answers when back online
        '''

        self._cache_mark_responded(prompt, answer, qid, offline)

        # If the question has been answered and sent to us, add it to the tracker
        if not offline:
            track_data("feedback_widget_response_sent", {"question": prompt,
                                                         "question_id": qid})

        # And we jump to the next available question
        if rotate:
            self.current_prompt = self._get_next_prompt()

        return self.current_prompt

    def get_offline_answers(self):
        '''
        This function will return a list of all offline answers
        Each answer contains in this order: The original question, the answer, the question ID.

           for offline in get_offline_answers():
              prompt=offline[0]
              answer=offline[1]
              qid=offline[2]
        '''
        return self._cache_get_all(offline=True)

    def _load_remote_prompts(self, num_retries=10):
        '''
        Get the prompts/questions through a request,
        retrying <num_retries> if network is not up.
        '''
        for retry in range(0, num_retries):
            try:
                if is_internet():
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
            except Exception as e:
                logger.debug("Exception in _load_remote_prompts: {}".format(str(e)))

            time.sleep(2)

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
        except Exception as e:
            logger.debug("Exception in _get_next_prompt: {}".format(str(e)))

        return next_prompt

    def _cache_mark_responded(self, prompt, answer, qid, offline=False):
        '''
        Will mark a question as being answered and sent, or marked offline.
        If offline is True, it will be saved along with the answer and question ID,
        to be sent at a later stage.
        '''

        found = False
        if not offline:
            # answers that have been sent are marked without answer or question ID
            answer = 'yes'
            qid = None

        # Replace the cached response if it's offline
        cached = self._cache_get_all()
        for row in cached:
            if row[0] == prompt:
                row[1] = answer
                row[2] = qid
                found = True

        if not found:
            # Or add it if it's not saved
            cached.append([prompt, answer, qid])

        cached = self._cache_save_all(cached)

    def _cache_is_prompt_responded(self, prompt):
        '''
        Find out if a question has been responded
        '''
        cached = self._cache_get_all()
        for row in cached:
            if row[0] == prompt:
                return True

        return False

    def _cache_get_all(self, offline=False):
        '''
        Loads the complete cache of prompts and answers, answered and postponed
        '''
        cached_prompts = []
        try:
            with open(self.cache_file) as csvfile:
                reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                for row in reader:
                    if row[0]: row[0] = row[0].decode('utf-8')
                    if row[1]: row[1] = row[1].decode('utf-8')
                    if row[2]: row[2] = row[2].decode('utf-8')

                    if offline:
                        if row[1] != 'yes':
                            # this is an offline answer
                            cached_prompts.append([row[0], row[1], row[2]])
                    else:
                        cached_prompts.append([row[0], row[1], row[2]])
        except Exception as e:
            logger.debug("Exception in _cache_get_all: {}".format(str(e)))

        return cached_prompts

    def _cache_save_all(self, rows):
        '''
        Saves the cache back to disk.
        '''
        try:
            with open(self.cache_file, 'w') as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                for row in rows:
                    if row[0]: row[0] = row[0].encode('utf-8')
                    if row[1]: row[1] = row[1].encode('utf-8')
                    if row[2]: row[2] = row[2].encode('utf-8')
                    writer.writerow([row[0], row[1], row[2]])
        except Exception as e:
            logger.debug("Exception in _cache_save_all: {}".format(str(e)))
            return False

        return True
