#
# Copyright (C) 2020 GreenWaves Technologies, SAS, ETH Zurich and University of Bologna
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import gsystree as st

class Gdbserver(st.Component):

    def __init__(self, parent, name, enabled=False, port=12345, default_hartid=0):

        super(Gdbserver, self).__init__(parent, name)

        self.add_property('enabled', enabled)
        self.add_property('port', port)
        self.add_property('default_hartid', default_hartid)

        self.set_component('gdbserver.gdbserver')