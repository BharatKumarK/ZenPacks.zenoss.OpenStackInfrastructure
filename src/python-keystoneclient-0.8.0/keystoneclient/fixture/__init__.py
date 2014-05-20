# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
The generators in this directory produce keystone compliant tokens for use in
testing.

They should be considered part of the public API because they may be relied
upon to generate test tokens for other clients. However they should never be
imported into the main client (keystoneclient or other). Because of this there
may be dependencies from this module on libraries that are only available in
testing.
"""

from keystoneclient.fixture.exception import FixtureValidationError  # noqa
from keystoneclient.fixture.v2 import Token as V2Token  # noqa
<<<<<<< HEAD

__all__ = ['V2Token', 'FixtureValidationError']
=======
from keystoneclient.fixture.v3 import Token as V3Token  # noqa

__all__ = ['V2Token', 'V3Token', 'FixtureValidationError']
>>>>>>> 77d63f4a7a5aeaf331e82ab5c713c86b5ddbee15
