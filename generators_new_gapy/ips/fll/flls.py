#
# Copyright (C) 2020 GreenWaves Technologies
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

class Memory(st.Component):
    """
    Memory array

    Attributes
    ----------
    size : int
        The size of the memory.
    stim_file: str
        The path to a binary file which should be preloaded at beginning of the memory.
    
    """

    def __init__(self, parent, name, size: int, stim_file: str=None):

        super(Memory, self).__init__(parent, name)

        self.set_component('memory.memory_impl')

        self.add_properties({
            'size': size,
            'stim_file': stim_file
        })