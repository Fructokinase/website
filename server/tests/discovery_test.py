# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from dataclasses import dataclass
from dataclasses import field
from typing import Dict, List
from unittest.mock import patch

from services.discovery import configure_routes
from services.discovery import get_service_url

test_routes = {
    'stat-var-svc': ['/stat-var/*'],
    'node-svc': ['/node/*'],
    'stat-svc': ['/stat/*'],
    'stat-value-svc': ['/stat/value'],
    'stat-set-series-svc': ['/stat/set/series/*'],
    'default-svc': ['/*']
}


@dataclass
class TestCase:
    endpoint_name: str
    expected_url: str
    routes: Dict = field(default_factory=lambda: test_routes)


class TestRoute(unittest.TestCase):
    def test_routes(self):
        """Tests host discovery for apis."""
        test_cases = [
            TestCase(endpoint_name='query', expected_url='default-svc:/query'),
            TestCase(endpoint_name='get_property_labels',
                     expected_url='node-svc:/node/property-labels'),
            TestCase(endpoint_name='get_stats_all',
                     expected_url='stat-svc:/stat/all'),
            # Exact match. stat-value-svc takes precedence over stat-svc.
            TestCase(endpoint_name='get_stats_value',
                     expected_url='stat-value-svc:/stat/value'),
            TestCase(
                endpoint_name='get_stat_set_series_within_place',
                expected_url='stat-set-series-svc:/stat/set/series/within-place'
            ),
            TestCase(endpoint_name='get_related_places',
                     expected_url='node-svc:/node/related-locations')
        ]

        for test_case in test_cases:
            configure_routes(test_case.routes)
            got = get_service_url(test_case.endpoint_name)
            self.assertEqual(got, test_case.expected_url)
