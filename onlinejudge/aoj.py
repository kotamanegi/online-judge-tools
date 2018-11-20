# Python Version: 3.x
# -*- coding: utf-8 -*-
import onlinejudge.service
import onlinejudge.problem
from onlinejudge.problem import LabeledString, TestCase
import onlinejudge.dispatch
import onlinejudge.implementation.utils as utils
import onlinejudge.implementation.logging as log
import io
import posixpath
import json
import requests
import urllib.parse
import zipfile
import collections
import itertools
from typing import *


@utils.singleton
class AOJService(onlinejudge.service.Service):

    def get_url(self):
        return 'http://judge.u-aizu.ac.jp/onlinejudge/'

    def get_name(self):
        return 'aoj'

    @classmethod
    def from_url(cls, s: str) -> Optional['AOJService']:
        # example: http://judge.u-aizu.ac.jp/onlinejudge/
        result = urllib.parse.urlparse(s)
        if result.scheme in ('', 'http', 'https') \
                and result.netloc == 'judge.u-aizu.ac.jp':
            return cls()
        return None


class AOJProblem(onlinejudge.problem.Problem):
    def __init__(self, problem_id):
        self.problem_id = problem_id

    def download(self, session: Optional[requests.Session] = None, is_system: bool = False) -> List[TestCase]:
        if is_system:
            return self.download_system(session=session)
        else:
            return self.download_samples(session=session)

    def download_samples(self, session: Optional[requests.Session] = None) -> List[TestCase]:
        session = session or utils.new_default_session()
        # get samples via the official API
        # reference: http://developers.u-aizu.ac.jp/api?key=judgedat%2Ftestcases%2Fsamples%2F%7BproblemId%7D_GET
        url = 'https://judgedat.u-aizu.ac.jp/testcases/samples/{}'.format(self.problem_id)
        resp = utils.request('GET', url, session=session)
        samples: List[TestCase] = []
        for sample in json.loads(resp.content):
            samples += [ TestCase(
                LabeledString(str(sample['serial']), sample['in']),
                LabeledString(str(sample['serial']), sample['out']),
                ) ]
        return samples

    def download_system(self, session: Optional[requests.Session] = None) -> List[TestCase]:
        session = session or utils.new_default_session()
        get_url = lambda case, type: 'https://judgedat.u-aizu.ac.jp/testcases/{}/{}/{}'.format(self.problem_id, case, type)
        testcases: List[TestCase] = []
        for case in itertools.count(1):
            # input
            resp = utils.request('GET', get_url(case, 'in'), session=session)
            in_txt = resp.text
            if in_txt.strip() == '/* This is a single file for multiple testcases. serial should be 1. */':
                break
            if in_txt.strip() == '/* Test case #{} for problem {} is not available. */'.format(case, self.problem_id):
                break
            # output
            resp = utils.request('GET', get_url(case, 'out'), session=session)
            out_txt = resp.text
            assert out_txt.strip() != '/* This is a single file for multiple testcases. serial should be 1. */'
            testcases += [ TestCase(
                LabeledString('in%d.txt' % case, in_txt),
                LabeledString('out%d.txt' % case, out_txt),
                ) ]
        return testcases

    def get_url(self) -> str:
        return 'http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id={}'.format(self.problem_id)

    @classmethod
    def from_url(cls, s: str) -> Optional['AOJProblem']:
        # example: http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=1169
        # example: http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=DSL_1_A&lang=jp
        result = urllib.parse.urlparse(s)
        querystring = urllib.parse.parse_qs(result.query)
        if result.scheme in ('', 'http', 'https') \
                and result.netloc == 'judge.u-aizu.ac.jp' \
                and utils.normpath(result.path) == '/onlinejudge/description.jsp' \
                and querystring.get('id') \
                and len(querystring['id']) == 1:
            n, = querystring['id']
            return cls(n)
        return None

    def get_service(self) -> AOJService:
        return AOJService()


onlinejudge.dispatch.services += [ AOJService ]
onlinejudge.dispatch.problems += [ AOJProblem ]
