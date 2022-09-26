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
"""Discovery module discoveres hosts based on API names."""

from dataclasses import dataclass
import itertools
from typing import Dict, List, TypeVar, Tuple


class InvalidEndpointException(Exception):
    pass


# By default, all endpoints are expected on localhost port 8081.
DEFAULT_INGRESS_RULES = dict({'http://127.0.0.1:8081': ['/*']})


@dataclass
class Endpoint:
    name: str  # Reference of the endpoint, use only within the server.
    path: str  # Path to a specific API defined by mixer.


class Endpoints:
    """Container for endpoint."""
    def __init__(self, endpoints: List[Endpoint]):
        self.endpoints = endpoints
        self.endpoint_name_to_path = {e.name: e.path for e in self.endpoints}
        self.endpoint_name_to_host = dict()  # unconfigured.

    def configure(self, ingress_rules: Dict[str, List[str]]):
        """Sets endpoint name to host mapping from ingress rules."""
        patterns = itertools.chain(*ingress_rules.values())
        if '/*' not in patterns:
            raise Exception('Invalid ingress rules,')

        # Find a matching host for each endpoint from ingress rules.
        for endpoint in self.endpoints:
            host = self.find_host(endpoint.path, ingress_rules)
            self.endpoint_name_to_host[endpoint.name] = host

    def find_host(self, path: str, ingress_rules: Dict[str, List[str]]) -> str:
        """Returns host with the pattern closest to a given path.

        For more on what is a pattern, see GCP doc.
        https://cloud.google.com/load-balancing/docs/url-map-concepts#wildcards-regx-dynamic
        """
        match_host, match_pattern = '', ''
        for host, patterns in ingress_rules.items():
            for pattern in patterns:
                # Pattern has wild card.
                if pattern.endswith('/*'):
                    pattern_prefix = pattern[:-len('/*')]
                    if not path.startswith(pattern_prefix):
                        continue
                    if len(pattern) > len(match_pattern):
                        match_pattern = pattern
                        match_host = host

                # Pattern does not have wild, card -> exact match.
                if not path.startswith(pattern):
                    continue
                if len(pattern) > len(match_pattern):
                    match_pattern = pattern
                    match_host = host

        return match_host

    def get_service_url(self, endpoint_name: str) -> str:
        """Returns a callable url for an endpoing.

        Caller is responsible for making sure that endpoint exists in config.
        """
        path = self.endpoint_name_to_path[endpoint_name]
        host = self.endpoint_name_to_host[endpoint_name]
        return f"{host}:{path}"


endpoints = Endpoints([
    Endpoint(name='query', path='/query'),
    Endpoint(name='translate', path='/translate'),
    Endpoint(name='search', path='/search'),
    Endpoint(name='get_property_labels', path='/node/property-labels'),
    Endpoint(name='get_property_values', path='/node/property-values'),
    Endpoint(name='get_places_in', path='/node/places-in'),
    Endpoint(name='get_place_ranking', path='/node/ranking-locations'),
    Endpoint(name='get_stat_set_series', path='/v1/stat/set/series'),
    Endpoint(name='get_stats_all', path='/stat/all'),
    Endpoint(name='get_stats_value', path='/stat/value'),
    Endpoint(name='get_stat_set_within_place', path='/stat/set/within-place'),
    Endpoint(name='v1_get_stat_set_within_place',
             path='/v1/stat/date/within-plac'),
    Endpoint(name='get_stat_set_within_place_all',
             path='/stat/set/within-place/all'),
    Endpoint(name='get_stat_set_series_within_place',
             path='/stat/set/series/within-place'),
    Endpoint(name='get_stat_set', path='/stat/set'),
    Endpoint(name='get_triples', path='/node/triples'),
    Endpoint(name='points_within', path='/v1/bulk/observations/point/linked'),
    Endpoint(name='series_within', path='/v1/bulk/observations/series/linked'),
    Endpoint(name='property_values', path='/v1/bulk/property/values'),
    Endpoint(name='get_related_places', path='/node/related-locations'),
    Endpoint(name='get_statvar_group', path='/stat-var/group'),
    Endpoint(name='get_statvar_path', path='/stat-var/path'),
    Endpoint(name='search_statvar', path='/stat-var/search'),
    Endpoint(name='match_statvar', path='/stat-var/match'),
    Endpoint(name='get_statvar_summary', path='/stat-var/summary'),
    Endpoint(name='version', path='/version')
])


def init(ingress_rules: Dict[str, List[str]]):
    """Must be caller at server startup, before server is considered ready."""
    endpoints.configure(ingress_rules)


def configure_routes(routes):
    endpoints.configure(routes)


def get_service_url(endpoint_name: str) -> str:
    """Returns the full url of a service.

    Args:
        endpoint_name: path of the API.
    Returns:
        Full service url.

    Examples:

    """
    if endpoint_name not in endpoints.endpoint_name_to_host:
        raise InvalidEndpointException("endpoint %s was not configured" %
                                       endpoint_name)
    return endpoints.get_service_url(endpoint_name)