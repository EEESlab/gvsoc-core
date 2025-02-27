#
# Copyright (C) 2020 GreenWaves Technologies, SAS, ETH Zurich and
#                    University of Bologna
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

#
# Authors: Germain Haugou, GreenWaves Technologies (germain.haugou@greenwaves-technologies.com)
#

from cpu.iss.isa_gen.isa_gen import *
import argparse
import os.path
import importlib
import hashlib
import filecmp
import shutil


iss_config_file = None


class R5(Instr):
    def __init__(self, label, format, encoding, decode=None, N=None, L=None, mapTo=None, group=None, fast_handler=False,
        tags=[], isa_tags=[], is_macro_op=False):

        # Encodings for non-compressed instruction sets
              #   3 3 2 2 2 2 2       2 2 2 2 2       1 1 1 1 1       1 1 1       1 1
              #   1 0 9 8 7 6 5       4 3 2 1 0       9 8 7 6 5       4 3 2       1 0 9 8 7       6 5 4 3 2 1 0
              #   X X X X X X X   |   X X X X X   |   X X X X X   |   X X X   |   X X X X X   |   X X X X X X X
        # R   #         f7        |      rs2      |      rs1      |     f3    |       rd      |      opcode
        # RF  #         f7        |      rs2      |      rs1      |  ui[2:0]  |       rd      |      opcode
        # RF4 #         f7        |      rs2      |      rs1      |  ui[2:0]  |     rd/rs3    |      opcode
        # R2F #                  f7               |      rs1      |  ui[2:0]  |       rd      |      opcode
        # R3F #                  f7               |      rs1      |     f3    |       rd      |      opcode
        # R4U #    rs3     |  f2  |      rs2      |      rs1      |  ui[2:0]  |       rd      |      opcode
        # RVF #         f7        |      rs2      |      rs1      |     f3    |       rd      |      opcode
        # RVF2#                  f7               |      rs1      |     f3    |       rd      |      opcode
        # RVF4#         f7        |      rs2      |      rs1      |     f3    |     rd/rs3    |      opcode
        # RRRR#         f7        |      rs2      |      rs1      |     f3    |     rd/rs3    |      opcode
        # RRRS#      f6      |     si[0|5:1]      |      rs2      |     f3    |     rd/rs1    |      opcode
        # RRRU#      f6      |     ui[0|5:1]      |      rs2      |     f3    |     rd/rs1    |      opcode
        #RRRU2#   f2 |   ui[4:0]  |      rs2      |      rs1      |     f3    |       rd      |      opcode
        #RRRRU#   f2 |   ui[4:0]  |      rs2      |      rs1      |     f3    |     rd/rs3    |      opcode
        # R1  #         f7        |       -       |      rs1      |     f3    |       rd      |      opcode
        # RRU #      f6      |     ui[0|5:1]      |      rs1      |     f3    |       rd      |      opcode
        # RRS #      f6      |     si[0|5:1]      |      rs1      |     f3    |       rd      |      opcode
        # RRU2#     f3 |ui[7:6]|f1|ui[0|5:1]      |      rs1      |     f3    |       rd      |      opcode
        # LR  #         f7        |      rs2      |      rs1      |     f3    |       rd      |      opcode        # Indirect addressing mode
        # RR  #   f2 |     rs3    |      rs2      |      rs1      |     f3    |       rd      |      opcode
        # SR  #   f2 |     rs3    |      rs2      |      rs1      |     f3    |       rd      |      opcode        # Indirect addressing mode
        # I   #              si[11:0]             |      rs1      |     f3    |       rd      |      opcode
        # L   #              si[11:0]             |      rs1      |     f3    |       rd      |      opcode        # Indirect addressing mode
        # IU  #              ui[11:0]             |      rs1      |     f3    |       rd      |      opcode
        # I1U #         f7        |    ui[4:0]    |      rs1      |     f3    |       rd      |      opcode
        # I2U #             ui0[11:0]             |   ui1[4:0]    |     f3    |       rd      |      opcode
        # I3U #    f4    |          ui[7:0]       |                    f13                    |      opcode
        # I4U #   f2 | ui0[4:0]   |   ui1[4:0]    |      rs1      |     f3    |       rd      |      opcode
        # I5U #   f2 | ui0[4:0]   |   ui1[4:0]    |      rs1      |     f3    |     rs2/rd    |      opcode
        # IOU #                  f12              |   ui0[4:0]    |     f3    |       f5      |      opcode
        # S   #       si[11:5]    |      rs2      |      rs1      |     f3    |     si[4:0]   |      opcode        # Indirect addressing mode
        # S1  #   f2 |     rs3    |      rs2      |      rs1      |     f3    |       f5      |      opcode
        # SB  #     si[12|10:5]   |      rs2      |      rs1      |     f3    |   si[4:1|11]  |      opcode
        # SB2 #     si[12|10:5]   |    si[4:0]    |      rs1      |     f3    |   si[4:1|11]  |      opcode
        # U   #                           ui[31:12]                           |       rd      |      opcode
        # UJ  #                    si[20|10:1|11|19:15|14:12]                 |       rd      |      opcode
        # HL0 #              ui1[11:0]            |      rs1      |     f3    |  opcode  |ui0[0]|      opcode
        # HL1 #              ui1[11:0]            |    ui2[4:0]   |     f3    |  opcode  |ui0[0]|      opcode
        # Z   #                 -                 |       -       |     f3    |        -      |      opcode

        self.args = []

        if format == 'R':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(15, 5)),
                            InReg (1, Range(20, 5)),
                            ]


        # int64 formats
        elif format == 'R1x64_W64':
            self.args = [   OutReg64 (0, Range(7,  5)),
                            InReg64  (0, Range(15, 5)),
                            ]

        elif format == 'R2x64_W64':
            self.args = [   OutReg64 (0, Range(7,  5)),
                            InReg64  (0, Range(15, 5)),
                            InReg64  (1, Range(20, 5)),
                            ]

        elif format == 'R1x64puImm_W64':
            self.args = [   OutReg64    (0, Range(7,  5)),
                            InReg64     (0, Range(15, 5)),
                            UnsignedImm (0, Range(20, 5)),
                            ]

        elif format == 'R1x64psImm_W64':
            self.args = [   OutReg64    (0, Range(7,  5)),
                            InReg64     (0, Range(15, 5)),
                            SignedImm   (0, Range(20, 5)),
                            ]

        elif format == 'R1x64puImm_W32':
            self.args = [   OutReg      (0, Range(7,  5)),
                            InReg64     (0, Range(15, 5)),
                            UnsignedImm (0, Range(20, 5)),
                            ]

        elif format == 'R1x64psImm_W32':
            self.args = [   OutReg      (0, Range(7,  5)),
                            InReg64     (0, Range(15, 5)),
                            SignedImm   (0, Range(20, 5)),
                            ]

        elif format == 'R1x64_W32':
            self.args = [   OutReg  (0, Range(7,  5)),
                            InReg64 (0, Range(15, 5)),
                            ]

        elif format == 'R2x64_W32':
            self.args = [   OutReg  (0, Range(7,  5)),
                            InReg64 (0, Range(15, 5)),
                            InReg64 (1, Range(20, 5)),
                            ]

        elif format == 'R1x32_W64':
            self.args = [   OutReg64 (0, Range(7,  5)),
                            InReg    (0, Range(15, 5)),
                            ]

        elif format == 'R2x32_W64':
            self.args = [   OutReg64 (0, Range(7,  5)),
                            InReg    (0, Range(15, 5)),
                            InReg    (1, Range(20, 5)),
                            ]

        elif format == 'R2x32_W32':
            self.args = [   OutReg   (0, Range(7,  5)),
                            InReg    (0, Range(15, 5)),
                            InReg    (1, Range(20, 5)),
                            ]

        elif format == 'R2x32p64_W64':
            self.args = [   OutReg64 (0, Range(7,  5)),
                            InReg    (0, Range(15, 5)),
                            InReg    (1, Range(20, 5)),
                            InReg64  (2, Range(7,  5)),
                            ]


        elif format == 'BITREV':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(15, 5)),
                            UnsignedImm(0, Range(20, 5)),
                            UnsignedImm(1, Range(25, 2)),
                            ]
        elif format == 'LRRRR':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (2, Range(7,  5), dumpName=False),
                            Indirect(InReg(0, Range(15, 5)), SignedImm(0, Ranges([]))),
                            InReg (1, Range(20, 5)),
                        ]
        elif format == 'F':
            self.args = [   InReg (0, Range(15, 5)),
                            ]
        elif format == 'RF':
            self.args = [   OutFReg(0, Range(7,  5)),
                            InFReg (0, Range(15, 5)),
                            InFReg (1, Range(20, 5)),
                            UnsignedImm(0, Range(12, 3)),
                            ]
        elif format == 'RF4':
            self.args = [   OutFReg(0, Range(7,  5)),
                            InFReg (2, Range(7,  5), dumpName=False),
                            InFReg (0, Range(15, 5)),
                            InFReg (1, Range(20, 5)),
                            UnsignedImm(0, Range(12, 3)),
                            ]
        elif format == 'RF2':
            self.args = [   OutReg(0, Range(7,  5)),
                            InFReg (0, Range(15, 5)),
                            InFReg (1, Range(20, 5)),
                            UnsignedImm(0, Range(12, 3)),
                            ]
        elif format == 'R2F1':
            self.args = [   OutReg(0, Range(7,  5)),
                            InFReg (0, Range(15, 5)),
                            UnsignedImm(0, Range(12, 3)),
                            ]
        elif format == 'R2F2':
            self.args = [   OutFReg(0, Range(7,  5)),
                            InReg (0, Range(15, 5)),
                            UnsignedImm(0, Range(12, 3)),
                            ]
        elif format == 'R2F3':
            self.args = [   OutFReg(0, Range(7,  5)),
                            InFReg (0, Range(15, 5)),
                            UnsignedImm(0, Range(12, 3)),
                            ]
        elif format == 'R3F':
            self.args = [   OutReg(0, Range(7,  5)),
                            InFReg (0, Range(15, 5)),
                            ]
        elif format == 'R3F2':
            self.args = [   OutFReg(0, Range(7,  5)),
                            InReg (0, Range(15, 5)),
                            ]
        elif format == 'R4U':
            self.args = [   OutFReg(0, Range(7,  5)),
                            InFReg (0, Range(15, 5)),
                            InFReg (1, Range(20, 5)),
                            InFReg (2, Range(27, 5)),
                            UnsignedImm(0, Range(12, 3)),
                            ]
        elif format == 'RVF':
            self.args = [   OutFReg(0, Range(7,  5)),
                            InFReg (0, Range(15, 5)),
                            InFReg (1, Range(20, 5)),
                            ]
        elif format == 'RVF2':
            self.args = [   OutFReg(0, Range(7,  5)),
                            InFReg (0, Range(15, 5)),
                            ]
        elif format == 'RVF4':
            self.args = [   OutFReg(0, Range(7,  5)),
                            InFReg (2, Range(7,  5), dumpName=False),
                            InFReg (0, Range(15, 5)),
                            InFReg (1, Range(20, 5)),
                            ]
        elif format == 'R2VF':
            self.args = [   OutReg(0, Range(7,  5)),
                            InFReg (0, Range(15, 5)),
                            InFReg (1, Range(20, 5)),
                            ]
        elif format == 'R2VF2':
            self.args = [   OutReg(0, Range(7,  5)),
                            InFReg (0, Range(15, 5)),
                            ]
        elif format == 'RRRR':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (2, Range(7,  5), dumpName=False),
                            InReg (0, Range(15, 5)),
                            InReg (1, Range(20, 5)),
                            ]
        elif format == 'LRR':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(15, 5)),
                            Indirect(InReg (1, Range(20, 5)), SignedImm(0, Ranges([]))),
                        ]
        elif format == 'RRRR64':
            self.args = [   OutReg64(0, Range(7,  5)),
                            InReg64 (2, Range(7,  5), dumpName=False),
                            InReg64 (0, Range(15, 5)),
                            InReg64 (1, Range(20, 5)),
                            ]
        elif format == 'RRRR2':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(7,  5), dumpName=False),
                            InReg (1, Range(15, 5)),
                            InReg (2, Range(20, 5)),
                            ]
        elif format == 'RRRS':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(7,  5)),
                            InReg (1, Range(15, 5)),
                            SignedImm(0, Ranges([[25, 1, 0], [20, 5, 1]])),
                            ]
        elif format == 'RRRU':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(7,  5)),
                            InReg (1, Range(15, 5)),
                            UnsignedImm(0, Ranges([[25, 1, 0], [20, 5, 1]])),
                            ]
        elif format == 'RRRU2':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(15, 5)),
                            InReg (1, Range(20, 5)),
                            UnsignedImm(0, Range(25, 5)),
                            ]
        elif format == 'RRRU3':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(7,  5)),
                            InReg (1, Range(15, 5)),
                            UnsignedImm(0, Range(20, 5)),
                            ]
        elif format == 'RRRRU':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (2, Range(7,  5)),
                            InReg (0, Range(15, 5)),
                            InReg (1, Range(20, 5)),
                            UnsignedImm(0, Range(25, 5)),
                            ]
        elif format == 'R1':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(15, 5)),
                            ]
        elif format == 'R1_64':
            self.args = [   OutReg64(0, Range(7,  5)),
                            InReg64 (0, Range(15, 5)),
                            ]
        elif format == 'RRU':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(15, 5)),
                            UnsignedImm(0, Ranges([[25, 1, 0], [20, 5, 1]])),
                            ]
        elif format == 'RRS':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(15, 5)),
                            SignedImm(0, Ranges([[25, 1, 0], [20, 5, 1]])),
                            ]
        elif format == 'RRU2':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(15, 5)),
                            UnsignedImm(0, Ranges([[25, 1, 0], [20, 5, 1]])),
                            ]
        elif format == 'LR':
            self.args = [   OutReg(0, Range(7,  5)),
                            Indirect(InReg (0, Range(15, 5)), InReg (1, Range(20, 5))),
                            ]
        elif format == 'LRPOST':
            self.args = [   OutReg(0, Range(7,  5)),
                            Indirect(InReg (0, Range(15, 5)), InReg (1, Range(20, 5)), postInc=True),
                            ]
        elif format == 'RR':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(15, 5)),
                            InReg (1, Range(20, 5)),
                            InReg (2, Range(25, 5)),
                        ]
        elif format == 'RR64':
            self.args = [   OutReg64(0, Range(7,  5)),
                            InReg64 (0, Range(15, 5)),
                            InReg64 (1, Range(20, 5)),
                            InReg64 (2, Range(7, 5)),
                        ]
        elif format == 'SR':
            self.args = [   InReg (1, Range(20, 5)),
                            Indirect(InReg (0, Range(15, 5)), InReg (2, Range(7, 5))),
                        ]
        elif format == 'SR_OLD':
            self.args = [   InReg (1, Range(20, 5)),
                            Indirect(InReg (0, Range(15, 5)), InReg (2, Range(25, 5))),
                        ]
        elif format == 'I':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(15, 5)),
                            SignedImm(0, Range(20, 12)),
                        ]
        elif format == 'I64':
            self.args = [   OutReg64(0, Range(7,  5)),
                            InReg64 (0, Range(15, 5)),
                            SignedImm(0, Range(20, 5)),
                        ]
        elif format == 'Z':
            self.args = [
                        ]
        elif format == 'L':
            self.args = [   OutReg(0, Range(7,  5)),
                            Indirect(InReg (0, Range(15, 5)), SignedImm(0, Range(20, 12))),
                        ]
        elif format == 'LRES':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(15, 5)),
                            UnsignedImm(0, Range(25, 1)),
                            UnsignedImm(1, Range(26, 1)),
                        ]
        elif format == 'FL':
            self.args = [   OutFReg(0, Range(7,  5)),
                            Indirect(InReg (0, Range(15, 5)), SignedImm(0, Range(20, 12))),
                        ]
        elif format == 'LPOST':
            self.args = [   OutReg(0, Range(7,  5)),
                            Indirect(InReg (0, Range(15, 5)), SignedImm(0, Range(20, 12)), postInc=True),
                        ]
        elif format == 'IU':
            self.args = [   OutReg(0, Range(7,  5)),
                            InReg (0, Range(15, 5)),
                            UnsignedImm(0, Range(20, 12)),
                        ]
        elif format == 'IUR':
            self.args = [   OutReg(0, Range(7,  5)),
                            UnsignedImm(1, Range(15, 5)),
                            UnsignedImm(0, Range(20, 12)),
                        ]
        elif format == 'I1U':
            self.args = [   OutReg(0, Range(7, 5)),
                            InReg(0, Range(15, 5)),
                            UnsignedImm(0, Range(20, 5)),
                        ]
        elif format == 'I1U64':
            self.args = [   OutReg(0, Range(7, 5)),
                            InReg(0, Range(15, 5)),
                            UnsignedImm(0, Range(20, 6)),
                        ]
        elif format == 'I2U':
            self.args = [   OutReg(0, Range(7, 5)),
                            UnsignedImm(0, Range(20, 12)),
                            UnsignedImm(1, Range(15, 5)),
                        ]
        elif format == 'I3U':
            self.args = [   UnsignedImm(0, Range(20, 8)),
			]
        elif format == 'I4U':
            self.args = [   OutReg(0, Range(7, 5)),
                            InReg(0, Range(15, 5)),
                            UnsignedImm(0, Range(25, 5)),
                            UnsignedImm(1, Range(20, 5)),
                        ]
        elif format == 'I5U':
            self.args = [   OutReg(0, Range(7, 5)),
                            InReg(1, Range(7, 5), dumpName=False),
                            InReg(0, Range(15, 5)),
                            UnsignedImm(0, Range(25, 5)),
                            UnsignedImm(1, Range(20, 5)),
                        ]
        elif format == 'I5U2':
            self.args = [   OutReg(0, Range(7, 5)),
                            InReg(1, Range(7, 5), dumpName=False),
                            InReg(0, Range(15, 5)),
                            InReg(2, Range(20, 5)),
                        ]
        elif format == 'IOU':
            self.args = [   UnsignedImm(0, Range(15, 5)),
                        ]
        elif format == 'S':
            self.args = [   InReg(1, Range(20, 5)),
                            Indirect(InReg(0, Range(15, 5)), SignedImm(0, Ranges([[7, 5, 0], [25, 7, 5]]))),
                        ]
        elif format == 'AMO':
            self.args = [   OutReg(0, Range(7, 5)),
                            InReg(1, Range(20, 5)),
                            InReg(0, Range(15, 5)),
                            UnsignedImm(0, Range(25, 1)),
                            UnsignedImm(1, Range(26, 1)),
                        ]
        elif format == 'FS':
            self.args = [   InFReg(1, Range(20, 5)),
                            Indirect(InReg(0, Range(15, 5)), SignedImm(0, Ranges([[7, 5, 0], [25, 7, 5]]))),
                        ]
        elif format == 'SPOST':
            self.args = [   InReg(1, Range(20, 5)),
                            Indirect(InReg(0, Range(15, 5)), SignedImm(0, Ranges([[7, 5, 0], [25, 7, 5]])), postInc=True),
                        ]
        elif format == 'S1':
            self.args = [   InReg(0, Range(15, 5)),
                            InReg(1, Range(20, 5)),
                            InReg(2, Range(25,5)),
                        ]
        elif format == 'INRR':
            self.args = [   InReg(0, Range(15, 5)),
                            InReg(1, Range(20, 5)),
                        ]
        elif format == 'SRPOST':
            self.args = [   InReg(1, Range(20, 5)),
                            Indirect(InReg(0, Range(15, 5)), InReg(2, Range(7,5)), postInc=True),
                        ]
        elif format == 'SB':
            self.args = [   InReg(0, Range(15, 5)),
                            InReg(1, Range(20, 5)),
                            SignedImm(0, Ranges([[7, 1, 11], [8, 4, 1], [25, 6, 5], [31, 1, 12]])),
                        ]
        elif format == 'SB2':
            self.args = [   InReg(0, Range(15, 5)),
                            SignedImm(0, Ranges([[7, 1, 11], [8, 4, 1], [25, 6, 5], [31, 1, 12]])),
                            SignedImm(1, Range(20, 5)),
                        ]
        elif format == 'U':
            self.args = [   OutReg(0, Range(7, 5)),
                            UnsignedImm(0, Range(12, 20, 12)),
                        ]
        elif format == 'UJ':
            self.args = [   OutReg(0, Range(7, 5)),
                            SignedImm(0, Ranges([[12, 8, 12], [20, 1, 11], [21, 10, 1], [31, 1, 20]])),
                        ]
        elif format == 'HL0':
            self.args = [   UnsignedImm(0, Range(7, 1)),
                            InReg (0, Range(15, 5)),
                            UnsignedImm(1, Range(20, 12)),
                        ]
        elif format == 'HL1':
            self.args = [   UnsignedImm(0, Range(7, 1)),
                            UnsignedImm(1, Range(20, 12)),
                            UnsignedImm(2, Range(15, 5)),
                        ]

        # Encodings for compressed instruction set

               # X   X   X   X   X   X   X   X   X   X   X   X   X   X   X   X
        # CR   #      func4    |      rd/rs1       |         rs2       |  op      #
        # CR1  #      func4    |        rs1        |          f5       |  op      # rs2=0, rd=0, si=0
        # CR2  #      func4    |        rd         |         rs2       |  op      # rs1=0
        # CR3  #      func4    |        rs1        |         rs2       |  op      # rd=1, si=0
        # CI1  #   func3 | si[5]|     rd/rs1       |      si[4:0]      |  op      #
        # CI1U #   func3 | ui[5]|     rd/rs1       |      ui[4:0]      |  op      #
        # CI2  #   func3 | si[7]|     rd/rs1       |      si[6:2]      |  op      #
        # CI3  #   func3 | ui[5]|       rd         |     ui[4:2|7:6]   |  op      # rs1=2, ui->si
        # CI4  #   func3 | si[9]|      func5       |    si[4|6|8:7|5]  |  op      # rs1=2, rd=2
        # CI5  #   func3 |si[17]|     rd/rs1       |      si[16:12]    |  op      # si->ui
        # CI6  #   func3 | si[5]|       rd         |      si[4:0]      |  op      # rs1=0
        # CSS  #   func3   |      ui[5:2|7:6]      |         rs2       |  op      # rs1=2, ui->si
        # CIW  #   func3   |        ui[5:4|9:6|2|3]        |    rd'    |  op      # rs1=2, ui->si
        # CL   #   func3   |      ui   |   rs1'    |   ui  |    rd'    |  op      # ui->si
        # CL1  #                                   op                             # rd=0
        # CS   #   func3   |  ui[5:3]  |   rs1'    |ui[6|2]|    rs2'   |  op      # ui->si
        # CS2  #      func6            |  rd/rs1   | func  |    rs2    |  op      #
        # CB1  #   func3   | si[8|4:3] |   rs1'    |   si[7:6|2:1|5]   |  op      # rs2=0
        # CB2  #   func3 |ui[5]| func2 |  rd/rs1'  |       ui[4:0]     |  op      #
        # CB2S #   func3 |si[5]| func2 |  rd/rs1'  |       si[4:0]     |  op      #
        # CJ   #   func3   |         si[11|4|9:8|6|7|3:1|5]            |  op      # rd=0
        # CJ1  #   func3   |         si[11|4|9:8|6|7|3:1|5]            |  op      # rd=1

        elif format == 'CR':
            self.args = [   OutReg(0, Range(7, 5)),
                            InReg(0, Range(7, 5)),
                            InReg(1, Range(2, 5)),
                        ]
        elif format == 'CR1':
            self.args = [   OutReg(0, Const(0)),
                            InReg(0, Range(7, 5)),
                            InReg(1, Const(0)),
                            SignedImm(0, Const(0)),
                        ]
        elif format == 'CR2':
            self.args = [   OutReg(0, Range(7, 5)),
                            InReg(0, Const(0)),
                            InReg(1, Range(2, 5)),
                        ]
        elif format == 'CR3':
            self.args = [   OutReg(0, Const(1)),
                            InReg(0, Range(7, 5)),
                            InReg(1, Range(2, 5)),
                            SignedImm(0, Const(0)),
                        ]
        elif format == 'CI1':
            self.args = [   OutReg(0, Range(7, 5)),
                            InReg(0, Range(7, 5)),
                            SignedImm(0, Ranges([[2, 5, 0], [12, 1, 5]])),
                        ]
        elif format == 'CI1U':
            self.args = [   OutReg(0, Range(7, 5)),
                            InReg(0, Range(7, 5)),
                            UnsignedImm(0, Ranges([[2, 5, 0], [12, 1, 5]])),
                        ]
        elif format == 'CI2':
            self.args = [   OutReg(0, Range(7, 5)),
                            InReg(0, Range(7, 5)),
                            SignedImm(0, Ranges([[2, 5, 2], [12, 1, 7]])),
                        ]
        elif format == 'CI3':
            self.args = [   OutReg(0, Range(7, 5)),
                            Indirect(InReg(0, Const(2)), SignedImm(0, Ranges([[4, 3, 2], [12, 1, 5], [2, 2, 6]]), isSigned=False)),
                        ]
        elif format == 'DCI3':
            self.args = [   OutReg(0, Range(7, 5)),
                            Indirect(InReg(0, Const(2)), SignedImm(0, Ranges([[5, 2, 3], [12, 1, 5], [2, 3, 6]]), isSigned=False)),
                        ]
        elif format == 'FCI3':
            self.args = [   OutFReg(0, Range(7, 5)),
                            Indirect(InReg(0, Const(2)), SignedImm(0, Ranges([[4, 3, 2], [12, 1, 5], [2, 2, 6]]), isSigned=False)),
                        ]
        elif format == 'FCI3D':
            self.args = [   OutFReg(0, Range(7, 5)),
                            Indirect(InReg(0, Const(2)), SignedImm(0, Ranges([[5, 2, 2], [12, 1, 5], [2, 3, 6]]), isSigned=False)),
                        ]
        elif format == 'CI4':
            self.args = [   OutReg(0, Const(2)),
                            InReg(0, Const(2)),
                            SignedImm(0, Ranges([[6, 1, 4], [2, 1, 5], [5, 1, 6], [3, 2, 7], [12, 1, 9]])),
                        ]
        elif format == 'CI5':
            self.args = [   OutReg(0, Range(7, 5)),
                            UnsignedImm(0, Ranges([[2, 5, 12], [12, 1, 17]]), isSigned=True),
                        ]
        elif format == 'CI6':
            self.args = [   OutReg(0, Range(7, 5)),
                            InReg(0, Const(0)),
                            SignedImm(0, Ranges([[2, 5, 0], [12, 1, 5]])),
                        ]
        elif format == 'CSS':
            self.args = [   InReg(1, Range(2, 5)),
                            Indirect(InReg(0, Const(2)), SignedImm(0, Ranges([[9, 4, 2], [7, 2, 6]]), isSigned=False)),
                        ]
        elif format == 'DCSS':
            self.args = [   InReg(1, Range(2, 5)),
                            Indirect(InReg(0, Const(2)), SignedImm(0, Ranges([[10, 3, 3], [7, 3, 6]]), isSigned=False)),
                        ]
        elif format == 'FCSS':
            self.args = [   InFReg(1, Range(2, 5)),
                            Indirect(InReg(0, Const(2)), SignedImm(0, Ranges([[9, 4, 2], [7, 2, 6]]), isSigned=False)),
                        ]
        elif format == 'FCSSD':
            self.args = [   InFReg(1, Range(2, 5)),
                            Indirect(InReg(0, Const(2)), SignedImm(0, Ranges([[10, 3, 3], [7, 3, 6]]), isSigned=False)),
                        ]
        elif format == 'CIW':
            self.args = [   OutRegComp(0, Range(2, 3)),
                            InReg(0, Const(2)),
                            SignedImm(0, Ranges([[6, 1, 2], [5, 1, 3], [11, 2, 4], [7, 4, 6]]), isSigned=False),
                        ]
        elif format == 'CL':
            self.args = [   OutRegComp(0, Range(2, 3)),
                            Indirect(InRegComp(0, Range(7, 3)), SignedImm(0, Ranges([[6, 1, 2], [10, 3, 3], [5, 1, 6]]), isSigned=False)),
                        ]
        elif format == 'CLD':
            self.args = [   OutRegComp(0, Range(2, 3)),
                            Indirect(InRegComp(0, Range(7, 3)), SignedImm(0, Ranges([[10, 3, 3], [5, 2, 6]]), isSigned=False)),
                        ]
        elif format == 'CFLD':
            self.args = [   OutFRegComp(0, Range(2, 3)),
                            Indirect(InRegComp(0, Range(7, 3)), SignedImm(0, Ranges([[10, 3, 3], [5, 2, 6]]), isSigned=False)),
                        ]
        elif format == 'FCL':
            self.args = [   OutFRegComp(0, Range(2, 3)),
                            Indirect(InRegComp(0, Range(7, 3)), SignedImm(0, Ranges([[6, 1, 2], [10, 3, 3], [5, 1, 6]]), isSigned=False)),
                        ]
        elif format == 'CS':
            self.args = [   InRegComp(1, Range(2, 3)),
                            Indirect(InRegComp(0, Range(7, 3)), SignedImm(0, Ranges([[6, 1, 2], [10, 3, 3], [5, 1, 6]]), isSigned=False)),
                        ]
        elif format == 'CFSD':
            self.args = [   InRegComp(1, Range(2, 3)),
                            Indirect(InRegComp(0, Range(7, 3)), SignedImm(0, Ranges([[10, 3, 3], [5, 2, 6]]), isSigned=False)),
                        ]
        elif format == 'CSD':
            self.args = [   InRegComp(1, Range(2, 3)),
                            Indirect(InRegComp(0, Range(7, 3)), SignedImm(0, Ranges([[10, 3, 3], [5, 2, 6]]), isSigned=False)),
                        ]
        elif format == 'FCS':
            self.args = [   InFRegComp(1, Range(2, 3)),
                            Indirect(InRegComp(0, Range(7, 3)), SignedImm(0, Ranges([[6, 1, 2], [10, 3, 3], [5, 1, 6]]), isSigned=False)),
                        ]
        elif format == 'CS2':
            self.args = [   OutRegComp(0, Range(7, 3)),
                            InRegComp(0, Range(7, 3)),
                            InRegComp(1, Range(2, 3)),
                        ]
        elif format == 'CB1':
            self.args = [   InRegComp(0, Range(7, 3)),
                            InReg(1, Const(0)),
                            SignedImm(0, Ranges([[3, 2, 1], [10, 2, 3], [2, 1, 5], [5, 2, 6], [12, 1, 8]])),
                        ]
        elif format == 'CB2':
            self.args = [   OutRegComp(0, Range(7, 3)),
                            InRegComp(0, Range(7, 3)),
                            UnsignedImm(0, Ranges([[2, 5, 0], [12, 1, 5]])),
                        ]
        elif format == 'CB2S':
            self.args = [   OutRegComp(0, Range(7, 3)),
                            InRegComp(0, Range(7, 3)),
                            SignedImm(0, Ranges([[2, 5, 0], [12, 1, 5]])),
                        ]
        elif format == 'CJ':
            self.args = [   OutReg(0, Const(0)),
                            SignedImm(0, Ranges([[3, 3, 1], [11, 1, 4], [2, 1, 5], [7, 1, 6], [6, 1, 7], [9, 2, 8], [8, 1, 10], [12, 1, 11]])),
                        ]
        elif format == 'CJ1':
            self.args = [   OutReg(0, Const(1)),
                            SignedImm(0, Ranges([[3, 3, 1], [11, 1, 4], [2, 1, 5], [7, 1, 6], [6, 1, 7], [9, 2, 8], [8, 1, 10], [12, 1, 11]])),
                        ]

        # Encodings for vector instruction set

                # 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
        # OPV   #   func6    |m|   vs2   |   vs1   |func3|    vd   |     op      # 
        # OPIVI #   func6    |m|   vs2   |   imm   |func3|    vd   |     op      #
        # OPVLS #  NF  |w|mop|m|  lumop  |   rs1   |width|    vd   |     op      #
        # OPVLI # 0|         zimm        |   rs1   |1 1 1|    rd   |     op      #

        elif format == 'OPV':
            self.args = [   OutReg     (0, Range(7 , 5)),
                            InReg      (0, Range(15, 5)),#rs1/vs1
                            InReg      (1, Range(20, 5)),#vs2
                            #UnsignedImm(0, Range(25, 0)),
                            UnsignedImm(0, Range(25, 1)),
                        ]
        elif format == 'OPVF':
            self.args = [   OutReg     (0, Range(7 , 5)),
                            InFReg     (0, Range(15, 5)),#rs1/vs1
                            InReg      (1, Range(20, 5)),#vs2
                            #UnsignedImm(0, Range(25, 0)),
                            UnsignedImm(0, Range(25, 1)),
                        ]            
        elif format == 'OPVFF':
            self.args = [   OutFReg    (0, Range(7 , 5)),
                            InFReg     (0, Range(15, 5)),#rs1/vs1
                            InReg      (1, Range(20, 5)),#vs2
                            #UnsignedImm(0, Range(25, 0)),
                            UnsignedImm(0, Range(25, 1)),
                        ]                        
        elif format == 'OPIVI':
            self.args = [   OutReg     (0, Range(7 , 5)),
                            SignedImm  (0, Range(15, 5)),
                            InReg      (0, Range(20, 5)),
                            UnsignedImm(0, Range(25, 1)),
                        ]
        elif format == 'OPVLS':
            self.args = [   OutReg     (0, Range(7 , 5)),
                            InReg      (0, Range(15, 5)),
                            UnsignedImm(0, Range(25, 0)),
                        ]
        #                           V 0.8
        # elif format == 'OPVLI':
        #     self.args = [   OutReg     (0, Range(7 , 5)),
        #                     InReg      (0, Range(15, 5)),
        #                     UnsignedImm(0, Range(20, 2)),# vlmul
        #                     UnsignedImm(1, Range(22, 3)),# vsew
        #                     UnsignedImm(2, Range(20, 12)),# vtype
        #                 ]
        #                           V 1.0
        elif format == 'OPVLI':
            self.args = [   OutReg     (0, Range(7 , 5)),
                            InReg      (0, Range(15, 5)),
                            UnsignedImm(0, Range(20, 3)),# vlmul
                            UnsignedImm(1, Range(23, 3)),# vsew
                            UnsignedImm(2, Range(20, 12)),# vtype
                        ]            
        elif format == 'OPVL':
            self.args = [   OutReg     (0, Range(7 , 5)),
                            InReg      (0, Range(15, 5)),
                            InReg      (1, Range(20, 5)),
                        ]


        elif format == 'CMPUSH':
            self.args = [   UnsignedImm(0, Range(4, 4)),
                            UnsignedImm(1, Range(2, 2)),
                            ]
        else:
            raise Exception('Undefined format: %s' % format)

        super(R5, self).__init__(label, type, encoding, decode, N, L, mapTo, group=group, fast_handler=fast_handler,
            tags=tags, isa_tags=isa_tags, is_macro_op=is_macro_op)



#
# RV32V
#

class Rv32v(IsaSubset):
    
    def __init__(self):
        super().__init__(name='v', instrs=[
            R5('vadd.vv'       ,   'OPV'  ,    '000000 - ----- ----- 000 ----- 1010111'),#inst[25] = VM , VM = 0 mask enable
            R5('vadd.vi'       ,   'OPIVI',    '000000 - ----- ----- 011 ----- 1010111'),
            R5('vadd.vx'       ,   'OPV'  ,    '000000 - ----- ----- 100 ----- 1010111'),

            R5('vsub.vv'       ,   'OPV'  ,    '000010 - ----- ----- 000 ----- 1010111'),
            R5('vsub.vx'       ,   'OPV'  ,    '000010 - ----- ----- 100 ----- 1010111'),

            R5('vrsub.vi'      ,   'OPIVI',    '000011 - ----- ----- 011 ----- 1010111'),
            R5('vrsub.vx'      ,   'OPV'  ,    '000011 - ----- ----- 100 ----- 1010111'),

            R5('vand.vv'       ,   'OPV'  ,    '001001 - ----- ----- 000 ----- 1010111'),#inst[25] = VM , VM = 0 mask enable
            R5('vand.vi'       ,   'OPIVI',    '001001 - ----- ----- 011 ----- 1010111'),
            R5('vand.vx'       ,   'OPV'  ,    '001001 - ----- ----- 100 ----- 1010111'),

            R5('vor.vv'        ,   'OPV'  ,    '001010 - ----- ----- 000 ----- 1010111'),#inst[25] = VM , VM = 0 mask enable
            R5('vor.vi'        ,   'OPIVI',    '001010 - ----- ----- 011 ----- 1010111'),
            R5('vor.vx'        ,   'OPV'  ,    '001010 - ----- ----- 100 ----- 1010111'),

            R5('vxor.vv'       ,   'OPV'  ,    '001011 - ----- ----- 000 ----- 1010111'),#inst[25] = VM , VM = 0 mask enable
            R5('vxor.vi'       ,   'OPIVI',    '001011 - ----- ----- 011 ----- 1010111'),
            R5('vxor.vx'       ,   'OPV'  ,    '001011 - ----- ----- 100 ----- 1010111'),

            R5('vmin.vv'       ,   'OPV'  ,    '000101 - ----- ----- 000 ----- 1010111'),#inst[25] = VM , VM = 0 mask enable
            R5('vmin.vx'       ,   'OPV'  ,    '000101 - ----- ----- 100 ----- 1010111'),

            R5('vminu.vv'      ,   'OPV'  ,    '000100 - ----- ----- 000 ----- 1010111'),#inst[25] = VM , VM = 0 mask enable
            R5('vminu.vx'      ,   'OPV'  ,    '000100 - ----- ----- 100 ----- 1010111'),

            R5('vmax.vv'       ,   'OPV'  ,    '000111 - ----- ----- 000 ----- 1010111'),#inst[25] = VM , VM = 0 mask enable
            R5('vmax.vx'       ,   'OPV'  ,    '000111 - ----- ----- 100 ----- 1010111'),

            R5('vmaxu.vv'      ,   'OPV'  ,    '000110 - ----- ----- 000 ----- 1010111'),#inst[25] = VM , VM = 0 mask enable
            R5('vmaxu.vx'      ,   'OPV'  ,    '000110 - ----- ----- 100 ----- 1010111'),

            R5('vmul.vv'       ,   'OPV'  ,    '100101 - ----- ----- 010 ----- 1010111'),#inst[25] = VM , VM = 0 mask enable
            R5('vmul.vx'       ,   'OPV'  ,    '100101 - ----- ----- 110 ----- 1010111'),

            R5('vmulh.vv'      ,   'OPV'  ,    '100111 - ----- ----- 010 ----- 1010111'),#inst[25] = VM , VM = 0 mask enable
            R5('vmulh.vx'      ,   'OPV'  ,    '100111 - ----- ----- 110 ----- 1010111'),

            R5('vmulhu.vv'     ,   'OPV'  ,    '100100 - ----- ----- 010 ----- 1010111'),#inst[25] = VM , VM = 0 mask enable
            R5('vmulhu.vx'     ,   'OPV'  ,    '100100 - ----- ----- 110 ----- 1010111'),

            R5('vmulhsu.vv'    ,   'OPV'  ,    '100110 - ----- ----- 010 ----- 1010111'),#inst[25] = VM , VM = 0 mask enable
            R5('vmulhsu.vx'    ,   'OPV'  ,    '100110 - ----- ----- 110 ----- 1010111'),

            R5('vmv.v.v'       ,   'OPV'  ,    '010111 - ----- ----- 000 ----- 1010111'),
            R5('vmv.v.i'       ,   'OPIVI',    '010111 - ----- ----- 011 ----- 1010111'),
            R5('vmv.v.x'       ,   'OPV'  ,    '010111 - ----- ----- 100 ----- 1010111'),
            R5('vmv.s.x'       ,   'OPV'  ,    '010000 - 00000 ----- 110 ----- 1010111'),
            R5('vmv.x.s'       ,   'OPV'  ,    '010000 - ----- 00000 010 ----- 1010111'),


            R5('vwmul.vv'      ,   'OPV'  ,    '111011 - ----- ----- 010 ----- 1010111'),#inst[25] = VM , VM = 0 mask enable
            R5('vwmul.vx'      ,   'OPV'  ,    '111011 - ----- ----- 110 ----- 1010111'),
    
            R5('vwmulu.vv'     ,   'OPV'  ,    '111000 - ----- ----- 010 ----- 1010111'),#inst[25] = VM , VM = 0 mask enable
            R5('vwmulu.vx'     ,   'OPV'  ,    '111000 - ----- ----- 110 ----- 1010111'),

            R5('vwmulsu.vv'    ,   'OPV'  ,    '111010 - ----- ----- 010 ----- 1010111'),#inst[25] = VM , VM = 0 mask enable
            R5('vwmulsu.vx'    ,   'OPV'  ,    '111010 - ----- ----- 110 ----- 1010111'),

            R5('vmacc.vv'      ,   'OPV'  ,    '101101 - ----- ----- 010 ----- 1010111'),
            R5('vmacc.vx'      ,   'OPV'  ,    '101101 - ----- ----- 110 ----- 1010111'),

            R5('vmadd.vv'      ,   'OPV'  ,    '101001 - ----- ----- 010 ----- 1010111'),
            R5('vmadd.vx'      ,   'OPV'  ,    '101001 - ----- ----- 110 ----- 1010111'),

            R5('vnmsac.vv'     ,   'OPV'  ,    '101111 - ----- ----- 010 ----- 1010111'),
            R5('vnmsac.vx'     ,   'OPV'  ,    '101111 - ----- ----- 110 ----- 1010111'),

            R5('vnmsub.vv'     ,   'OPV'  ,    '101011 - ----- ----- 010 ----- 1010111'),
            R5('vnmsub.vx'     ,   'OPV'  ,    '101011 - ----- ----- 110 ----- 1010111'),

            R5('vwmacc.vv'     ,   'OPV'  ,    '111101 - ----- ----- 010 ----- 1010111'),
            R5('vwmacc.vx'     ,   'OPV'  ,    '111101 - ----- ----- 110 ----- 1010111'),

            R5('vwmaccu.vv'    ,   'OPV'  ,    '111100 - ----- ----- 010 ----- 1010111'),
            R5('vwmaccu.vx'    ,   'OPV'  ,    '111100 - ----- ----- 110 ----- 1010111'),

            R5('vwmaccus.vx'   ,   'OPV'  ,    '111110 - ----- ----- 110 ----- 1010111'),

            R5('vwmaccsu.vv'   ,   'OPV'  ,    '111111 - ----- ----- 010 ----- 1010111'),
            R5('vwmaccsu.vx'   ,   'OPV'  ,    '111111 - ----- ----- 110 ----- 1010111'),

            R5('vredsum.vs'    ,   'OPV'  ,    '000000 - ----- ----- 010 ----- 1010111'),
            R5('vredand.vs'    ,   'OPV'  ,    '000001 - ----- ----- 010 ----- 1010111'),
            R5('vredor.vs'     ,   'OPV'  ,    '000010 - ----- ----- 010 ----- 1010111'),
            R5('vredxor.vs'    ,   'OPV'  ,    '000011 - ----- ----- 010 ----- 1010111'),
            R5('vredminu.vs'   ,   'OPV'  ,    '000100 - ----- ----- 010 ----- 1010111'),
            R5('vredmin.vs'    ,   'OPV'  ,    '000101 - ----- ----- 010 ----- 1010111'),
            R5('vredmaxu.vs'   ,   'OPV'  ,    '000110 - ----- ----- 010 ----- 1010111'),
            R5('vredmax.vs'    ,   'OPV'  ,    '000111 - ----- ----- 010 ----- 1010111'),


            R5('vslideup.vi'   ,   'OPIVI',    '001110 - ----- ----- 011 ----- 1010111'),
            R5('vslideup.vx'   ,   'OPV'  ,    '001110 - ----- ----- 100 ----- 1010111'),

            R5('vslidedown.vi' ,   'OPIVI',    '001111 - ----- ----- 011 ----- 1010111'),
            R5('vslidedown.vx' ,   'OPV'  ,    '001111 - ----- ----- 100 ----- 1010111'),

            R5('vslide1up.vx'  ,   'OPV'  ,    '001110 - ----- ----- 110 ----- 1010111'),
            R5('vslide1down.vx',   'OPV'  ,    '001111 - ----- ----- 110 ----- 1010111'),

            R5('vdiv.vv'       ,   'OPV'  ,    '100001 - ----- ----- 010 ----- 1010111'),
            R5('vdiv.vx'       ,   'OPV'  ,    '100001 - ----- ----- 110 ----- 1010111'),

            R5('vdivu.vv'      ,   'OPV'  ,    '100000 - ----- ----- 010 ----- 1010111'),
            R5('vdivu.vx'      ,   'OPV'  ,    '100000 - ----- ----- 110 ----- 1010111'),

            R5('vrem.vv'       ,   'OPV'  ,    '100011 - ----- ----- 010 ----- 1010111'),
            R5('vrem.vx'       ,   'OPV'  ,    '100011 - ----- ----- 110 ----- 1010111'),

            R5('vremu.vv'      ,   'OPV'  ,    '100010 - ----- ----- 010 ----- 1010111'),
            R5('vremu.vx'      ,   'OPV'  ,    '100010 - ----- ----- 110 ----- 1010111'),





            R5('vfadd.vv'      ,   'OPV'  ,    '000000 - ----- ----- 001 ----- 1010111'),
            R5('vfadd.vf'      ,   'OPVF' ,    '000000 - ----- ----- 101 ----- 1010111'),

            R5('vfsub.vv'      ,   'OPV'  ,    '000010 - ----- ----- 001 ----- 1010111'),
            R5('vfsub.vf'      ,   'OPVF' ,    '000010 - ----- ----- 101 ----- 1010111'),

            R5('vfrsub.vf'     ,   'OPVF'  ,    '100111 - ----- ----- 101 ----- 1010111'),

            R5('vfmin.vv'      ,   'OPV'  ,    '000100 - ----- ----- 001 ----- 1010111'),
            R5('vfmin.vf'      ,   'OPVF' ,    '000100 - ----- ----- 101 ----- 1010111'),

            R5('vfmax.vv'      ,   'OPV'  ,    '000110 - ----- ----- 001 ----- 1010111'),
            R5('vfmax.vf'      ,   'OPVF' ,    '000110 - ----- ----- 101 ----- 1010111'),

            R5('vfmul.vv'      ,   'OPV'  ,    '100100 - ----- ----- 001 ----- 1010111'),
            R5('vfmul.vf'      ,   'OPVF' ,    '100100 - ----- ----- 101 ----- 1010111'),

            R5('vfmacc.vv'     ,   'OPV'  ,    '101100 - ----- ----- 001 ----- 1010111'),
            R5('vfmacc.vf'     ,   'OPVF' ,    '101100 - ----- ----- 101 ----- 1010111'),

            R5('vfnmacc.vv'    ,   'OPV'  ,    '101101 - ----- ----- 001 ----- 1010111'),
            R5('vfnmacc.vf'    ,   'OPVF' ,    '101101 - ----- ----- 101 ----- 1010111'),

            R5('vfmsac.vv'     ,   'OPV'  ,    '101110 - ----- ----- 001 ----- 1010111'),
            R5('vfmsac.vf'     ,   'OPVF' ,    '101110 - ----- ----- 101 ----- 1010111'),

            R5('vfnmsac.vv'    ,   'OPV'  ,    '101111 - ----- ----- 001 ----- 1010111'),
            R5('vfnmsac.vf'    ,   'OPVF' ,    '101111 - ----- ----- 101 ----- 1010111'),

            R5('vfmadd.vv'     ,   'OPV'  ,    '101000 - ----- ----- 001 ----- 1010111'),
            R5('vfmadd.vf'     ,   'OPVF' ,    '101000 - ----- ----- 101 ----- 1010111'),

            R5('vfnmadd.vv'    ,   'OPV'  ,    '101001 - ----- ----- 001 ----- 1010111'),
            R5('vfnmadd.vf'    ,   'OPVF' ,    '101001 - ----- ----- 101 ----- 1010111'),

            R5('vfmsub.vv'     ,   'OPV'  ,    '101010 - ----- ----- 001 ----- 1010111'),
            R5('vfmsub.vf'     ,   'OPVF' ,    '101010 - ----- ----- 101 ----- 1010111'),

            R5('vfnmsub.vv'    ,   'OPV'  ,    '101011 - ----- ----- 001 ----- 1010111'),
            R5('vfnmsub.vf'    ,   'OPVF' ,    '101011 - ----- ----- 101 ----- 1010111'),

            R5('vfredmax.vs'      ,   'OPV'  ,    '000111 - ----- ----- 001 ----- 1010111'),
            
            R5('vfredmin.vs'      ,   'OPV'  ,    '000101 - ----- ----- 001 ----- 1010111'),

            R5('vfredsum.vs'      ,   'OPV'  ,    '000001 - ----- ----- 001 ----- 1010111'),
            R5('vfredosum.vs'     ,   'OPV'  ,    '000011 - ----- ----- 001 ----- 1010111'),

            R5('vfwadd.vv'        ,   'OPV'  ,    '110000 - ----- ----- 001 ----- 1010111'),
            R5('vfwadd.vf'        ,   'OPVF' ,    '110000 - ----- ----- 101 ----- 1010111'),
            R5('vfwadd.wv'        ,   'OPV'  ,    '110100 - ----- ----- 001 ----- 1010111'),
            R5('vfwadd.wf'        ,   'OPVF' ,    '110100 - ----- ----- 101 ----- 1010111'),

            R5('vfwsub.vv'        ,   'OPV'  ,    '110010 - ----- ----- 001 ----- 1010111'),
            R5('vfwsub.vf'        ,   'OPVF' ,    '110010 - ----- ----- 101 ----- 1010111'),
            R5('vfwsub.wv'        ,   'OPV'  ,    '110110 - ----- ----- 001 ----- 1010111'),
            R5('vfwsub.wf'        ,   'OPVF' ,    '110110 - ----- ----- 101 ----- 1010111'),

            R5('vfwmul.vv'        ,   'OPV'  ,    '111000 - ----- ----- 001 ----- 1010111'),
            R5('vfwmul.vf'        ,   'OPVF' ,    '111000 - ----- ----- 101 ----- 1010111'),

            R5('vfwmacc.vv'       ,   'OPV'  ,    '111100 - ----- ----- 001 ----- 1010111'),
            R5('vfwmacc.vf'       ,   'OPVF' ,    '111100 - ----- ----- 101 ----- 1010111'),

            R5('vfwmsac.vv'       ,   'OPV'  ,    '111110 - ----- ----- 001 ----- 1010111'),
            R5('vfwmsac.vf'       ,   'OPVF' ,    '111110 - ----- ----- 101 ----- 1010111'),

            R5('vfwnmsac.vv'      ,   'OPV'  ,    '111111 - ----- ----- 001 ----- 1010111'),
            R5('vfwnmsac.vf'      ,   'OPVF' ,    '111111 - ----- ----- 101 ----- 1010111'),

            R5('vfsgnj.vv'        ,   'OPV'  ,    '001000 - ----- ----- 001 ----- 1010111'),
            R5('vfsgnj.vf'        ,   'OPVF' ,    '001000 - ----- ----- 101 ----- 1010111'),

            R5('vfsgnjn.vv'       ,   'OPV'  ,    '001001 - ----- ----- 001 ----- 1010111'),
            R5('vfsgnjn.vf'       ,   'OPVF' ,    '001001 - ----- ----- 101 ----- 1010111'),

            R5('vfsgnjx.vv'       ,   'OPV'  ,    '001010 - ----- ----- 001 ----- 1010111'),
            R5('vfsgnjx.vf'       ,   'OPVF' ,    '001010 - ----- ----- 101 ----- 1010111'),
            
            R5('vfcvt.xu.f.v'     ,   'OPV'  ,    '010010 - ----- 00000 001 ----- 1010111'),
            
            R5('vfcvt.x.f.v'      ,   'OPV'  ,    '010010 - ----- 00001 001 ----- 1010111'),
            
            R5('vfcvt.f.xu.v'     ,   'OPV'  ,    '010010 - ----- 00010 001 ----- 1010111'),
            
            R5('vfcvt.f.x.v'      ,   'OPV'  ,    '010010 - ----- 00011 001 ----- 1010111'),
            
            R5('vfcvt.rtz.xu.f.v' ,   'OPV'  ,    '010010 - ----- 00110 001 ----- 1010111'),
            
            R5('vfcvt.rtz.x.f.v'  ,   'OPV'  ,    '010010 - ----- 00111 001 ----- 1010111'),
            
            R5('vfncvt.xu.f.w'    ,   'OPV'  ,    '010010 - ----- 10000 001 ----- 1010111'),
            
            R5('vfncvt.x.f.w'     ,   'OPV'  ,    '010010 - ----- 10001 001 ----- 1010111'),
            
            R5('vfncvt.f.xu.w'    ,   'OPV'  ,    '010010 - ----- 10010 001 ----- 1010111'),
            
            R5('vfncvt.f.x.w'     ,   'OPV'  ,    '010010 - ----- 10011 001 ----- 1010111'),
            
            R5('vfncvt.f.f.w'     ,   'OPV'  ,    '010010 - ----- 10100 001 ----- 1010111'),
            
            R5('vfncvt.rod.f.f.w' ,   'OPV'  ,    '010010 - ----- 10101 001 ----- 1010111'),
            
            R5('vfncvt.rtz.xu.f.w',   'OPV'  ,    '010010 - ----- 10110 001 ----- 1010111'),
            
            R5('vfncvt.rtz.x.f.w' ,   'OPV'  ,    '010010 - ----- 10111 001 ----- 1010111'),


            
            R5('vfmv.v.f'         ,   'OPVF' ,    '010111 - ----- ----- 101 ----- 1010111'),
            R5('vfmv.s.f'         ,   'OPVF' ,    '010000 - 00000 ----- 101 ----- 1010111'),
            R5('vfmv.f.s'         ,   'OPVFF',    '010000 - ----- 00000 001 ----- 1010111'),

            R5('vle8.v'           ,   'OPV'  ,    '000 0 00 - 00000 ----- 000 ----- 0000111'),# vd, (rs1), vm
            R5('vle16.v'          ,   'OPV'  ,    '000 0 00 - 00000 ----- 101 ----- 0000111'),
            R5('vle32.v'          ,   'OPV'  ,    '000 0 00 - 00000 ----- 110 ----- 0000111'),
            R5('vle64.v'          ,   'OPV'  ,    '000 0 00 - 00000 ----- 111 ----- 0000111'),

            R5('vse8.v'           ,   'OPV'  ,    '000 0 00 - 00000 ----- 000 ----- 0100111'),
            R5('vse16.v'          ,   'OPV'  ,    '000 0 00 - 00000 ----- 101 ----- 0100111'),
            R5('vse32.v'          ,   'OPV'  ,    '000 0 00 - 00000 ----- 110 ----- 0100111'),
            R5('vse64.v'          ,   'OPV'  ,    '000 0 00 - 00000 ----- 111 ----- 0100111'),

            R5('vluxei8.v'        ,   'OPV'  ,    '000 0 01 - ----- ----- 000 ----- 0000111'),# vd, (rs1), vm
            R5('vluxei16.v'       ,   'OPV'  ,    '000 0 01 - ----- ----- 101 ----- 0000111'),
            R5('vluxei32.v'       ,   'OPV'  ,    '000 0 01 - ----- ----- 110 ----- 0000111'),
            R5('vluxei64.v'       ,   'OPV'  ,    '000 0 01 - ----- ----- 111 ----- 0000111'),

            R5('vsuxei8.v'        ,   'OPV'  ,    '000 0 01 - ----- ----- 000 ----- 0100111'),# vd, (rs1), vm
            R5('vsuxei16.v'       ,   'OPV'  ,    '000 0 01 - ----- ----- 101 ----- 0100111'),
            R5('vsuxei32.v'       ,   'OPV'  ,    '000 0 01 - ----- ----- 110 ----- 0100111'),
            R5('vsuxei64.v'       ,   'OPV'  ,    '000 0 01 - ----- ----- 111 ----- 0100111'),

            R5('vlse8.v'          ,   'OPV'  ,    '000 0 10 - ----- ----- 000 ----- 0000111'),# vd, (rs1), vm
            R5('vlse16.v'         ,   'OPV'  ,    '000 0 10 - ----- ----- 101 ----- 0000111'),
            R5('vlse32.v'         ,   'OPV'  ,    '000 0 10 - ----- ----- 110 ----- 0000111'),
            R5('vlse64.v'         ,   'OPV'  ,    '000 0 10 - ----- ----- 111 ----- 0000111'),

            R5('vsse8.v'          ,   'OPV'  ,    '000 0 10 - ----- ----- 000 ----- 0100111'),# vd, (rs1), vm
            R5('vsse16.v'         ,   'OPV'  ,    '000 0 10 - ----- ----- 101 ----- 0100111'),
            R5('vsse32.v'         ,   'OPV'  ,    '000 0 10 - ----- ----- 110 ----- 0100111'),
            R5('vsse64.v'         ,   'OPV'  ,    '000 0 10 - ----- ----- 111 ----- 0100111'),












            R5('vl1r.v'       ,   'OPV'  ,    '000 0 001 01000 ----- 000 ----- 0000111'),# vd, (rs1), vm
            # R5('vl1re8.v'     ,   'OPV'  ,    '000 0 001 01000 ----- 000 ----- 0000111'),# vd, (rs1), vm
            R5('vl1re16.v'    ,   'OPV'  ,    '000 0 001 01000 ----- 101 ----- 0000111'),
            R5('vl1re32.v'    ,   'OPV'  ,    '000 0 001 01000 ----- 110 ----- 0000111'),
            R5('vl1re64.v'    ,   'OPV'  ,    '000 0 001 01000 ----- 111 ----- 0000111'),

            R5('vl2r.v'       ,   'OPV'  ,    '001 0 001 01000 ----- 000 ----- 0000111'),# vd, (rs1), vm
            # R5('vl2re8.v'     ,   'OPV'  ,    '001 0 001 01000 ----- 000 ----- 0000111'),# vd, (rs1), vm
            R5('vl2re16.v'    ,   'OPV'  ,    '001 0 001 01000 ----- 101 ----- 0000111'),
            R5('vl2re32.v'    ,   'OPV'  ,    '001 0 001 01000 ----- 110 ----- 0000111'),
            R5('vl2re64.v'    ,   'OPV'  ,    '001 0 001 01000 ----- 111 ----- 0000111'),

            R5('vl4r.v'       ,   'OPV'  ,    '011 0 001 01000 ----- 000 ----- 0000111'),# vd, (rs1), vm
            # R5('vl4re8.v'     ,   'OPV'  ,    '011 0 001 01000 ----- 000 ----- 0000111'),# vd, (rs1), vm
            R5('vl4re16.v'    ,   'OPV'  ,    '011 0 001 01000 ----- 101 ----- 0000111'),
            R5('vl4re32.v'    ,   'OPV'  ,    '011 0 001 01000 ----- 110 ----- 0000111'),
            R5('vl4re64.v'    ,   'OPV'  ,    '011 0 001 01000 ----- 111 ----- 0000111'),

            R5('vl8r.v'       ,   'OPV'  ,    '111 0 001 01000 ----- 000 ----- 0000111'),# vd, (rs1), vm
            # R5('vl8re8.v'     ,   'OPV'  ,    '111 0 001 01000 ----- 000 ----- 0000111'),# vd, (rs1), vm
            R5('vl8re16.v'    ,   'OPV'  ,    '111 0 001 01000 ----- 101 ----- 0000111'),
            R5('vl8re32.v'    ,   'OPV'  ,    '111 0 001 01000 ----- 110 ----- 0000111'),
            R5('vl8re64.v'    ,   'OPV'  ,    '111 0 001 01000 ----- 111 ----- 0000111'),


            R5('vs1r.v'       ,   'OPV'  ,    '000 0 001 01000 ----- 000 ----- 0100111'),# vd, (rs1), vm
            R5('vs2r.v'       ,   'OPV'  ,    '001 0 001 01000 ----- 000 ----- 0100111'),# vd, (rs1), vm
            R5('vs4r.v'       ,   'OPV'  ,    '011 0 001 01000 ----- 000 ----- 0100111'),# vd, (rs1), vm
            R5('vs8r.v'       ,   'OPV'  ,    '111 0 001 01000 ----- 000 ----- 0100111'),# vd, (rs1), vm











            #                           V 1.0
            R5('vsetvli' ,   'OPVLI',    '- ----------- ----- 111 ----- 1010111'), # zimm = {3'b000,vma,vta,vsew[2:0],vlmul[2:0]}
            
            #                           V 0.8    
            # R5('vsetvli' ,   'OPVLI',    '0 ----------- ----- 111 ----- 1010111'), # zimm = {7'b0000000,vsew[2:0],vlmul[1:0]}
            R5('vsetvl'  ,   'OPVL' ,    '1000000 ----- ----- 111 ----- 1010111'),

            #R5('csrr', 'IU',  '------- ----- 00000 010 ----- 1110011', decode='csr_decode'),


        ])



#
# RV64I
#

class Rv64i(IsaSubset):
    
    def __init__(self):
        super().__init__(name='i', instrs=[
            R5('lwu',   'L',    '------- ----- ----- 110 ----- 0000011', fast_handler=True, tags=["load"]),
            R5('ld',    'L',    '------- ----- ----- 011 ----- 0000011', fast_handler=True, tags=["load"]),
            R5('sd',    'S',    '------- ----- ----- 011 ----- 0100011', fast_handler=True, tags=["store"]),
            R5('slli',  'I1U64','000000- ----- ----- 001 ----- 0010011'),
            R5('srli',  'I1U64','000000- ----- ----- 101 ----- 0010011'),
            R5('srai',  'I1U64','010000- ----- ----- 101 ----- 0010011'),
            R5('addiw', 'I',    '------- ----- ----- 000 ----- 0011011'),
            R5('slliw', 'I1U',  '0000000 ----- ----- 001 ----- 0011011'),
            R5('srliw', 'I1U',  '0000000 ----- ----- 101 ----- 0011011'),
            R5('sraiw', 'I1U',  '0100000 ----- ----- 101 ----- 0011011'),
            R5('addw',   'R',   '0000000 ----- ----- 000 ----- 0111011'),
            R5('subw',   'R',   '0100000 ----- ----- 000 ----- 0111011'),
            R5('sllw',   'R',   '0000000 ----- ----- 001 ----- 0111011'),
            R5('srlw',   'R',   '0000000 ----- ----- 101 ----- 0111011'),
            R5('sraw',   'R',   '0100000 ----- ----- 101 ----- 0111011'),
        ])



#
# RV32I
#
class Rv32i(IsaSubset):
    
    def __init__(self):
        super().__init__(name='i', instrs=[
            R5('lui',   'U',    '------- ----- ----- --- ----- 0110111', 'lui_decode'),
            R5('auipc', 'U',    '------- ----- ----- --- ----- 0010111', 'auipc_decode'),
            R5('jal',   'UJ',   '------- ----- ----- --- ----- 1101111', 'jal_decode', fast_handler=True),
            R5('jalr',  'I',    '------- ----- ----- 000 ----- 1100111', fast_handler=True),
            R5('beq',   'SB',   '------- ----- ----- 000 ----- 1100011', 'bxx_decode', fast_handler=True),
            R5('bne',   'SB',   '------- ----- ----- 001 ----- 1100011', 'bxx_decode', fast_handler=True),
            R5('blt',   'SB',   '------- ----- ----- 100 ----- 1100011', 'bxx_decode', fast_handler=True),
            R5('bge',   'SB',   '------- ----- ----- 101 ----- 1100011', 'bxx_decode', fast_handler=True),
            R5('bltu',  'SB',   '------- ----- ----- 110 ----- 1100011', 'bxx_decode', fast_handler=True),
            R5('bgeu',  'SB',   '------- ----- ----- 111 ----- 1100011', 'bxx_decode', fast_handler=True),
            R5('lb',    'L',    '------- ----- ----- 000 ----- 0000011', fast_handler=True, tags=["load"]),
            R5('lh',    'L',    '------- ----- ----- 001 ----- 0000011', fast_handler=True, tags=["load"]),
            R5('lw',    'L',    '------- ----- ----- 010 ----- 0000011', fast_handler=True, tags=["load"]),
            R5('lbu',   'L',    '------- ----- ----- 100 ----- 0000011', fast_handler=True, tags=["load"]),
            R5('lhu',   'L',    '------- ----- ----- 101 ----- 0000011', fast_handler=True, tags=["load"]),
            R5('sb',    'S',    '------- ----- ----- 000 ----- 0100011', fast_handler=True, tags=["store"]),
            R5('sh',    'S',    '------- ----- ----- 001 ----- 0100011', fast_handler=True, tags=["store"]),
            R5('sw',    'S',    '------- ----- ----- 010 ----- 0100011', fast_handler=True, tags=["store"]),
            R5('addi',  'I',    '------- ----- ----- 000 ----- 0010011'),
            R5('addi',  'Z',    '0000000 00000 00000 000 00000 0010011', mapTo="nop", L='nop'),
            R5('slti',  'I',    '------- ----- ----- 010 ----- 0010011'),
            R5('sltiu', 'I',    '------- ----- ----- 011 ----- 0010011'),
            R5('xori',  'I',    '------- ----- ----- 100 ----- 0010011'),
            R5('ori',   'I',    '------- ----- ----- 110 ----- 0010011'),
            R5('andi',  'I',    '------- ----- ----- 111 ----- 0010011'),
            R5('slli',  'I1U64','0000000 ----- ----- 001 ----- 0010011'),
            R5('srli',  'I1U64','0000000 ----- ----- 101 ----- 0010011'),
            R5('srai',  'I1U64','0100000 ----- ----- 101 ----- 0010011'),
            R5('add',   'R',    '0000000 ----- ----- 000 ----- 0110011'),
            R5('sub',   'R',    '0100000 ----- ----- 000 ----- 0110011'),
            R5('sll',   'R',    '0000000 ----- ----- 001 ----- 0110011'),
            R5('slt',   'R',    '0000000 ----- ----- 010 ----- 0110011'),
            R5('sltu',  'R',    '0000000 ----- ----- 011 ----- 0110011'),
            R5('xor',   'R',    '0000000 ----- ----- 100 ----- 0110011'),
            R5('srl',   'R',    '0000000 ----- ----- 101 ----- 0110011'),
            R5('sra',   'R',    '0100000 ----- ----- 101 ----- 0110011'),
            R5('or',    'R',    '0000000 ----- ----- 110 ----- 0110011'),
            R5('and',   'R',    '0000000 ----- ----- 111 ----- 0110011'),
            R5('fence', 'I3U',  '0000--- ----- 00000 000 00000 0001111'),
            R5('fence.i','I',   '0000000 00000 00000 001 00000 0001111'),
            R5('ecall',  'I',   '0000000 00000 00000 000 00000 1110011'),
            R5('ebreak', 'I',   '0000000 00001 00000 000 00000 1110011')
        #
        ])


#
# RV32M
#
class Rv32m(IsaSubset):
    
    def __init__(self):
        super().__init__(name='m', instrs=[
            R5('mul',   'R', '0000001 ----- ----- 000 ----- 0110011', tags=['mul']),
            R5('mulh',  'R', '0000001 ----- ----- 001 ----- 0110011', tags=['mulh']),
            R5('mulhsu','R', '0000001 ----- ----- 010 ----- 0110011', tags=['mulh']),
            R5('mulhu', 'R', '0000001 ----- ----- 011 ----- 0110011', tags=['mulh']),
            R5('div',   'R', '0000001 ----- ----- 100 ----- 0110011', tags=['div']),
            R5('divu',  'R', '0000001 ----- ----- 101 ----- 0110011', tags=['div']),
            R5('rem',   'R', '0000001 ----- ----- 110 ----- 0110011', tags=['div']),
            R5('remu',  'R', '0000001 ----- ----- 111 ----- 0110011', tags=['div']),

        ])

class Rv64m(IsaSubset):
    
    def __init__(self):
        super().__init__(name='m', instrs=[
            R5('mulw',  'R', '0000001 ----- ----- 000 ----- 0111011', tags=['mul']),
            R5('divw',  'R', '0000001 ----- ----- 100 ----- 0111011', tags=['div']),
            R5('divuw', 'R', '0000001 ----- ----- 101 ----- 0111011', tags=['div']),
            R5('remw',  'R', '0000001 ----- ----- 110 ----- 0111011', tags=['div']),
            R5('remuw', 'R', '0000001 ----- ----- 111 ----- 0111011', tags=['div']),
        ])

class Rv32a(IsaSubset):
    
    def __init__(self):
        super().__init__(name='a', instrs=[
            R5('lr.w',       'LRES',  '00010 -- 00000 ----- 010 ----- 0101111'),
            R5('sc.w',       'AMO',   '00011 -- ----- ----- 010 ----- 0101111'),
            R5('amoswap.w',  'AMO',   '00001 -- ----- ----- 010 ----- 0101111'),
            R5('amoadd.w' ,  'AMO',   '00000 -- ----- ----- 010 ----- 0101111'),
            R5('amoxor.w' ,  'AMO',   '00100 -- ----- ----- 010 ----- 0101111'),
            R5('amoand.w' ,  'AMO',   '01100 -- ----- ----- 010 ----- 0101111'),
            R5('amoor.w'  ,  'AMO',   '01000 -- ----- ----- 010 ----- 0101111'),
            R5('amomin.w' ,  'AMO',   '10000 -- ----- ----- 010 ----- 0101111'),
            R5('amomax.w' ,  'AMO',   '10100 -- ----- ----- 010 ----- 0101111'),
            R5('amominu.w',  'AMO',   '11000 -- ----- ----- 010 ----- 0101111'),
            R5('amomaxu.w',  'AMO',   '11100 -- ----- ----- 010 ----- 0101111')
        ])

class Rv64a(IsaSubset):
    
    def __init__(self):
        super().__init__(name='a', instrs=[
            R5('lr.d',       'LRES',  '00010 -- 00000 ----- 011 ----- 0101111'),
            R5('sc.d',       'AMO',   '00011 -- ----- ----- 011 ----- 0101111'),
            R5('amoswap.d',  'AMO',   '00001 -- ----- ----- 011 ----- 0101111'),
            R5('amoadd.d' ,  'AMO',   '00000 -- ----- ----- 011 ----- 0101111'),
            R5('amoxor.d' ,  'AMO',   '00100 -- ----- ----- 011 ----- 0101111'),
            R5('amoand.d' ,  'AMO',   '01100 -- ----- ----- 011 ----- 0101111'),
            R5('amoor.d'  ,  'AMO',   '01000 -- ----- ----- 011 ----- 0101111'),
            R5('amomin.d' ,  'AMO',   '10000 -- ----- ----- 011 ----- 0101111'),
            R5('amomax.d' ,  'AMO',   '10100 -- ----- ----- 011 ----- 0101111'),
            R5('amominu.d',  'AMO',   '11000 -- ----- ----- 011 ----- 0101111'),
            R5('amomaxu.d',  'AMO',   '11100 -- ----- ----- 011 ----- 0101111')
        ])

class Rv32f(IsaSubset):
    
    def __init__(self):
        super().__init__(name='f', instrs=[
            R5('flw',       'FL', '------- ----- ----- 010 ----- 0000111', tags=["load"]),
            R5('fsw',       'FS', '------- ----- ----- 010 ----- 0100111'),

            R5('fmadd.s',   'R4U','-----00 ----- ----- --- ----- 1000011', tags=['fmadd']),
            R5('fmsub.s',   'R4U','-----00 ----- ----- --- ----- 1000111', tags=['fmadd']),
            R5('fnmsub.s',  'R4U','-----00 ----- ----- --- ----- 1001011', tags=['fmadd']),
            R5('fnmadd.s',  'R4U','-----00 ----- ----- --- ----- 1001111', tags=['fmadd']),

            R5('fadd.s',    'RF', '0000000 ----- ----- --- ----- 1010011', tags=['fadd']),
            R5('fsub.s',    'RF', '0000100 ----- ----- --- ----- 1010011', tags=['fadd']),
            R5('fmul.s',    'RF', '0001000 ----- ----- --- ----- 1010011', tags=['fmul']),
            R5('fdiv.s',    'RF', '0001100 ----- ----- --- ----- 1010011', tags=['fdiv']),
            R5('fsqrt.s',  'R2F3','0101100 00000 ----- --- ----- 1010011', tags=['fdiv']),

            R5('fsgnj.s',   'RF', '0010000 ----- ----- 000 ----- 1010011', tags=['fconv']),
            R5('fsgnjn.s',  'RF', '0010000 ----- ----- 001 ----- 1010011', tags=['fconv']),
            R5('fsgnjx.s',  'RF', '0010000 ----- ----- 010 ----- 1010011', tags=['fconv']),

            R5('fmin.s',    'RF', '0010100 ----- ----- 000 ----- 1010011', tags=['fconv']),
            R5('fmax.s',    'RF', '0010100 ----- ----- 001 ----- 1010011', tags=['fconv']),

            R5('feq.s',    'RF2', '1010000 ----- ----- 010 ----- 1010011'),
            R5('flt.s',    'RF2', '1010000 ----- ----- 001 ----- 1010011'),
            R5('fle.s',    'RF2', '1010000 ----- ----- 000 ----- 1010011'),

            R5('fcvt.w.s', 'R2F1','1100000 00000 ----- --- ----- 1010011', tags=['fconv']),
            R5('fcvt.wu.s','R2F1','1100000 00001 ----- --- ----- 1010011', tags=['fconv']),
            R5('fcvt.s.w', 'R2F2','1101000 00000 ----- --- ----- 1010011', tags=['fconv']),
            R5('fcvt.s.wu','R2F2','1101000 00001 ----- --- ----- 1010011', tags=['fconv']),

            R5('fmv.x.s',   'R3F','1110000 00000 ----- 000 ----- 1010011'),
            R5('fclass.s',  'R3F','1110000 00000 ----- 001 ----- 1010011'),
            R5('fmv.s.x',  'R3F2','1111000 00000 ----- 000 ----- 1010011'),

            # If RV64F supported
            R5('fcvt.l.s', 'R2F1','1100000 00010 ----- --- ----- 1010011', tags=['fconv'], isa_tags=['rv64f']),
            R5('fcvt.lu.s','R2F1','1100000 00011 ----- --- ----- 1010011', tags=['fconv'], isa_tags=['rv64f']),
            R5('fcvt.s.l', 'R2F2','1101000 00010 ----- --- ----- 1010011', tags=['fconv'], isa_tags=['rv64f']),
            R5('fcvt.s.lu','R2F2','1101000 00011 ----- --- ----- 1010011', tags=['fconv'], isa_tags=['rv64f']),
        ])

class Rv32d(IsaSubset):
    
    def __init__(self):
        super().__init__(name='d', instrs=[
            R5('fld',       'FL', '------- ----- ----- 011 ----- 0000111', tags=["load"]),
            R5('fsd',       'FS', '------- ----- ----- 011 ----- 0100111'),

            R5('fmadd.d',   'R4U','-----01 ----- ----- --- ----- 1000011', tags=['fmadd']),
            R5('fmsub.d',   'R4U','-----01 ----- ----- --- ----- 1000111', tags=['fmadd']),
            R5('fnmsub.d',  'R4U','-----01 ----- ----- --- ----- 1001011', tags=['fmadd']),
            R5('fnmadd.d',  'R4U','-----01 ----- ----- --- ----- 1001111', tags=['fmadd']),

            R5('fadd.d',    'RF', '0000001 ----- ----- --- ----- 1010011', tags=['fadd']),
            R5('fsub.d',    'RF', '0000101 ----- ----- --- ----- 1010011', tags=['fadd']),
            R5('fmul.d',    'RF', '0001001 ----- ----- --- ----- 1010011', tags=['fmul']),
            R5('fdiv.d',    'RF', '0001101 ----- ----- --- ----- 1010011', tags=['fdiv']),
            R5('fsqrt.d',  'R2F3','0101101 00000 ----- --- ----- 1010011', tags=['fdiv']),

            R5('fsgnj.d',   'RF', '0010001 ----- ----- 000 ----- 1010011', tags=['fconv']),
            R5('fsgnjn.d',  'RF', '0010001 ----- ----- 001 ----- 1010011', tags=['fconv']),
            R5('fsgnjx.d',  'RF', '0010001 ----- ----- 010 ----- 1010011', tags=['fconv']),

            R5('fmin.d',    'RF', '0010101 ----- ----- 000 ----- 1010011', tags=['fconv']),
            R5('fmax.d',    'RF', '0010101 ----- ----- 001 ----- 1010011', tags=['fconv']),

            R5('fcvt.s.d', 'R2F3','0100000 00001 ----- --- ----- 1010011', tags=['fconv']),
            R5('fcvt.d.s', 'R2F3','0100001 00000 ----- --- ----- 1010011', tags=['fconv']),

            R5('feq.d',    'RF2', '1010001 ----- ----- 010 ----- 1010011'),
            R5('flt.d',    'RF2', '1010001 ----- ----- 001 ----- 1010011'),
            R5('fle.d',    'RF2', '1010001 ----- ----- 000 ----- 1010011'),

            R5('fcvt.w.d', 'R2F1','1100001 00000 ----- --- ----- 1010011', tags=['fconv']),
            R5('fcvt.wu.d','R2F1','1100001 00001 ----- --- ----- 1010011', tags=['fconv']),
            R5('fcvt.d.w', 'R2F2','1101001 00000 ----- --- ----- 1010011', tags=['fconv']),
            R5('fcvt.d.wu','R2F2','1101001 00001 ----- --- ----- 1010011', tags=['fconv']),

            R5('fclass.d',  'R3F','1110001 00000 ----- 001 ----- 1010011'),

            # # If RV64F supported
            R5('fcvt.l.d', 'R2F1','1100001 00010 ----- --- ----- 1010011', tags=['fconv'], isa_tags=['rv64f']),
            R5('fcvt.lu.d','R2F1','1100001 00011 ----- --- ----- 1010011', tags=['fconv'], isa_tags=['rv64f']),
            R5('fmv.x.d',   'R3F','1110001 00000 ----- 000 ----- 1010011'),
            R5('fcvt.d.l', 'R2F2','1101001 00010 ----- --- ----- 1010011', tags=['fconv'], isa_tags=['rv64f']),
            R5('fcvt.d.lu','R2F2','1101001 00011 ----- --- ----- 1010011', tags=['fconv'], isa_tags=['rv64f']),
            R5('fmv.d.x',  'R3F2','1111001 00000 ----- 000 ----- 1010011'),
        ])

class Xf16(IsaSubset):
    
    def __init__(self):
        super().__init__(name='f16', instrs=[

            R5('flh',       'FL', '------- ----- ----- 001 ----- 0000111', tags=["load"]),
            R5('fsh',       'FS', '------- ----- ----- 001 ----- 0100111'),

            R5('fmadd.h',   'R4U','-----10 ----- ----- --- ----- 1000011', tags=['sfmadd']),
            R5('fmsub.h',   'R4U','-----10 ----- ----- --- ----- 1000111', tags=['sfmadd']),
            R5('fnmsub.h',  'R4U','-----10 ----- ----- --- ----- 1001011', tags=['sfmadd']),
            R5('fnmadd.h',  'R4U','-----10 ----- ----- --- ----- 1001111', tags=['sfmadd']),

            R5('fadd.h',    'RF', '0000010 ----- ----- --- ----- 1010011', tags=['sfadd']),
            R5('fsub.h',    'RF', '0000110 ----- ----- --- ----- 1010011', tags=['sfadd']),
            R5('fmul.h',    'RF', '0001010 ----- ----- --- ----- 1010011', tags=['sfmul']),
            R5('fdiv.h',    'RF', '0001110 ----- ----- --- ----- 1010011', tags=['sfdiv']),
            R5('fsqrt.h',  'R2F3','0101110 00000 ----- --- ----- 1010011', tags=['sfdiv']),

            R5('fsgnj.h',   'RF', '0010010 ----- ----- 000 ----- 1010011', tags=['sfconv']),
            R5('fsgnjn.h',  'RF', '0010010 ----- ----- 001 ----- 1010011', tags=['sfconv']),
            R5('fsgnjx.h',  'RF', '0010010 ----- ----- 010 ----- 1010011', tags=['sfconv']),

            R5('fmin.h',    'RF', '0010110 ----- ----- 000 ----- 1010011', tags=['sfconv']),
            R5('fmax.h',    'RF', '0010110 ----- ----- 001 ----- 1010011', tags=['sfconv']),

            R5('feq.h',    'RF2', '1010010 ----- ----- 010 ----- 1010011', tags=['sfother']),
            R5('flt.h',    'RF2', '1010010 ----- ----- 001 ----- 1010011', tags=['sfother']),
            R5('fle.h',    'RF2', '1010010 ----- ----- 000 ----- 1010011', tags=['sfother']),

            R5('fcvt.w.h', 'R2F1','1100010 00000 ----- --- ----- 1010011', tags=['sfconv']),
            R5('fcvt.wu.h','R2F1','1100010 00001 ----- --- ----- 1010011', tags=['sfconv']),
            R5('fcvt.h.w', 'R2F2','1101010 00000 ----- --- ----- 1010011', tags=['sfconv']),
            R5('fcvt.h.wu','R2F2','1101010 00001 ----- --- ----- 1010011', tags=['sfconv']),

            R5('fmv.x.h',   'R3F','1110010 00000 ----- 000 ----- 1010011', tags=['sfother']),
            R5('fclass.h',  'R3F','1110010 00000 ----- 001 ----- 1010011', tags=['sfother']),
            R5('fmv.h.x',  'R3F2','1111010 00000 ----- 000 ----- 1010011', tags=['sfother']),

            # If RV64Xf16 supported
            R5('fcvt.l.h', 'R2F1','1100010 00010 ----- --- ----- 1010011', tags=['sfconv'], isa_tags=['rv64f16']),
            R5('fcvt.lu.h','R2F1','1100010 00011 ----- --- ----- 1010011', tags=['sfconv'], isa_tags=['rv64f16']),
            R5('fcvt.h.l', 'R2F2','1101010 00010 ----- --- ----- 1010011', tags=['sfconv'], isa_tags=['rv64f16']),
            R5('fcvt.h.lu','R2F2','1101010 00011 ----- --- ----- 1010011', tags=['sfconv'], isa_tags=['rv64f16']),

            # If F also supported
            R5('fcvt.s.h', 'R2F3','0100000 00010 ----- 000 ----- 1010011', tags=['sfconv'], isa_tags=['f16f']),
            R5('fcvt.h.s', 'R2F3','0100010 00000 ----- --- ----- 1010011', tags=['sfconv'], isa_tags=['f16f']),

            # # If D also supported
            # R5('fcvt.d.h', 'R2F3','0100001 00010 ----- 000 ----- 1010011', tags=['sfconv'], isa_tags=['f16d']),
            # R5('fcvt.h.d', 'R2F3','0100010 00001 ----- --- ----- 1010011', tags=['sfconv'], isa_tags=['f16d']),
        ])

class Xf16alt(IsaSubset):
    
    def __init__(self):
        super().__init__(name='f16alt', instrs=[
            R5('fmadd.ah',   'R4U','-----10 ----- ----- 101 ----- 1000011', tags=['sfmadd']),
            R5('fmsub.ah',   'R4U','-----10 ----- ----- 101 ----- 1000111', tags=['sfmadd']),
            R5('fnmsub.ah',  'R4U','-----10 ----- ----- 101 ----- 1001011', tags=['sfmadd']),
            R5('fnmadd.ah',  'R4U','-----10 ----- ----- 101 ----- 1001111', tags=['sfmadd']),

            R5('fadd.ah',    'RF', '0000010 ----- ----- 101 ----- 1010011', tags=['sfadd']),
            R5('fsub.ah',    'RF', '0000110 ----- ----- 101 ----- 1010011', tags=['sfadd']),
            R5('fmul.ah',    'RF', '0001010 ----- ----- 101 ----- 1010011', tags=['sfmul']),
            R5('fdiv.ah',    'RF', '0001110 ----- ----- 101 ----- 1010011', tags=['sfdiv']),
            R5('fsqrt.ah',  'R2F3','0101110 00000 ----- 101 ----- 1010011', tags=['sfdiv']),

            R5('fsgnj.ah',   'RF', '0010010 ----- ----- 100 ----- 1010011', tags=['sfconv']),
            R5('fsgnjn.ah',  'RF', '0010010 ----- ----- 101 ----- 1010011', tags=['sfconv']),
            R5('fsgnjx.ah',  'RF', '0010010 ----- ----- 110 ----- 1010011', tags=['sfconv']),

            R5('fmin.ah',    'RF', '0010110 ----- ----- 100 ----- 1010011', tags=['sfconv']),
            R5('fmax.ah',    'RF', '0010110 ----- ----- 101 ----- 1010011', tags=['sfconv']),

            R5('feq.ah',    'RF2', '1010010 ----- ----- 110 ----- 1010011', tags=['sfother']),
            R5('flt.ah',    'RF2', '1010010 ----- ----- 101 ----- 1010011', tags=['sfother']),
            R5('fle.ah',    'RF2', '1010010 ----- ----- 100 ----- 1010011', tags=['sfother']),

            R5('fcvt.w.ah', 'R2F1','1100010 00000 ----- 101 ----- 1010011', tags=['sfconv']),
            R5('fcvt.wu.ah','R2F1','1100010 00001 ----- 101 ----- 1010011', tags=['sfconv']),
            R5('fcvt.ah.w', 'R2F2','1101010 00000 ----- 101 ----- 1010011', tags=['sfconv']),
            R5('fcvt.ah.wu','R2F2','1101010 00001 ----- 101 ----- 1010011', tags=['sfconv']),

            R5('fmv.x.ah',   'R3F','1110010 00000 ----- 100 ----- 1010011', tags=['sfother']),
            R5('fclass.ah',  'R3F','1110010 00000 ----- 101 ----- 1010011', tags=['sfother']),
            R5('fmv.ah.x',  'R3F2','1111010 00000 ----- 100 ----- 1010011', tags=['sfother']),

            # If RV64Xf16alt supported
            R5('fcvt.l.ah', 'R2F1','1100010 00010 ----- 101 ----- 1010011', tags=['sfconv'], isa_tags=['rv64f16alt']),
            R5('fcvt.lu.ah','R2F1','1100010 00011 ----- 101 ----- 1010011', tags=['sfconv'], isa_tags=['rv64f16alt']),
            R5('fcvt.ah.l', 'R2F2','1101010 00010 ----- 101 ----- 1010011', tags=['sfconv'], isa_tags=['rv64f16alt']),
            R5('fcvt.ah.lu','R2F2','1101010 00011 ----- 101 ----- 1010011', tags=['sfconv'], isa_tags=['rv64f16alt']),

            # If F also supported
            R5('fcvt.s.ah', 'R2F3','0100000 00110 ----- 000 ----- 1010011', tags=['sfconv'], isa_tags=['f16altf']),
            R5('fcvt.ah.s', 'R2F3','0100010 00000 ----- 101 ----- 1010011', tags=['sfconv'], isa_tags=['f16altf']),

            # # If D also supported
            # R5('fcvt.d.ah', 'R2F3','0100001 00110 ----- 000 ----- 1010011', tags=['sfconv'], isa_tags=['f16altd']),
            # R5('fcvt.ah.d', 'R2F3','0100010 00001 ----- 101 ----- 1010011', tags=['sfconv'], isa_tags=['f16altd']),

            # If Xf16 also supported
            R5('fcvt.h.ah', 'R2F3','0100010 00110 ----- --- ----- 1010011', tags=['sfconv'], isa_tags=['f16altf16']),
            R5('fcvt.ah.h', 'R2F3','0100010 00010 ----- 101 ----- 1010011', tags=['sfconv'], isa_tags=['f16altf16']),
        ])

class Xf8(IsaSubset):
    
    def __init__(self):
        super().__init__(name='f8', instrs=[
            R5('flb',       'FL', '------- ----- ----- 000 ----- 0000111', tags=["load"]),
            R5('fsb',       'FS', '------- ----- ----- 000 ----- 0100111'),

            R5('fmadd.b',   'R4U','-----11 ----- ----- --- ----- 1000011', tags=['sfmadd']),
            R5('fmsub.b',   'R4U','-----11 ----- ----- --- ----- 1000111', tags=['sfmadd']),
            R5('fnmsub.b',  'R4U','-----11 ----- ----- --- ----- 1001011', tags=['sfmadd']),
            R5('fnmadd.b',  'R4U','-----11 ----- ----- --- ----- 1001111', tags=['sfmadd']),

            R5('fadd.b',    'RF', '0000011 ----- ----- --- ----- 1010011', tags=['sfadd']),
            R5('fsub.b',    'RF', '0000111 ----- ----- --- ----- 1010011', tags=['sfadd']),
            R5('fmul.b',    'RF', '0001011 ----- ----- --- ----- 1010011', tags=['sfmul']),
            R5('fdiv.b',    'RF', '0001111 ----- ----- --- ----- 1010011', tags=['sfdiv']),
            R5('fsqrt.b',  'R2F3','0101111 00000 ----- --- ----- 1010011', tags=['sfdiv']),

            R5('fsgnj.b',   'RF', '0010011 ----- ----- 000 ----- 1010011', tags=['sfconv']),
            R5('fsgnjn.b',  'RF', '0010011 ----- ----- 001 ----- 1010011', tags=['sfconv']),
            R5('fsgnjx.b',  'RF', '0010011 ----- ----- 010 ----- 1010011', tags=['sfconv']),

            R5('fmin.b',    'RF', '0010111 ----- ----- 000 ----- 1010011', tags=['sfconv']),
            R5('fmax.b',    'RF', '0010111 ----- ----- 001 ----- 1010011', tags=['sfconv']),

            R5('feq.b',    'RF2', '1010011 ----- ----- 010 ----- 1010011', tags=['sfother']),
            R5('flt.b',    'RF2', '1010011 ----- ----- 001 ----- 1010011', tags=['sfother']),
            R5('fle.b',    'RF2', '1010011 ----- ----- 000 ----- 1010011', tags=['sfother']),

            R5('fcvt.w.b', 'R2F1','1100011 00000 ----- --- ----- 1010011', tags=['sfconv']),
            R5('fcvt.wu.b','R2F1','1100011 00001 ----- --- ----- 1010011', tags=['sfconv']),
            R5('fcvt.b.w', 'R2F2','1101011 00000 ----- --- ----- 1010011', tags=['sfconv']),
            R5('fcvt.b.wu','R2F2','1101011 00001 ----- --- ----- 1010011', tags=['sfconv']),

            R5('fmv.x.b',   'R3F','1110011 00000 ----- 000 ----- 1010011', tags=['sfother']),
            R5('fclass.b',  'R3F','1110011 00000 ----- 001 ----- 1010011', tags=['sfother']),
            R5('fmv.b.x',  'R3F2','1111011 00000 ----- 000 ----- 1010011', tags=['sfother']),

            # If RV64Xf8 supported
            R5('fcvt.l.b', 'R2F1','1100011 00010 ----- --- ----- 1010011', tags=['sfconv'], isa_tags=['rv64f8']),
            R5('fcvt.lu.b','R2F1','1100011 00011 ----- --- ----- 1010011', tags=['sfconv'], isa_tags=['rv64f8']),
            R5('fcvt.b.l', 'R2F2','1101011 00010 ----- --- ----- 1010011', tags=['sfconv'], isa_tags=['rv64f8']),
            R5('fcvt.b.lu','R2F2','1101011 00011 ----- --- ----- 1010011', tags=['sfconv'], isa_tags=['rv64f8']),

            # If F also supported
            R5('fcvt.s.b', 'R2F3','0100000 00011 ----- 000 ----- 1010011', tags=['sfconv'], isa_tags=['f8f']),
            R5('fcvt.b.s', 'R2F3','0100011 00000 ----- --- ----- 1010011', tags=['sfconv'], isa_tags=['f8f']),

            # # If D also supported
            # R5('fcvt.d.b', 'R2F3','0100001 00011 ----- 000 ----- 1010011', tags=['sfconv'], isa_tags=['f8d']),
            # R5('fcvt.b.d', 'R2F3','0100011 00001 ----- --- ----- 1010011', tags=['sfconv'], isa_tags=['f8d']),

            # If Xf16 also supported
            R5('fcvt.h.b', 'R2F3','0100010 00011 ----- 000 ----- 1010011', tags=['sfconv'], isa_tags=['f8f16']),
            R5('fcvt.b.h', 'R2F3','0100011 00010 ----- --- ----- 1010011', tags=['sfconv'], isa_tags=['f8f16']),

            # If Xf16alt also supported
            R5('fcvt.ah.b','R2F3','0100010 00011 ----- 101 ----- 1010011', tags=['sfconv'], isa_tags=['f8f16alt']),
            R5('fcvt.b.ah','R2F3','0100011 00110 ----- --- ----- 1010011', tags=['sfconv'], isa_tags=['f8f16alt']),
        ])


#
# Vectorial Floats
#

class Xfvec(IsaSubset):
    
    def __init__(self):
        super().__init__(name='fvec', instrs=[
        #
        # For F
        #
            # R5('vfadd.s',    'RVF', '1000001 ----- ----- 000 ----- 0110011', tags=['fadd'], isa_tags=['f32vec']),
            # R5('vfadd.r.s',  'RVF', '1000001 ----- ----- 100 ----- 0110011', tags=['fadd'], isa_tags=['f32vec']),
            # R5('vfsub.s',    'RVF', '1000010 ----- ----- 000 ----- 0110011', tags=['fadd'], isa_tags=['f32vec']),
            # R5('vfsub.r.s',  'RVF', '1000010 ----- ----- 100 ----- 0110011', tags=['fadd'], isa_tags=['f32vec']),
            # R5('vfmul.s',    'RVF', '1000011 ----- ----- 000 ----- 0110011', tags=['fmul'], isa_tags=['f32vec']),
            # R5('vfmul.r.s',  'RVF', '1000011 ----- ----- 100 ----- 0110011', tags=['fmul'], isa_tags=['f32vec']),
            # R5('vfdiv.s',    'RVF', '1000100 ----- ----- 000 ----- 0110011', tags=['fdiv'], isa_tags=['f32vec']),
            # R5('vfdiv.r.s',  'RVF', '1000100 ----- ----- 100 ----- 0110011', tags=['fdiv'], isa_tags=['f32vec']),

            # R5('vfmin.s',    'RVF', '1000101 ----- ----- 000 ----- 0110011', tags=['fconv'], isa_tags=['f32vec']),
            # R5('vfmin.r.s',  'RVF', '1000101 ----- ----- 100 ----- 0110011', tags=['fconv'], isa_tags=['f32vec']),
            # R5('vfmax.s',    'RVF', '1000110 ----- ----- 000 ----- 0110011', tags=['fconv'], isa_tags=['f32vec']),
            # R5('vfmax.r.s',  'RVF', '1000110 ----- ----- 100 ----- 0110011', tags=['fconv'], isa_tags=['f32vec']),

            # R5('vfsqrt.s',   'RVF2','1000111 00000 ----- 000 ----- 0110011', tags=['fdiv'], isa_tags=['f32vec']),

            # R5('vfmac.s',    'RVF4','1001000 ----- ----- 000 ----- 0110011', tags=['fmadd'], isa_tags=['f32vec']),
            # R5('vfmac.r.s',  'RVF4','1001000 ----- ----- 100 ----- 0110011', tags=['fmadd'], isa_tags=['f32vec']),
            # R5('vfmre.s',    'RVF4','1001001 ----- ----- 000 ----- 0110011', tags=['fmadd'], isa_tags=['f32vec']),
            # R5('vfmre.r.s',  'RVF4','1001001 ----- ----- 100 ----- 0110011', tags=['fmadd'], isa_tags=['f32vec']),

            # R5('vfclass.s', 'R2VF2','1001100 00001 ----- 000 ----- 0110011', tags=['fother'], isa_tags=['f32vec']),

            # R5('vfsgnj.r.s', 'RVF', '1001101 ----- ----- 000 ----- 0110011', tags=['fconv'], isa_tags=['f32vec']),
            # R5('vfsgnj.s',   'RVF', '1001101 ----- ----- 100 ----- 0110011', tags=['fconv'], isa_tags=['f32vec']),
            # R5('vfsgnjn.s',  'RVF', '1001110 ----- ----- 000 ----- 0110011', tags=['fconv'], isa_tags=['f32vec']),
            # R5('vfsgnjn.r.s','RVF', '1001110 ----- ----- 100 ----- 0110011', tags=['fconv'], isa_tags=['f32vec']),
            # R5('vfsgnjx.s',  'RVF', '1001111 ----- ----- 000 ----- 0110011', tags=['fconv'], isa_tags=['f32vec']),
            # R5('vfsgnjx.r.s','RVF', '1001111 ----- ----- 100 ----- 0110011', tags=['fconv'], isa_tags=['f32vec']),

            # R5('vfeq.s',    'R2VF', '1010000 ----- ----- 000 ----- 0110011', tags=['fother'], isa_tags=['f32vec']),
            # R5('vfeq.r.s',  'R2VF', '1010000 ----- ----- 100 ----- 0110011', tags=['fother'], isa_tags=['f32vec']),
            # R5('vfne.s',    'R2VF', '1010001 ----- ----- 000 ----- 0110011', tags=['fother'], isa_tags=['f32vec']),
            # R5('vfne.r.s',  'R2VF', '1010001 ----- ----- 100 ----- 0110011', tags=['fother'], isa_tags=['f32vec']),
            # R5('vflt.s',    'R2VF', '1010010 ----- ----- 000 ----- 0110011', tags=['fother'], isa_tags=['f32vec']),
            # R5('vflt.r.s',  'R2VF', '1010010 ----- ----- 100 ----- 0110011', tags=['fother'], isa_tags=['f32vec']),
            # R5('vfge.s',    'R2VF', '1010011 ----- ----- 000 ----- 0110011', tags=['fother'], isa_tags=['f32vec']),
            # R5('vfge.r.s',  'R2VF', '1010011 ----- ----- 100 ----- 0110011', tags=['fother'], isa_tags=['f32vec']),
            # R5('vfle.s',    'R2VF', '1010100 ----- ----- 000 ----- 0110011', tags=['fother'], isa_tags=['f32vec']),
            # R5('vfle.r.s',  'R2VF', '1010100 ----- ----- 100 ----- 0110011', tags=['fother'], isa_tags=['f32vec']),
            # R5('vfgt.s',    'R2VF', '1010101 ----- ----- 000 ----- 0110011', tags=['fother'], isa_tags=['f32vec']),
            # R5('vfgt.r.s',  'R2VF', '1010101 ----- ----- 100 ----- 0110011', tags=['fother'], isa_tags=['f32vec']),

            # R5('vfcpka.s.s', 'RVF', '1011000 ----- ----- 000 ----- 0110011', tags=['fother'], isa_tags=['f32vec']),
            # # R5('vfcpka.s.d', 'RVF', '1011010 ----- ----- 000 ----- 0110011', tags=['fother'], isa_tags=['f32vec']),

            # # Unless RV32D supported
            # R5('vfmv.x.s',   'R3F', '1001100 00000 ----- 000 ----- 0110011', tags=['fother'], isa_tags=['f32vecno32d']),
            # R5('vfmv.s.x',   'R3F2','1001100 00000 ----- 100 ----- 0110011', tags=['fother'], isa_tags=['f32vecno32d']),

            # R5('vfcvt.x.s',  'R3F', '1001100 00010 ----- 000 ----- 0110011', tags=['fconv'], isa_tags=['f32vecno32d']),
            # R5('vfcvt.xu.s', 'R3F', '1001100 00010 ----- 100 ----- 0110011', tags=['fconv'], isa_tags=['f32vecno32d']),
            # R5('vfcvt.s.x',  'R3F2','1001100 00011 ----- 000 ----- 0110011', tags=['fconv'], isa_tags=['f32vecno32d']),
            # R5('vfcvt.s.xu', 'R3F2','1001100 00011 ----- 100 ----- 0110011', tags=['fconv'], isa_tags=['f32vecno32d']),

        #
        # For Xf16
        #
            R5('vfadd.h',    'RVF', '1000001 ----- ----- 010 ----- 0110011', tags=['fadd'], isa_tags=['f16vec']),
            R5('vfadd.r.h',  'RVF', '1000001 ----- ----- 110 ----- 0110011', tags=['fadd'], isa_tags=['f16vec']),
            R5('vfsub.h',    'RVF', '1000010 ----- ----- 010 ----- 0110011', tags=['fadd'], isa_tags=['f16vec']),
            R5('vfsub.r.h',  'RVF', '1000010 ----- ----- 110 ----- 0110011', tags=['fadd'], isa_tags=['f16vec']),
            R5('vfmul.h',    'RVF', '1000011 ----- ----- 010 ----- 0110011', tags=['fmul'], isa_tags=['f16vec']),
            R5('vfmul.r.h',  'RVF', '1000011 ----- ----- 110 ----- 0110011', tags=['fmul'], isa_tags=['f16vec']),
            R5('vfdiv.h',    'RVF', '1000100 ----- ----- 010 ----- 0110011', tags=['fdiv'], isa_tags=['f16vec']),
            R5('vfdiv.r.h',  'RVF', '1000100 ----- ----- 110 ----- 0110011', tags=['fdiv'], isa_tags=['f16vec']),

            R5('vfmin.h',    'RVF', '1000101 ----- ----- 010 ----- 0110011', tags=['fconv'], isa_tags=['f16vec']),
            R5('vfmin.r.h',  'RVF', '1000101 ----- ----- 110 ----- 0110011', tags=['fconv'], isa_tags=['f16vec']),
            R5('vfmax.h',    'RVF', '1000110 ----- ----- 010 ----- 0110011', tags=['fconv'], isa_tags=['f16vec']),
            R5('vfmax.r.h',  'RVF', '1000110 ----- ----- 110 ----- 0110011', tags=['fconv'], isa_tags=['f16vec']),

            R5('vfsqrt.h',   'RVF2','1000111 00000 ----- 010 ----- 0110011', tags=['fdiv'], isa_tags=['f16vec']),

            R5('vfmac.h',    'RVF4','1001000 ----- ----- 010 ----- 0110011', tags=['fmadd'], isa_tags=['f16vec']),
            R5('vfmac.r.h',  'RVF4','1001000 ----- ----- 110 ----- 0110011', tags=['fmadd'], isa_tags=['f16vec']),
            R5('vfmre.h',    'RVF4','1001001 ----- ----- 010 ----- 0110011', tags=['fmadd'], isa_tags=['f16vec']),
            R5('vfmre.r.h',  'RVF4','1001001 ----- ----- 110 ----- 0110011', tags=['fmadd'], isa_tags=['f16vec']),

            R5('vfclass.h', 'R2VF2','1001100 00001 ----- 010 ----- 0110011', tags=['fother'], isa_tags=['f16vec']),

            R5('vfsgnj.h',   'RVF', '1001101 ----- ----- 010 ----- 0110011', tags=['fconv'], isa_tags=['f16vec']),
            R5('vfsgnj.r.h', 'RVF', '1001101 ----- ----- 110 ----- 0110011', tags=['fconv'], isa_tags=['f16vec']),
            R5('vfsgnjn.h',  'RVF', '1001110 ----- ----- 010 ----- 0110011', tags=['fconv'], isa_tags=['f16vec']),
            R5('vfsgnjn.r.h','RVF', '1001110 ----- ----- 110 ----- 0110011', tags=['fconv'], isa_tags=['f16vec']),
            R5('vfsgnjx.h',  'RVF', '1001111 ----- ----- 010 ----- 0110011', tags=['fconv'], isa_tags=['f16vec']),
            R5('vfsgnjx.r.h','RVF', '1001111 ----- ----- 110 ----- 0110011', tags=['fconv'], isa_tags=['f16vec']),

            R5('vfeq.h',    'R2VF', '1010000 ----- ----- 010 ----- 0110011', tags=['fother'], isa_tags=['f16vec']),
            R5('vfeq.r.h',  'R2VF', '1010000 ----- ----- 110 ----- 0110011', tags=['fother'], isa_tags=['f16vec']),
            R5('vfne.h',    'R2VF', '1010001 ----- ----- 010 ----- 0110011', tags=['fother'], isa_tags=['f16vec']),
            R5('vfne.r.h',  'R2VF', '1010001 ----- ----- 110 ----- 0110011', tags=['fother'], isa_tags=['f16vec']),
            R5('vflt.h',    'R2VF', '1010010 ----- ----- 010 ----- 0110011', tags=['fother'], isa_tags=['f16vec']),
            R5('vflt.r.h',  'R2VF', '1010010 ----- ----- 110 ----- 0110011', tags=['fother'], isa_tags=['f16vec']),
            R5('vfge.h',    'R2VF', '1010011 ----- ----- 010 ----- 0110011', tags=['fother'], isa_tags=['f16vec']),
            R5('vfge.r.h',  'R2VF', '1010011 ----- ----- 110 ----- 0110011', tags=['fother'], isa_tags=['f16vec']),
            R5('vfle.h',    'R2VF', '1010100 ----- ----- 010 ----- 0110011', tags=['fother'], isa_tags=['f16vec']),
            R5('vfle.r.h',  'R2VF', '1010100 ----- ----- 110 ----- 0110011', tags=['fother'], isa_tags=['f16vec']),
            R5('vfgt.h',    'R2VF', '1010101 ----- ----- 010 ----- 0110011', tags=['fother'], isa_tags=['f16vec']),
            R5('vfgt.r.h',  'R2VF', '1010101 ----- ----- 110 ----- 0110011', tags=['fother'], isa_tags=['f16vec']),

            R5('vfcpka.h.s', 'R2VF','1011000 ----- ----- 010 ----- 0110011', tags=['fother'], isa_tags=['f16vec']),

            # Unless RV32D supported
            R5('vfmv.x.h',   'R3F', '1001100 00000 ----- 010 ----- 0110011', tags=['fother'], isa_tags=['f16vecno32d']),
            R5('vfmv.h.x',   'R3F2','1001100 00000 ----- 110 ----- 0110011', tags=['fother'], isa_tags=['f16vecno32d']),

            R5('vfcvt.x.h',  'R3F', '1001100 00010 ----- 010 ----- 0110011', tags=['fconv'], isa_tags=['f16vecno32d']),
            R5('vfcvt.xu.h', 'R3F', '1001100 00010 ----- 110 ----- 0110011', tags=['fconv'], isa_tags=['f16vecno32d']),
            R5('vfcvt.h.x',  'R3F2','1001100 00011 ----- 010 ----- 0110011', tags=['fconv'], isa_tags=['f16vecno32d']),
            R5('vfcvt.h.xu', 'R3F2','1001100 00011 ----- 110 ----- 0110011', tags=['fconv'], isa_tags=['f16vecno32d']),

            # # If D extension also supported (implies FLEN>=64)
            # R5('vfcvt.s.h',  'RVF2','1001100 00110 ----- 000 ----- 0110011', tags=['fconv'], isa_tags=['f16vecd']),
            # R5('vfcvt.h.s',  'RVF2','1001100 00100 ----- 010 ----- 0110011', tags=['fconv'], isa_tags=['f16vecd']),

            # R5('vfcpkb.h.s', 'RVF4','1011000 ----- ----- 110 ----- 0110011', tags=['fother'], isa_tags=['f16vecd']),
            # R5('vfcpka.h.d', 'RVF4','1011010 ----- ----- 010 ----- 0110011', tags=['fother'], isa_tags=['f16vecd']),
            # R5('vfcpkb.h.d', 'RVF4','1011010 ----- ----- 110 ----- 0110011', tags=['fother'], isa_tags=['f16vecd']),

        #
        # For Xf16alt
        #
            R5('vfadd.ah',    'RVF', '1000001 ----- ----- 001 ----- 0110011', tags=['fadd'], isa_tags=['f16altvec']),
            R5('vfadd.r.ah',  'RVF', '1000001 ----- ----- 101 ----- 0110011', tags=['fadd'], isa_tags=['f16altvec']),
            R5('vfsub.ah',    'RVF', '1000010 ----- ----- 001 ----- 0110011', tags=['fadd'], isa_tags=['f16altvec']),
            R5('vfsub.r.ah',  'RVF', '1000010 ----- ----- 101 ----- 0110011', tags=['fadd'], isa_tags=['f16altvec']),
            R5('vfmul.ah',    'RVF', '1000011 ----- ----- 001 ----- 0110011', tags=['fmul'], isa_tags=['f16altvec']),
            R5('vfmul.r.ah',  'RVF', '1000011 ----- ----- 101 ----- 0110011', tags=['fmul'], isa_tags=['f16altvec']),
            R5('vfdiv.ah',    'RVF', '1000100 ----- ----- 001 ----- 0110011', tags=['fdiv'], isa_tags=['f16altvec']),
            R5('vfdiv.r.ah',  'RVF', '1000100 ----- ----- 101 ----- 0110011', tags=['fdiv'], isa_tags=['f16altvec']),

            R5('vfmin.ah',    'RVF', '1000101 ----- ----- 001 ----- 0110011', tags=['fconv'], isa_tags=['f16altvec']),
            R5('vfmin.r.ah',  'RVF', '1000101 ----- ----- 101 ----- 0110011', tags=['fconv'], isa_tags=['f16altvec']),
            R5('vfmax.ah',    'RVF', '1000110 ----- ----- 001 ----- 0110011', tags=['fconv'], isa_tags=['f16altvec']),
            R5('vfmax.r.ah',  'RVF', '1000110 ----- ----- 101 ----- 0110011', tags=['fconv']),

            R5('vfsqrt.ah',   'RVF2','1000111 00000 ----- 001 ----- 0110011', tags=['fdiv'], isa_tags=['f16altvec']),

            R5('vfmac.ah',    'RVF4','1001000 ----- ----- 001 ----- 0110011', tags=['fmadd'], isa_tags=['f16altvec']),
            R5('vfmac.r.ah',  'RVF4','1001000 ----- ----- 101 ----- 0110011', tags=['fmadd'], isa_tags=['f16altvec']),
            R5('vfmre.ah',    'RVF4','1001001 ----- ----- 001 ----- 0110011', tags=['fmadd'], isa_tags=['f16altvec']),
            R5('vfmre.r.ah',  'RVF4','1001001 ----- ----- 101 ----- 0110011', tags=['fmadd'], isa_tags=['f16altvec']),

            R5('vfclass.ah', 'R2VF2','1001100 00001 ----- 001 ----- 0110011', tags=['fother'], isa_tags=['f16altvec']),

            R5('vfsgnj.r.ah', 'RVF', '1001101 ----- ----- 001 ----- 0110011', tags=['fconv'], isa_tags=['f16altvec']),
            R5('vfsgnj.ah',   'RVF', '1001101 ----- ----- 101 ----- 0110011', tags=['fconv'], isa_tags=['f16altvec']),
            R5('vfsgnjn.ah',  'RVF', '1001110 ----- ----- 001 ----- 0110011', tags=['fconv'], isa_tags=['f16altvec']),
            R5('vfsgnjn.r.ah','RVF', '1001110 ----- ----- 101 ----- 0110011', tags=['fconv'], isa_tags=['f16altvec']),
            R5('vfsgnjx.ah',  'RVF', '1001111 ----- ----- 001 ----- 0110011', tags=['fconv'], isa_tags=['f16altvec']),
            R5('vfsgnjx.r.ah','RVF', '1001111 ----- ----- 101 ----- 0110011', tags=['fconv']),

            R5('vfeq.ah',    'R2VF', '1010000 ----- ----- 001 ----- 0110011', tags=['fother'], isa_tags=['f16altvec']),
            R5('vfeq.r.ah',  'R2VF', '1010000 ----- ----- 101 ----- 0110011', tags=['fother'], isa_tags=['f16altvec']),
            R5('vfne.ah',    'R2VF', '1010001 ----- ----- 001 ----- 0110011', tags=['fother'], isa_tags=['f16altvec']),
            R5('vfne.r.ah',  'R2VF', '1010001 ----- ----- 101 ----- 0110011', tags=['fother'], isa_tags=['f16altvec']),
            R5('vflt.ah',    'R2VF', '1010010 ----- ----- 001 ----- 0110011', tags=['fother'], isa_tags=['f16altvec']),
            R5('vflt.r.ah',  'R2VF', '1010010 ----- ----- 101 ----- 0110011', tags=['fother'], isa_tags=['f16altvec']),
            R5('vfge.ah',    'R2VF', '1010011 ----- ----- 001 ----- 0110011', tags=['fother'], isa_tags=['f16altvec']),
            R5('vfge.r.ah',  'R2VF', '1010011 ----- ----- 101 ----- 0110011', tags=['fother'], isa_tags=['f16altvec']),
            R5('vfle.ah',    'R2VF', '1010100 ----- ----- 001 ----- 0110011', tags=['fother'], isa_tags=['f16altvec']),
            R5('vfle.r.ah',  'R2VF', '1010100 ----- ----- 101 ----- 0110011', tags=['fother'], isa_tags=['f16altvec']),
            R5('vfgt.ah',    'R2VF', '1010101 ----- ----- 001 ----- 0110011', tags=['fother'], isa_tags=['f16altvec']),
            R5('vfgt.r.ah',  'R2VF', '1010101 ----- ----- 101 ----- 0110011', tags=['fother']),

            R5('vfcpka.ah.s', 'R2VF','1011000 ----- ----- 001 ----- 0110011', tags=['fother'], isa_tags=['f16altvec']),

            # Unless RV32D supported
            R5('vfmv.x.ah',   'R3F', '1001100 00000 ----- 001 ----- 0110011', tags=['fother'], isa_tags=['f16altvecno32d']),
            R5('vfmv.ah.x',   'R3F2','1001100 00000 ----- 101 ----- 0110011', tags=['fother'], isa_tags=['f16altvecno32d']),

            R5('vfcvt.x.ah',  'R3F', '1001100 00010 ----- 001 ----- 0110011', tags=['fconv'], isa_tags=['f16altvecno32d']),
            R5('vfcvt.xu.ah', 'R3F', '1001100 00010 ----- 101 ----- 0110011', tags=['fconv'], isa_tags=['f16altvecno32d']),
            R5('vfcvt.ah.x',  'R3F2','1001100 00011 ----- 001 ----- 0110011', tags=['fconv'], isa_tags=['f16altvecno32d']),
            R5('vfcvt.ah.xu', 'R3F2','1001100 00011 ----- 101 ----- 0110011', tags=['fconv'], isa_tags=['f16altvecno32d']),

            # # If D extension also supported (implies FLEN>=64)
            # R5('vfcvt.s.ah',  'RVF2','1001100 00101 ----- 000 ----- 0110011', tags=['fconv'], isa_tags=['f16altvecd']),
            # R5('vfcvt.ah.s',  'RVF2','1001100 00100 ----- 001 ----- 0110011', tags=['fconv'], isa_tags=['f16altvecd']),

            # R5('vfcpkb.ah.s', 'RVF4','1011000 ----- ----- 101 ----- 0110011', tags=['fother'], isa_tags=['f16altvecd']),
            # R5('vfcpka.ah.d', 'RVF4','1011010 ----- ----- 001 ----- 0110011', tags=['fother'], isa_tags=['f16altvecd']),
            # R5('vfcpkb.ah.d', 'RVF4','1011010 ----- ----- 101 ----- 0110011', tags=['fother'], isa_tags=['f16altvecd']),

            # If Xf16 extension also supported
            R5('vfcvt.h.ah',  'RVF2','1001100 00101 ----- 010 ----- 0110011', tags=['fconv'], isa_tags=['f16altvecf16']),
            R5('vfcvt.ah.h',  'RVF2','1001100 00110 ----- 001 ----- 0110011', tags=['fconv'], isa_tags=['f16altvecf16']),

        #
        # For Xf8
        #
            R5('vfadd.b',    'RVF', '1000001 ----- ----- 011 ----- 0110011', tags=['fadd'], isa_tags=['f8vec']),
            R5('vfadd.r.b',  'RVF', '1000001 ----- ----- 111 ----- 0110011', tags=['fadd'], isa_tags=['f8vec']),
            R5('vfsub.b',    'RVF', '1000010 ----- ----- 011 ----- 0110011', tags=['fadd'], isa_tags=['f8vec']),
            R5('vfsub.r.b',  'RVF', '1000010 ----- ----- 111 ----- 0110011', tags=['fadd'], isa_tags=['f8vec']),
            R5('vfmul.b',    'RVF', '1000011 ----- ----- 011 ----- 0110011', tags=['fmul'], isa_tags=['f8vec']),
            R5('vfmul.r.b',  'RVF', '1000011 ----- ----- 111 ----- 0110011', tags=['fmul'], isa_tags=['f8vec']),
            R5('vfdiv.b',    'RVF', '1000100 ----- ----- 011 ----- 0110011', tags=['fdiv'], isa_tags=['f8vec']),
            R5('vfdiv.r.b',  'RVF', '1000100 ----- ----- 111 ----- 0110011', tags=['fdiv'], isa_tags=['f8vec']),

            R5('vfmin.b',    'RVF', '1000101 ----- ----- 011 ----- 0110011', tags=['fconv'], isa_tags=['f8vec']),
            R5('vfmin.r.b',  'RVF', '1000101 ----- ----- 111 ----- 0110011', tags=['fconv'], isa_tags=['f8vec']),
            R5('vfmax.b',    'RVF', '1000110 ----- ----- 011 ----- 0110011', tags=['fconv'], isa_tags=['f8vec']),
            R5('vfmax.r.b',  'RVF', '1000110 ----- ----- 111 ----- 0110011', tags=['fconv'], isa_tags=['f8vec']),

            R5('vfsqrt.b',   'RVF2','1000111 00000 ----- 011 ----- 0110011', tags=['fdiv'], isa_tags=['f8vec']),

            R5('vfmac.b',    'RVF4','1001000 ----- ----- 011 ----- 0110011', tags=['fmadd'], isa_tags=['f8vec']),
            R5('vfmac.r.b',  'RVF4','1001000 ----- ----- 111 ----- 0110011', tags=['fmadd'], isa_tags=['f8vec']),
            R5('vfmre.b',    'RVF4','1001001 ----- ----- 011 ----- 0110011', tags=['fmadd'], isa_tags=['f8vec']),
            R5('vfmre.r.b',  'RVF4','1001001 ----- ----- 111 ----- 0110011', tags=['fmadd'], isa_tags=['f8vec']),

            R5('vfclass.b', 'R2VF2','1001100 00001 ----- 011 ----- 0110011', tags=['fother'], isa_tags=['f8vec']),

            R5('vfsgnj.r.b', 'RVF', '1001101 ----- ----- 011 ----- 0110011', tags=['fconv'], isa_tags=['f8vec']),
            R5('vfsgnj.b',   'RVF', '1001101 ----- ----- 111 ----- 0110011', tags=['fconv'], isa_tags=['f8vec']),
            R5('vfsgnjn.b',  'RVF', '1001110 ----- ----- 011 ----- 0110011', tags=['fconv'], isa_tags=['f8vec']),
            R5('vfsgnjn.r.b','RVF', '1001110 ----- ----- 111 ----- 0110011', tags=['fconv'], isa_tags=['f8vec']),
            R5('vfsgnjx.b',  'RVF', '1001111 ----- ----- 011 ----- 0110011', tags=['fconv'], isa_tags=['f8vec']),
            R5('vfsgnjx.r.b','RVF', '1001111 ----- ----- 111 ----- 0110011', tags=['fconv'], isa_tags=['f8vec']),

            R5('vfeq.b',    'R2VF', '1010000 ----- ----- 011 ----- 0110011', tags=['fother'], isa_tags=['f8vec']),
            R5('vfeq.r.b',  'R2VF', '1010000 ----- ----- 111 ----- 0110011', tags=['fother'], isa_tags=['f8vec']),
            R5('vfne.b',    'R2VF', '1010001 ----- ----- 011 ----- 0110011', tags=['fother'], isa_tags=['f8vec']),
            R5('vfne.r.b',  'R2VF', '1010001 ----- ----- 111 ----- 0110011', tags=['fother'], isa_tags=['f8vec']),
            R5('vflt.b',    'R2VF', '1010010 ----- ----- 011 ----- 0110011', tags=['fother'], isa_tags=['f8vec']),
            R5('vflt.r.b',  'R2VF', '1010010 ----- ----- 111 ----- 0110011', tags=['fother'], isa_tags=['f8vec']),
            R5('vfge.b',    'R2VF', '1010011 ----- ----- 011 ----- 0110011', tags=['fother'], isa_tags=['f8vec']),
            R5('vfge.r.b',  'R2VF', '1010011 ----- ----- 111 ----- 0110011', tags=['fother'], isa_tags=['f8vec']),
            R5('vfle.b',    'R2VF', '1010100 ----- ----- 011 ----- 0110011', tags=['fother'], isa_tags=['f8vec']),
            R5('vfle.r.b',  'R2VF', '1010100 ----- ----- 111 ----- 0110011', tags=['fother'], isa_tags=['f8vec']),
            R5('vfgt.b',    'R2VF', '1010101 ----- ----- 011 ----- 0110011', tags=['fother'], isa_tags=['f8vec']),
            R5('vfgt.r.b',  'R2VF', '1010101 ----- ----- 111 ----- 0110011', tags=['fother'], isa_tags=['f8vec']),

            # Unless RV32D supported
            R5('vfmv.x.b',   'R3F', '1001100 00000 ----- 011 ----- 0110011', tags=['fother'], isa_tags=['f8vecno32d']),
            R5('vfmv.b.x',   'R3F2','1001100 00000 ----- 111 ----- 0110011', tags=['fother'], isa_tags=['f8vecno32d']),


            R5('vfcvt.x.b',  'R3F', '1001100 00010 ----- 011 ----- 0110011', tags=['fconv'], isa_tags=['f8vecno32d']),
            R5('vfcvt.xu.b', 'R3F', '1001100 00010 ----- 111 ----- 0110011', tags=['fconv'], isa_tags=['f8vecno32d']),
            R5('vfcvt.b.x',  'R3F2','1001100 00011 ----- 011 ----- 0110011', tags=['fconv'], isa_tags=['f8vecno32d']),
            R5('vfcvt.b.xu', 'R3F2','1001100 00011 ----- 111 ----- 0110011', tags=['fconv'], isa_tags=['f8vecno32d']),

            # If F extension also supported (implies FLEN>=32)
            R5('vfcpka.b.s', 'R2VF','1011000 ----- ----- 011 ----- 0110011', tags=['fother'], isa_tags=['f8vecf']),
            R5('vfcpkb.b.s', 'R2VF','1011000 ----- ----- 111 ----- 0110011', tags=['fother'], isa_tags=['f8vecf']),

            # # If D extension also supported (implies FLEN>=64)
            # R5('vfcvt.s.b',  'RVF2','1001100 00111 ----- 000 ----- 0110011', tags=['fconv'], isa_tags=['f8vecd']),
            # R5('vfcvt.b.s',  'RVF2','1001100 00100 ----- 011 ----- 0110011', tags=['fconv'], isa_tags=['f8vecd']),

            # R5('vfcpkc.b.s', 'RVF4','1011001 ----- ----- 011 ----- 0110011', tags=['fother'], isa_tags=['f8vecd']),
            # R5('vfcpkd.b.s', 'RVF4','1011001 ----- ----- 111 ----- 0110011', tags=['fother'], isa_tags=['f8vecd']),
            # R5('vfcpka.b# ', 'RVF4','1011010 ----- ----- 011 ----- 0110011', tags=['fother'], isa_tags=['f8vecd']),
            # R5('vfcpkb.b.d', 'RVF4','1011010 ----- ----- 111 ----- 0110011', tags=['fother'], isa_tags=['f8vecd']),
            # R5('vfcpkc.b.d', 'RVF4','1011011 ----- ----- 011 ----- 0110011', tags=['fother'], isa_tags=['f8vecd']),
            # R5('vfcpkd.b.d', 'RVF4','1011011 ----- ----- 111 ----- 0110011', tags=['fother'], isa_tags=['f8vecd']),

            # If Xf16 extension also supported
            R5('vfcvt.h.b',  'RVF2','1001100 00111 ----- 010 ----- 0110011', tags=['fconv'], isa_tags=['f8vecf16']),
            R5('vfcvt.b.h',  'RVF2','1001100 00110 ----- 011 ----- 0110011', tags=['fconv'], isa_tags=['f8vecf16']),

            # If Xf16alt extension also supported
            R5('vfcvt.ah.b', 'RVF2','1001100 00111 ----- 001 ----- 0110011', tags=['fconv'], isa_tags=['f8vecf16alt']),
            R5('vfcvt.b.ah', 'RVF2','1001100 00101 ----- 011 ----- 0110011', tags=['fconv'], isa_tags=['f8vecf16alt']),

        ])


#
# Auxiliary Float operations
#

class Xfaux(IsaSubset):
    
    def __init__(self):
        super().__init__(name='faux', instrs=[
        #
        # For F
        #
            # # If Xfvec supported
            # R5('vfdotp.s',      'RVF', '1001010 ----- ----- 000 ----- 0110011', tags=['fmadd'], isa_tags=['f32auxvec']),
            # R5('vfdotp.r.s',    'RVF', '1001010 ----- ----- 100 ----- 0110011', tags=['fmadd'], isa_tags=['f32auxvec']),
            # R5('vfavg.s',       'RVF', '1010110 ----- ----- 000 ----- 0110011', tags=['fadd'], isa_tags=['f32auxvec']),
            # R5('vfavg.r.s',     'RVF', '1010110 ----- ----- 100 ----- 0110011', tags=['fadd'], isa_tags=['f32auxvec']),

        #
        # For Xf16
        #
            R5('fmulex.s.h',     'RF', '0100110 ----- ----- --- ----- 1010011', tags=['fmul'], isa_tags=['f16aux']),
            R5('fmacex.s.h',    'RF4', '0101010 ----- ----- --- ----- 1010011', tags=['fmadd'], isa_tags=['f16aux']),

            # If Xfvec supported
            R5('vfdotp.h',      'RVF', '1001010 ----- ----- 010 ----- 0110011', tags=['fmadd'], isa_tags=['f16auxvec']),
            R5('vfdotp.r.h',    'RVF', '1001010 ----- ----- 110 ----- 0110011', tags=['fmadd'], isa_tags=['f16auxvec']),
            R5('vfdotpex.s.h',  'RVF', '1001011 ----- ----- 010 ----- 0110011', tags=['fmadd'], isa_tags=['f16auxvec']),
            R5('vfdotpex.s.r.h','RVF', '1001011 ----- ----- 110 ----- 0110011', tags=['fmadd'], isa_tags=['f16auxvec']),
            R5('vfavg.h',       'RVF', '1010110 ----- ----- 010 ----- 0110011', tags=['fadd'], isa_tags=['f16auxvec']),
            R5('vfavg.r.h',     'RVF', '1010110 ----- ----- 110 ----- 0110011', tags=['fadd'], isa_tags=['f16auxvec']),

        #
        # For Xf16aux
        #
            R5('fmulex.s.ah',    'RF', '0100110 ----- ----- 101 ----- 1010011', tags=['fmul'], isa_tags=['f16altaux']),
            R5('fmacex.s.ah',   'RF4', '0101010 ----- ----- 101 ----- 1010011', tags=['fmadd'], isa_tags=['f16altaux']),

            # If Xfvec supported
            R5('vfdotp.ah',      'RVF','1001010 ----- ----- 001 ----- 0110011', tags=['fmadd'], isa_tags=['f16altauxvec']),
            R5('vfdotp.r.ah',    'RVF','1001010 ----- ----- 101 ----- 0110011', tags=['fmadd'], isa_tags=['f16altauxvec']),
            R5('vfdotpex.s.ah',  'RVF','1001011 ----- ----- 001 ----- 0110011', tags=['fmadd'], isa_tags=['f16altauxvec']),
            R5('vfdotpex.s.r.ah','RVF','1001011 ----- ----- 101 ----- 0110011', tags=['fmadd'], isa_tags=['f16altauxvec']),
            R5('vfavg.ah',       'RVF','1010110 ----- ----- 001 ----- 0110011', tags=['fadd'], isa_tags=['f16altauxvec']),
            R5('vfavg.r.ah',     'RVF','1010110 ----- ----- 101 ----- 0110011', tags=['fadd'], isa_tags=['f16altauxvec']),

        #
        # For Xf8
        #
            R5('fmulex.s.b',     'RF', '0100111 ----- ----- --- ----- 1010011', tags=['fmul'], isa_tags=['f8aux']),
            R5('fmacex.s.b',    'RF4', '0101011 ----- ----- --- ----- 1010011', tags=['fmadd'], isa_tags=['f8aux']),

            # If Xfvec supported
            R5('vfdotp.b',      'RVF', '1001010 ----- ----- 011 ----- 0110011', tags=['fmadd'], isa_tags=['f8auxvec']),
            R5('vfdotp.r.b',    'RVF', '1001010 ----- ----- 111 ----- 0110011', tags=['fmadd'], isa_tags=['f8auxvec']),
            R5('vfdotpex.s.b',  'RVF', '1001011 ----- ----- 011 ----- 0110011', tags=['fmadd'], isa_tags=['f8auxvec']),
            R5('vfdotpex.s.r.b','RVF', '1001011 ----- ----- 111 ----- 0110011', tags=['fmadd'], isa_tags=['f8auxvec']),
            R5('vfavg.b',       'RVF', '1010110 ----- ----- 011 ----- 0110011', tags=['fadd'], isa_tags=['f8auxvec']),
            R5('vfavg.r.b',     'RVF', '1010110 ----- ----- 111 ----- 0110011', tags=['fadd'], isa_tags=['f8auxvec']),

        ])


#
# Privileged ISA
#
class Priv(IsaSubset):
    
    def __init__(self):
        super().__init__(name='priv', instrs=[
            R5('csrrw', 'IU',  '------- ----- ----- 001 ----- 1110011', decode='csr_decode'),
            R5('csrrs', 'IU',  '------- ----- ----- 010 ----- 1110011', decode='csr_decode'),
            R5('csrrc', 'IU',  '------- ----- ----- 011 ----- 1110011', decode='csr_decode'),
            R5('csrrwi','IUR', '------- ----- ----- 101 ----- 1110011', decode='csr_decode'),
            R5('csrrsi','IUR', '------- ----- ----- 110 ----- 1110011', decode='csr_decode'),
            R5('csrrci','IUR', '------- ----- ----- 111 ----- 1110011', decode='csr_decode'),

        ])


class TrapReturn(IsaSubset):
    
    def __init__(self):
        super().__init__(name='trap_return', instrs=[
            #R5('uret',      'Z',   '0000000 00010 00000 000 00000 1110011'),
            R5('sret',      'Z',   '0001000 00010 00000 000 00000 1110011'),
            #R5('hret',      'Z',   '0010000 00010 00000 000 00000 1110011'),
            R5('mret',      'Z',   '0011000 00010 00000 000 00000 1110011'),
            R5('dret',      'Z',   '0111101 10010 00000 000 00000 1110011'),
            R5('wfi',       'Z',   '0001000 00101 00000 000 00000 1110011'),

        ])



class PrivSmmu(IsaSubset):
    
    def __init__(self):
        super().__init__(name='priv_smmu', instrs=[
            R5('sfence.vma',       'INRR',   '0001001 ----- ----- 000 00000 1110011'),

        ])


#
# Zcmp
#
class Zcmp(IsaSubset):
    
    def __init__(self):
        super().__init__(name='zcmp', instrs=[
            # Compressed ISA
            R5('cm.push'    , 'CMPUSH','101 110 00- -- --- 10', is_macro_op=True),
            R5('cm.pop'     , 'CMPUSH','101 110 10- -- --- 10', is_macro_op=True),
            R5('cm.popretz' , 'CMPUSH','101 111 00- -- --- 10', is_macro_op=True),
            R5('cm.popret'  , 'CMPUSH','101 111 10- -- --- 10', is_macro_op=True),
        ])



#
# RV32C
#
class Rv32c(IsaSubset):
    
    def __init__(self):
        super().__init__(name='c', instrs=[
            # Compressed ISA
            R5('c.unimp',    'CI1', '000 000 000 00 000 00'),
            R5('c.addi4spn', 'CIW', '000 --- --- -- --- 00', fast_handler=True),
            R5('c.lw',       'CL',  '010 --- --- -- --- 00', fast_handler=True, tags=["load"]),
            R5('c.sw',       'CS',  '110 --- --- -- --- 00', fast_handler=True),
            R5('c.nop',      'CI1', '000 000 000 00 000 01', fast_handler=True),
            R5('c.addi',     'CI1', '000 --- --- -- --- 01', fast_handler=True),
            R5('c.jal',      'CJ1', '001 --- --- -- --- 01', fast_handler=True, decode='jal_decode'),
            R5('c.li',       'CI6', '010 --- --- -- --- 01', fast_handler=True),
            R5('c.addi16sp', 'CI4', '011 -00 010 -- --- 01', fast_handler=True),
            R5('c.lui',      'CI5', '011 --- --- -- --- 01', fast_handler=True),
            R5('c.srli',     'CB2', '100 -00 --- -- --- 01', fast_handler=True),
            R5('c.srai',     'CB2', '100 -01 --- -- --- 01', fast_handler=True),
            R5('c.andi',     'CB2S','100 -10 --- -- --- 01', fast_handler=True),
            R5('c.sub',      'CS2', '100 011 --- 00 --- 01', fast_handler=True),
            R5('c.xor',      'CS2', '100 011 --- 01 --- 01', fast_handler=True),
            R5('c.or',       'CS2', '100 011 --- 10 --- 01', fast_handler=True),
            R5('c.and',      'CS2', '100 011 --- 11 --- 01', fast_handler=True),
            R5('c.j',        'CJ',  '101 --- --- -- --- 01', fast_handler=True, decode='jal_decode'),
            R5('c.beqz',     'CB1', '110 --- --- -- --- 01', fast_handler=True, decode='bxx_decode'),
            R5('c.bnez',     'CB1', '111 --- --- -- --- 01', fast_handler=True, decode='bxx_decode'),
            R5('c.slli',     'CI1U','000 --- --- -- --- 10', fast_handler=True),
            R5('c.lwsp',     'CI3', '010 --- --- -- --- 10', fast_handler=True, tags=["load"]),
            R5('c.jr',       'CR1', '100 0-- --- 00 000 10', fast_handler=True),
            R5('c.mv',       'CR2', '100 0-- --- -- --- 10', fast_handler=True),
            R5('c.ebreak',   'CR',  '100 100 000 00 000 10'),
            R5('c.jalr',     'CR3', '100 1-- --- 00 000 10', fast_handler=True),
            R5('c.add',      'CR',  '100 1-- --- -- --- 10', fast_handler=True),
            R5('c.swsp',     'CSS', '110 --- --- -- --- 10', fast_handler=True),
            R5('c.sbreak',   'CI1', '100 000 000 00 000 10'),
            R5('c.flwsp',    'FCI3', '011 --- --- -- --- 10', tags=["load"], isa_tags=['cf']),
            R5('c.fswsp',    'FCSS', '111 --- --- -- --- 10', isa_tags=['cf']),
            R5('c.fsw',      'FCS',  '111 --- --- -- --- 00', isa_tags=['cf']),
            R5('c.flw',      'FCL',  '011 --- --- -- --- 00', tags=["load"], isa_tags=['cf']),
        ])


        if os.environ.get('CONFIG_GVSOC_USE_UNCOMPRESSED_LABELS') is not None:
            unconmpressed_names = [
                'addi', 'lw', 'sw', 'nop', 'addi', 'jal', 'addi', 'addi', 'lui', 'srli', 'srai', 'andi', 'sub', 'xor', 'or', 'and', 'j', 'beqz', 'bnez', 'slli',
                'lw', 'jr', 'mv', 'ebreak', 'jalr', 'add', 'sw', 'sbreak',
            ]

            for insn in self.instrs:
                label = unconmpressed_names.pop(0)
                insn.traceLabel = label


#
# RV64C
#
class Rv64c(IsaSubset):

    def __init__(self):
        super().__init__(name='c', instrs=[
            # Compressed ISA
            R5('c.unimp',    'CI1', '000 000 000 00 000 00'),
            R5('c.addi4spn', 'CIW', '000 --- --- -- --- 00', fast_handler=True),
            R5('c.ld',       'CLD', '011 --- --- -- --- 00', fast_handler=True, tags=["load"]),
            R5('c.lw',       'CL',  '010 --- --- -- --- 00', fast_handler=True, tags=["load"]),
            R5('c.fld',      'CFLD', '001 --- --- -- --- 00', fast_handler=True, tags=["load"]),
            R5('c.sw',       'CS',  '110 --- --- -- --- 00', fast_handler=True),
            R5('c.sd',       'CSD', '111 --- --- -- --- 00', fast_handler=True),
            R5('c.fsd',      'CFSD', '101 --- --- -- --- 00', fast_handler=True),
            R5('c.nop',      'CI1', '000 000 000 00 000 01', fast_handler=True),
            R5('c.addi',     'CI1', '000 --- --- -- --- 01', fast_handler=True),
            R5('c.addiw',    'CI1', '001 --- --- -- --- 01', fast_handler=True),
            R5('c.li',       'CI6', '010 --- --- -- --- 01', fast_handler=True),
            R5('c.addi16sp', 'CI4', '011 -00 010 -- --- 01', fast_handler=True),
            R5('c.lui',      'CI5', '011 --- --- -- --- 01', fast_handler=True),
            R5('c.srli',     'CB2', '100 -00 --- -- --- 01', fast_handler=True),
            R5('c.srai',     'CB2', '100 -01 --- -- --- 01', fast_handler=True),
            R5('c.andi',     'CB2S','100 -10 --- -- --- 01', fast_handler=True),
            R5('c.sub',      'CS2', '100 011 --- 00 --- 01', fast_handler=True),
            R5('c.xor',      'CS2', '100 011 --- 01 --- 01', fast_handler=True),
            R5('c.or',       'CS2', '100 011 --- 10 --- 01', fast_handler=True),
            R5('c.and',      'CS2', '100 011 --- 11 --- 01', fast_handler=True),
            R5('c.subw',     'CS2', '100 111 --- 00 --- 01', fast_handler=True),
            R5('c.addw',     'CS2', '100 111 --- 01 --- 01', fast_handler=True),
            R5('c.j',        'CJ',  '101 --- --- -- --- 01', fast_handler=True, decode='jal_decode'),
            R5('c.beqz',     'CB1', '110 --- --- -- --- 01', fast_handler=True, decode='bxx_decode'),
            R5('c.bnez',     'CB1', '111 --- --- -- --- 01', fast_handler=True, decode='bxx_decode'),
            R5('c.slli',     'CI1U','000 --- --- -- --- 10', fast_handler=True),
            R5('c.lwsp',     'CI3', '010 --- --- -- --- 10', fast_handler=True, tags=["load"]),
            R5('c.ldsp',     'DCI3', '011 --- --- -- --- 10', fast_handler=True, tags=["load"]),
            R5('c.jr',       'CR1', '100 0-- --- 00 000 10', fast_handler=True),
            R5('c.mv',       'CR2', '100 0-- --- -- --- 10', fast_handler=True),
            R5('c.ebreak',   'CR',  '100 100 000 00 000 10'),
            R5('c.jalr',     'CR3', '100 1-- --- 00 000 10', fast_handler=True),
            R5('c.add',      'CR',  '100 1-- --- -- --- 10', fast_handler=True),
            R5('c.swsp',     'CSS', '110 --- --- -- --- 10', fast_handler=True),
            R5('c.sdsp',     'DCSS', '111 --- --- -- --- 10', fast_handler=True),
            R5('c.sbreak',   'CI1', '100 000 000 00 000 10'),
            R5('c.fsdsp',    'FCSSD', '101 --- --- -- --- 10', isa_tags=['cf']),
            R5('c.fldsp',    'FCI3D', '001 --- --- -- --- 10', tags=["load"], isa_tags=['cf']),
        ])



#
# PULP extensions
#

class PulpV2(IsaSubset):

    def __init__(self):
        super().__init__(name='pulpv2', instrs=[
            # Reg-reg LD/ST
            R5('LB_RR',    'LR', '0000000 ----- ----- 111 ----- 0000011', L='p.lb' , fast_handler=True, tags=["load"]),
            R5('LH_RR',    'LR', '0001000 ----- ----- 111 ----- 0000011', L='p.lh' , fast_handler=True, tags=["load"]),
            R5('LW_RR',    'LR', '0010000 ----- ----- 111 ----- 0000011', L='p.lw' , fast_handler=True, tags=["load"]),
            R5('LBU_RR',   'LR', '0100000 ----- ----- 111 ----- 0000011', L='p.lbu', fast_handler=True, tags=["load"]),
            R5('LHU_RR',   'LR', '0101000 ----- ----- 111 ----- 0000011', L='p.lhu', fast_handler=True, tags=["load"]),

            # Regular post-inc LD/ST
            R5('LB_POSTINC',    'LPOST', '------- ----- ----- 000 ----- 0001011', L='p.lb' , fast_handler=True, tags=["load"]),
            R5('LH_POSTINC',    'LPOST', '------- ----- ----- 001 ----- 0001011', L='p.lh' , fast_handler=True, tags=["load"]),
            R5('LW_POSTINC',    'LPOST', '------- ----- ----- 010 ----- 0001011', L='p.lw' , fast_handler=True, tags=["load"]),
            R5('LBU_POSTINC',   'LPOST', '------- ----- ----- 100 ----- 0001011', L='p.lbu', fast_handler=True, tags=["load"]),
            R5('LHU_POSTINC',   'LPOST', '------- ----- ----- 101 ----- 0001011', L='p.lhu', fast_handler=True, tags=["load"]),
            R5('SB_POSTINC',    'SPOST', '------- ----- ----- 000 ----- 0101011', L='p.sb' , fast_handler=True),
            R5('SH_POSTINC',    'SPOST', '------- ----- ----- 001 ----- 0101011', L='p.sh' , fast_handler=True),
            R5('SW_POSTINC',    'SPOST', '------- ----- ----- 010 ----- 0101011', L='p.sw' , fast_handler=True),

            # Reg-reg post-inc LD/ST
            R5('LB_RR_POSTINC',   'LRPOST',  '0000000 ----- ----- 111 ----- 0001011', L='p.lb' , fast_handler=True, tags=["load"]),
            R5('LH_RR_POSTINC',   'LRPOST',  '0001000 ----- ----- 111 ----- 0001011', L='p.lh' , fast_handler=True, tags=["load"]),
            R5('LW_RR_POSTINC',   'LRPOST',  '0010000 ----- ----- 111 ----- 0001011', L='p.lw' , fast_handler=True, tags=["load"]),
            R5('LBU_RR_POSTINC',  'LRPOST',  '0100000 ----- ----- 111 ----- 0001011', L='p.lbu', fast_handler=True, tags=["load"]),
            R5('LHU_RR_POSTINC',  'LRPOST',  '0101000 ----- ----- 111 ----- 0001011', L='p.lhu', fast_handler=True, tags=["load"]),
            R5('SB_RR_POSTINC',   'SRPOST', '0000000 ----- ----- 100 ----- 0101011',  L='p.sb' , fast_handler=True),
            R5('SH_RR_POSTINC',   'SRPOST', '0000000 ----- ----- 101 ----- 0101011',  L='p.sh' , fast_handler=True),
            R5('SW_RR_POSTINC',   'SRPOST', '0000000 ----- ----- 110 ----- 0101011',  L='p.sw' , fast_handler=True),

            # Additional ALU operations
            R5('p.avgu','R',  '0000010 ----- ----- 001 ----- 0110011'),
            R5('p.slet','R',  '0000010 ----- ----- 010 ----- 0110011'),
            R5('p.sletu','R', '0000010 ----- ----- 011 ----- 0110011'),
            R5('p.min', 'R',  '0000010 ----- ----- 100 ----- 0110011'),
            R5('p.minu','R',  '0000010 ----- ----- 101 ----- 0110011'),
            R5('p.max', 'R',  '0000010 ----- ----- 110 ----- 0110011'),
            R5('p.maxu','R',  '0000010 ----- ----- 111 ----- 0110011'),
            R5('p.ror', 'R',  '0000100 ----- ----- 101 ----- 0110011'),
            R5('p.ff1', 'R1',  '0001000 00000 ----- 000 ----- 0110011'),
            R5('p.fl1','R1',   '0001000 00000 ----- 001 ----- 0110011'),
            R5('p.clb', 'R1',  '0001000 00000 ----- 010 ----- 0110011'),
            R5('p.cnt', 'R1',  '0001000 00000 ----- 011 ----- 0110011'),
            R5('p.exths','R1', '0001000 00000 ----- 100 ----- 0110011'),
            R5('p.exthz','R1', '0001000 00000 ----- 101 ----- 0110011'),
            R5('p.extbs','R1', '0001000 00000 ----- 110 ----- 0110011'),
            R5('p.extbz','R1', '0001000 00000 ----- 111 ----- 0110011'),

            # HW loops
            R5('lp.starti','HL0','------- ----- ----- 000 0000- 1111011'),
            R5('lp.endi',  'HL0','------- ----- ----- 001 0000- 1111011'),
            R5('lp.count', 'HL0','------- ----- ----- 010 0000- 1111011'),
            R5('lp.counti','HL0','------- ----- ----- 011 0000- 1111011'),
            R5('lp.setup', 'HL0','------- ----- ----- 100 0000- 1111011'),
            R5('lp.setupi','HL1','------- ----- ----- 101 0000- 1111011'),

            R5('p.abs',  'R1', '0000010 00000 ----- 000 ----- 0110011'),

            R5('SB_RR',    'SR', '0000000 ----- ----- 100 ----- 0100011', L='p.sb', fast_handler=True),
            R5('SH_RR',    'SR', '0000000 ----- ----- 101 ----- 0100011', L='p.sh', fast_handler=True),
            R5('SW_RR',    'SR', '0000000 ----- ----- 110 ----- 0100011', L='p.sw', fast_handler=True),

            R5('p.elw',           'L',   '------- ----- ----- 110 ----- 0000011', tags=["load"]),

            R5('pv.add.h',        'R',   '000000- ----- ----- 000 ----- 1010111'),
            R5('pv.add.sc.h',     'R',   '000000- ----- ----- 100 ----- 1010111'),
            R5('pv.add.sci.h',    'RRS', '000000- ----- ----- 110 ----- 1010111'),
            R5('pv.add.b',        'R',   '000000- ----- ----- 001 ----- 1010111'),
            R5('pv.add.sc.b',     'R',   '000000- ----- ----- 101 ----- 1010111'),
            R5('pv.add.sci.b',    'RRS', '000000- ----- ----- 111 ----- 1010111'),

            R5('pv.sub.h',        'R',   '000010- ----- ----- 000 ----- 1010111'),
            R5('pv.sub.sc.h',     'R',   '000010- ----- ----- 100 ----- 1010111'),
            R5('pv.sub.sci.h',    'RRS', '000010- ----- ----- 110 ----- 1010111'),
            R5('pv.sub.b',        'R',   '000010- ----- ----- 001 ----- 1010111'),
            R5('pv.sub.sc.b',     'R',   '000010- ----- ----- 101 ----- 1010111'),
            R5('pv.sub.sci.b',    'RRS', '000010- ----- ----- 111 ----- 1010111'),

            R5('pv.avg.h',        'R',   '000100- ----- ----- 000 ----- 1010111'),
            R5('pv.avg.sc.h',     'R',   '000100- ----- ----- 100 ----- 1010111'),
            R5('pv.avg.sci.h',    'RRS', '000100- ----- ----- 110 ----- 1010111'),
            R5('pv.avg.b',        'R',   '000100- ----- ----- 001 ----- 1010111'),
            R5('pv.avg.sc.b',     'R',   '000100- ----- ----- 101 ----- 1010111'),
            R5('pv.avg.sci.b',    'RRS', '000100- ----- ----- 111 ----- 1010111'),

            R5('pv.avgu.h',       'R',   '000110- ----- ----- 000 ----- 1010111'),
            R5('pv.avgu.sc.h',    'R',   '000110- ----- ----- 100 ----- 1010111'),
            R5('pv.avgu.sci.h',   'RRU', '000110- ----- ----- 110 ----- 1010111'),
            R5('pv.avgu.b',       'R',   '000110- ----- ----- 001 ----- 1010111'),
            R5('pv.avgu.sc.b',    'R',   '000110- ----- ----- 101 ----- 1010111'),
            R5('pv.avgu.sci.b',   'RRU', '000110- ----- ----- 111 ----- 1010111'),

            R5('pv.min.h',        'R',   '001000- ----- ----- 000 ----- 1010111'),
            R5('pv.min.sc.h',     'R',   '001000- ----- ----- 100 ----- 1010111'),
            R5('pv.min.sci.h',    'RRS', '001000- ----- ----- 110 ----- 1010111'),
            R5('pv.min.b',        'R',   '001000- ----- ----- 001 ----- 1010111'),
            R5('pv.min.sc.b',     'R',   '001000- ----- ----- 101 ----- 1010111'),
            R5('pv.min.sci.b',    'RRS', '001000- ----- ----- 111 ----- 1010111'),

            R5('pv.minu.h',       'R',   '001010- ----- ----- 000 ----- 1010111'),
            R5('pv.minu.sc.h',    'R',   '001010- ----- ----- 100 ----- 1010111'),
            R5('pv.minu.sci.h',   'RRU', '001010- ----- ----- 110 ----- 1010111'),
            R5('pv.minu.b',       'R',   '001010- ----- ----- 001 ----- 1010111'),
            R5('pv.minu.sc.b',    'R',   '001010- ----- ----- 101 ----- 1010111'),
            R5('pv.minu.sci.b',   'RRU', '001010- ----- ----- 111 ----- 1010111'),

            R5('pv.max.h',        'R',   '001100- ----- ----- 000 ----- 1010111'),
            R5('pv.max.sc.h',     'R',   '001100- ----- ----- 100 ----- 1010111'),
            R5('pv.max.sci.h',    'RRS', '001100- ----- ----- 110 ----- 1010111'),
            R5('pv.max.b',        'R',   '001100- ----- ----- 001 ----- 1010111'),
            R5('pv.max.sc.b',     'R',   '001100- ----- ----- 101 ----- 1010111'),
            R5('pv.max.sci.b',    'RRS', '001100- ----- ----- 111 ----- 1010111'),

            R5('pv.maxu.h',       'R',   '001110- ----- ----- 000 ----- 1010111'),
            R5('pv.maxu.sc.h',    'R',   '001110- ----- ----- 100 ----- 1010111'),
            R5('pv.maxu.sci.h',   'RRU', '001110- ----- ----- 110 ----- 1010111'),
            R5('pv.maxu.b',       'R',   '001110- ----- ----- 001 ----- 1010111'),
            R5('pv.maxu.sc.b',    'R',   '001110- ----- ----- 101 ----- 1010111'),
            R5('pv.maxu.sci.b',   'RRU', '001110- ----- ----- 111 ----- 1010111'),

            R5('pv.srl.h',        'R',   '010000- ----- ----- 000 ----- 1010111'),
            R5('pv.srl.sc.h',     'R',   '010000- ----- ----- 100 ----- 1010111'),
            R5('pv.srl.sci.h',    'RRU', '010000- ----- ----- 110 ----- 1010111'),
            R5('pv.srl.b',        'R',   '010000- ----- ----- 001 ----- 1010111'),
            R5('pv.srl.sc.b',     'R',   '010000- ----- ----- 101 ----- 1010111'),
            R5('pv.srl.sci.b',    'RRU', '010000- ----- ----- 111 ----- 1010111'),

            R5('pv.sra.h',        'R',   '010010- ----- ----- 000 ----- 1010111'),
            R5('pv.sra.sc.h',     'R',   '010010- ----- ----- 100 ----- 1010111'),
            R5('pv.sra.sci.h',    'RRS', '010010- ----- ----- 110 ----- 1010111'),
            R5('pv.sra.b',        'R',   '010010- ----- ----- 001 ----- 1010111'),
            R5('pv.sra.sc.b',     'R',   '010010- ----- ----- 101 ----- 1010111'),
            R5('pv.sra.sci.b',    'RRS', '010010- ----- ----- 111 ----- 1010111'),

            R5('pv.sll.h',        'R',   '010100- ----- ----- 000 ----- 1010111'),
            R5('pv.sll.sc.h',     'R',   '010100- ----- ----- 100 ----- 1010111'),
            R5('pv.sll.sci.h',    'RRU', '010100- ----- ----- 110 ----- 1010111'),
            R5('pv.sll.b',        'R',   '010100- ----- ----- 001 ----- 1010111'),
            R5('pv.sll.sc.b',     'R',   '010100- ----- ----- 101 ----- 1010111'),
            R5('pv.sll.sci.b',    'RRU', '010100- ----- ----- 111 ----- 1010111'),

            R5('pv.or.h',         'R',   '010110- ----- ----- 000 ----- 1010111'),
            R5('pv.or.sc.h',      'R',   '010110- ----- ----- 100 ----- 1010111'),
            R5('pv.or.sci.h',     'RRS', '010110- ----- ----- 110 ----- 1010111'),
            R5('pv.or.b',         'R',   '010110- ----- ----- 001 ----- 1010111'),
            R5('pv.or.sc.b',      'R',   '010110- ----- ----- 101 ----- 1010111'),
            R5('pv.or.sci.b',     'RRS', '010110- ----- ----- 111 ----- 1010111'),

            R5('pv.xor.h',        'R',   '011000- ----- ----- 000 ----- 1010111'),
            R5('pv.xor.sc.h',     'R',   '011000- ----- ----- 100 ----- 1010111'),
            R5('pv.xor.sci.h',    'RRS', '011000- ----- ----- 110 ----- 1010111'),
            R5('pv.xor.b',        'R',   '011000- ----- ----- 001 ----- 1010111'),
            R5('pv.xor.sc.b',     'R',   '011000- ----- ----- 101 ----- 1010111'),
            R5('pv.xor.sci.b',    'RRS', '011000- ----- ----- 111 ----- 1010111'),

            R5('pv.and.h',        'R',   '011010- ----- ----- 000 ----- 1010111'),
            R5('pv.and.sc.h',     'R',   '011010- ----- ----- 100 ----- 1010111'),
            R5('pv.and.sci.h',    'RRS', '011010- ----- ----- 110 ----- 1010111'),
            R5('pv.and.b',        'R',   '011010- ----- ----- 001 ----- 1010111'),
            R5('pv.and.sc.b',     'R',   '011010- ----- ----- 101 ----- 1010111'),
            R5('pv.and.sci.b',    'RRS', '011010- ----- ----- 111 ----- 1010111'),

            R5('pv.abs.h',        'R1',  '0111000 ----- ----- 000 ----- 1010111'),
            R5('pv.abs.b',        'R1',  '0111000 ----- ----- 001 ----- 1010111'),

            R5('pv.extract.h',    'RRU', '011110- ----- ----- 110 ----- 1010111'),
            R5('pv.extract.b',    'RRU', '011110- ----- ----- 111 ----- 1010111'),
            R5('pv.extractu.h',   'RRU', '100100- ----- ----- 110 ----- 1010111'),
            R5('pv.extractu.b',   'RRU', '100100- ----- ----- 111 ----- 1010111'),

            R5('pv.insert.h',     'RRRU','101100- ----- ----- 110 ----- 1010111'),
            R5('pv.insert.b',     'RRRU','101100- ----- ----- 111 ----- 1010111'),

            R5('pv.dotsp.h',      'R',   '100110- ----- ----- 000 ----- 1010111'),
            R5('pv.dotsp.h.sc',   'R',   '100110- ----- ----- 100 ----- 1010111'),
            R5('pv.dotsp.h.sci',  'RRS', '100110- ----- ----- 110 ----- 1010111'),

            R5('pv.dotsp.b',      'R',   '100110- ----- ----- 001 ----- 1010111'),
            R5('pv.dotsp.b.sc',   'R',   '100110- ----- ----- 101 ----- 1010111'),
            R5('pv.dotsp.b.sci',  'RRS', '100110- ----- ----- 111 ----- 1010111'),

            R5('pv.dotup.h',      'R',   '100000- ----- ----- 000 ----- 1010111'),
            R5('pv.dotup.h.sc',   'R',   '100000- ----- ----- 100 ----- 1010111'),
            R5('pv.dotup.h.sci',  'RRU', '100000- ----- ----- 110 ----- 1010111'),

            R5('pv.dotup.b',      'R',   '100000- ----- ----- 001 ----- 1010111'),
            R5('pv.dotup.b.sc',   'R',   '100000- ----- ----- 101 ----- 1010111'),
            R5('pv.dotup.b.sci',  'RRU', '100000- ----- ----- 111 ----- 1010111'),

            R5('pv.dotusp.h',     'R',   '100010- ----- ----- 000 ----- 1010111'),
            R5('pv.dotusp.h.sc',  'R',   '100010- ----- ----- 100 ----- 1010111'),
            R5('pv.dotusp.h.sci', 'RRS', '100010- ----- ----- 110 ----- 1010111'),

            R5('pv.dotusp.b',     'R',   '100010- ----- ----- 001 ----- 1010111'),
            R5('pv.dotusp.b.sc',  'R',   '100010- ----- ----- 101 ----- 1010111'),
            R5('pv.dotusp.b.sci', 'RRS', '100010- ----- ----- 111 ----- 1010111'),


            R5('pv.sdotsp.h',     'RRRR','101110- ----- ----- 000 ----- 1010111'),
            R5('pv.sdotsp.h.sc',  'RRRR','101110- ----- ----- 100 ----- 1010111'),
            R5('pv.sdotsp.h.sci', 'RRRS','101110- ----- ----- 110 ----- 1010111'),

            R5('pv.sdotsp.b',     'RRRR','101110- ----- ----- 001 ----- 1010111'),
            R5('pv.sdotsp.b.sc',  'RRRR','101110- ----- ----- 101 ----- 1010111'),
            R5('pv.sdotsp.b.sci', 'RRRS','101110- ----- ----- 111 ----- 1010111'),

            R5('pv.sdotup.h',     'RRRR','101000- ----- ----- 000 ----- 1010111'),
            R5('pv.sdotup.h.sc',  'RRRR','101000- ----- ----- 100 ----- 1010111'),
            R5('pv.sdotup.h.sci', 'RRRU','101000- ----- ----- 110 ----- 1010111'),

            R5('pv.sdotup.b',     'RRRR','101000- ----- ----- 001 ----- 1010111'),
            R5('pv.sdotup.b.sc',  'RRRR','101000- ----- ----- 101 ----- 1010111'),
            R5('pv.sdotup.b.sci', 'RRRU','101000- ----- ----- 111 ----- 1010111'),

            R5('pv.sdotusp.h',    'RRRR','101010- ----- ----- 000 ----- 1010111'),
            R5('pv.sdotusp.h.sc', 'RRRR','101010- ----- ----- 100 ----- 1010111'),
            R5('pv.sdotusp.h.sci','RRRS','101010- ----- ----- 110 ----- 1010111'),

            R5('pv.sdotusp.b',    'RRRR','101010- ----- ----- 001 ----- 1010111'),
            R5('pv.sdotusp.b.sc', 'RRRR','101010- ----- ----- 101 ----- 1010111'),
            R5('pv.sdotusp.b.sci','RRRS','101010- ----- ----- 111 ----- 1010111'),

            R5('pv.shuffle.h',    'R',   '110000- ----- ----- 000 ----- 1010111'),
            R5('pv.shuffle.h.sci','RRU', '110000- ----- ----- 110 ----- 1010111'),

            R5('pv.shuffle.b',    'R',   '110000- ----- ----- 001 ----- 1010111'),
            R5('pv.shufflei0.b.sci','RRU2','110000- ----- ----- 111 ----- 1010111'),
            R5('pv.shufflei1.b.sci','RRU2','111010- ----- ----- 111 ----- 1010111'),
            R5('pv.shufflei2.b.sci','RRU2','111100- ----- ----- 111 ----- 1010111'),
            R5('pv.shufflei3.b.sci','RRU2','111110- ----- ----- 111 ----- 1010111'),

            R5('pv.shuffle2.h',   'RRRR','110010- ----- ----- 000 ----- 1010111'),
            R5('pv.shuffle2.b',   'RRRR','110010- ----- ----- 001 ----- 1010111'),

            R5('pv.pack.h',       'RRRR','1101000 ----- ----- 000 ----- 1010111'),
            R5('pv.packhi.b',     'RRRR','110110- ----- ----- 001 ----- 1010111'),
            R5('pv.packlo.b',     'RRRR','111000- ----- ----- 001 ----- 1010111'),

            R5('pv.cmpeq.h',      'R',   '000001- ----- ----- 000 ----- 1010111'),
            R5('pv.cmpeq.sc.h',   'R',   '000001- ----- ----- 100 ----- 1010111'),
            R5('pv.cmpeq.sci.h',  'RRS', '000001- ----- ----- 110 ----- 1010111'),
            R5('pv.cmpeq.b',      'R',   '000001- ----- ----- 001 ----- 1010111'),
            R5('pv.cmpeq.sc.b',   'R',   '000001- ----- ----- 101 ----- 1010111'),
            R5('pv.cmpeq.sci.b',  'RRS', '000001- ----- ----- 111 ----- 1010111'),

            R5('pv.cmpne.h',      'R',   '000011- ----- ----- 000 ----- 1010111'),
            R5('pv.cmpne.sc.h',   'R',   '000011- ----- ----- 100 ----- 1010111'),
            R5('pv.cmpne.sci.h',  'RRS', '000011- ----- ----- 110 ----- 1010111'),
            R5('pv.cmpne.b',      'R',   '000011- ----- ----- 001 ----- 1010111'),
            R5('pv.cmpne.sc.b',   'R',   '000011- ----- ----- 101 ----- 1010111'),
            R5('pv.cmpne.sci.b',  'RRS', '000011- ----- ----- 111 ----- 1010111'),

            R5('pv.cmpgt.h',      'R',   '000101- ----- ----- 000 ----- 1010111'),
            R5('pv.cmpgt.sc.h',   'R',   '000101- ----- ----- 100 ----- 1010111'),
            R5('pv.cmpgt.sci.h',  'RRS', '000101- ----- ----- 110 ----- 1010111'),
            R5('pv.cmpgt.b',      'R',   '000101- ----- ----- 001 ----- 1010111'),
            R5('pv.cmpgt.sc.b',   'R',   '000101- ----- ----- 101 ----- 1010111'),
            R5('pv.cmpgt.sci.b',  'RRS', '000101- ----- ----- 111 ----- 1010111'),

            R5('pv.cmpge.h',      'R',   '000111- ----- ----- 000 ----- 1010111'),
            R5('pv.cmpge.sc.h',   'R',   '000111- ----- ----- 100 ----- 1010111'),
            R5('pv.cmpge.sci.h',  'RRS', '000111- ----- ----- 110 ----- 1010111'),
            R5('pv.cmpge.b',      'R',   '000111- ----- ----- 001 ----- 1010111'),
            R5('pv.cmpge.sc.b',   'R',   '000111- ----- ----- 101 ----- 1010111'),
            R5('pv.cmpge.sci.b',  'RRS', '000111- ----- ----- 111 ----- 1010111'),

            R5('pv.cmplt.h',      'R',   '001001- ----- ----- 000 ----- 1010111'),
            R5('pv.cmplt.sc.h',   'R',   '001001- ----- ----- 100 ----- 1010111'),
            R5('pv.cmplt.sci.h',  'RRS', '001001- ----- ----- 110 ----- 1010111'),
            R5('pv.cmplt.b',      'R',   '001001- ----- ----- 001 ----- 1010111'),
            R5('pv.cmplt.sc.b',   'R',   '001001- ----- ----- 101 ----- 1010111'),
            R5('pv.cmplt.sci.b',  'RRS', '001001- ----- ----- 111 ----- 1010111'),

            R5('pv.cmple.h',      'R',   '001011- ----- ----- 000 ----- 1010111'),
            R5('pv.cmple.sc.h',   'R',   '001011- ----- ----- 100 ----- 1010111'),
            R5('pv.cmple.sci.h',  'RRS', '001011- ----- ----- 110 ----- 1010111'),
            R5('pv.cmple.b',      'R',   '001011- ----- ----- 001 ----- 1010111'),
            R5('pv.cmple.sc.b',   'R',   '001011- ----- ----- 101 ----- 1010111'),
            R5('pv.cmple.sci.b',  'RRS', '001011- ----- ----- 111 ----- 1010111'),

            R5('pv.cmpgtu.h',     'R',   '001101- ----- ----- 000 ----- 1010111'),
            R5('pv.cmpgtu.sc.h',  'R',   '001101- ----- ----- 100 ----- 1010111'),
            R5('pv.cmpgtu.sci.h', 'RRU', '001101- ----- ----- 110 ----- 1010111'),
            R5('pv.cmpgtu.b',     'R',   '001101- ----- ----- 001 ----- 1010111'),
            R5('pv.cmpgtu.sc.b',  'R',   '001101- ----- ----- 101 ----- 1010111'),
            R5('pv.cmpgtu.sci.b', 'RRU', '001101- ----- ----- 111 ----- 1010111'),

            R5('pv.cmpgeu.h',     'R',   '001111- ----- ----- 000 ----- 1010111'),
            R5('pv.cmpgeu.sc.h',  'R',   '001111- ----- ----- 100 ----- 1010111'),
            R5('pv.cmpgeu.sci.h', 'RRU', '001111- ----- ----- 110 ----- 1010111'),
            R5('pv.cmpgeu.b',     'R',   '001111- ----- ----- 001 ----- 1010111'),
            R5('pv.cmpgeu.sc.b',  'R',   '001111- ----- ----- 101 ----- 1010111'),
            R5('pv.cmpgeu.sci.b', 'RRU', '001111- ----- ----- 111 ----- 1010111'),

            R5('pv.cmpltu.h',     'R',   '010001- ----- ----- 000 ----- 1010111'),
            R5('pv.cmpltu.sc.h',  'R',   '010001- ----- ----- 100 ----- 1010111'),
            R5('pv.cmpltu.sci.h', 'RRU', '010001- ----- ----- 110 ----- 1010111'),
            R5('pv.cmpltu.b',     'R',   '010001- ----- ----- 001 ----- 1010111'),
            R5('pv.cmpltu.sc.b',  'R',   '010001- ----- ----- 101 ----- 1010111'),
            R5('pv.cmpltu.sci.b', 'RRU', '010001- ----- ----- 111 ----- 1010111'),

            R5('pv.cmpleu.h',     'R',   '010011- ----- ----- 000 ----- 1010111'),
            R5('pv.cmpleu.sc.h',  'R',   '010011- ----- ----- 100 ----- 1010111'),
            R5('pv.cmpleu.sci.h', 'RRU', '010011- ----- ----- 110 ----- 1010111'),
            R5('pv.cmpleu.b',     'R',   '010011- ----- ----- 001 ----- 1010111'),
            R5('pv.cmpleu.sc.b',  'R',   '010011- ----- ----- 101 ----- 1010111'),
            R5('pv.cmpleu.sci.b', 'RRU', '010011- ----- ----- 111 ----- 1010111'),

            R5('p.beqimm',        'SB2', '------- ----- ----- 010 ----- 1100011', fast_handler=True, decode='bxx_decode'),
            R5('p.bneimm',        'SB2', '------- ----- ----- 011 ----- 1100011', fast_handler=True, decode='bxx_decode'),

            R5('p.mac',           'RRRR', '0100001 ----- ----- 000 ----- 0110011'),
            R5('p.msu',           'RRRR', '0100001 ----- ----- 001 ----- 0110011'),
            R5('p.mul',           'R',    '0000001 ----- ----- 000 ----- 0110011'),

            R5('p.muls',          'R',    '1000000 ----- ----- 000 ----- 1011011'),
            R5('p.mulhhs',        'R',    '1100000 ----- ----- 000 ----- 1011011'),
            R5('p.mulsN',         'RRRU2','10----- ----- ----- 000 ----- 1011011'),
            R5('p.mulhhsN',       'RRRU2','11----- ----- ----- 000 ----- 1011011'),
            R5('p.mulsNR',        'RRRU2','10----- ----- ----- 100 ----- 1011011'),
            R5('p.mulhhsNR',      'RRRU2','11----- ----- ----- 100 ----- 1011011'),

            R5('p.mulu',          'R',    '0000000 ----- ----- 000 ----- 1011011'),
            R5('p.mulhhu',        'R',    '0100000 ----- ----- 000 ----- 1011011'),
            R5('p.muluN',         'RRRU2','00----- ----- ----- 000 ----- 1011011'),
            R5('p.mulhhuN',       'RRRU2','01----- ----- ----- 000 ----- 1011011'),
            R5('p.muluNR',        'RRRU2','00----- ----- ----- 100 ----- 1011011'),
            R5('p.mulhhuNR',      'RRRU2','01----- ----- ----- 100 ----- 1011011'),

            R5('p.macs',          'RRRR', '1000000 ----- ----- 001 ----- 1011011'),
            R5('p.machhs',        'RRRR', '1100000 ----- ----- 001 ----- 1011011'),
            R5('p.macsN',         'RRRRU','10----- ----- ----- 001 ----- 1011011'),
            R5('p.machhsN',       'RRRRU','11----- ----- ----- 001 ----- 1011011'),
            R5('p.macsNR',        'RRRRU','10----- ----- ----- 101 ----- 1011011'),
            R5('p.machhsNR',      'RRRRU','11----- ----- ----- 101 ----- 1011011'),

            R5('p.macu',          'RRRR', '0000000 ----- ----- 001 ----- 1011011'),
            R5('p.machhu',        'RRRR', '0100000 ----- ----- 001 ----- 1011011'),
            R5('p.macuN',         'RRRRU','00----- ----- ----- 001 ----- 1011011'),
            R5('p.machhuN',       'RRRRU','01----- ----- ----- 001 ----- 1011011'),
            R5('p.macuNR',        'RRRRU','00----- ----- ----- 101 ----- 1011011'),
            R5('p.machhuNR',      'RRRRU','01----- ----- ----- 101 ----- 1011011'),

            R5('p.addNi',         'RRRU2','00----- ----- ----- 010 ----- 1011011'),
            R5('p.adduNi',        'RRRU2','10----- ----- ----- 010 ----- 1011011'),
            R5('p.addRNi',        'RRRU2','00----- ----- ----- 110 ----- 1011011'),
            R5('p.adduRNi',       'RRRU2','10----- ----- ----- 110 ----- 1011011'),

            R5('p.subNi',         'RRRU2','00----- ----- ----- 011 ----- 1011011'),
            R5('p.subuNi',        'RRRU2','10----- ----- ----- 011 ----- 1011011'),
            R5('p.subRNi',        'RRRU2','00----- ----- ----- 111 ----- 1011011'),
            R5('p.subuRNi',       'RRRU2','10----- ----- ----- 111 ----- 1011011'),

            R5('p.addN',          'RRRR2',    '0100000 ----- ----- 010 ----- 1011011'),
            R5('p.adduN',         'RRRR2',    '1100000 ----- ----- 010 ----- 1011011'),
            R5('p.addRN',         'RRRR2',    '0100000 ----- ----- 110 ----- 1011011'),
            R5('p.adduRN',        'RRRR2',    '1100000 ----- ----- 110 ----- 1011011'),

            R5('p.subN',          'RRRR2',    '0100000 ----- ----- 011 ----- 1011011'),
            R5('p.subuN',         'RRRR2',    '1100000 ----- ----- 011 ----- 1011011'),
            R5('p.subRN',         'RRRR2',    '0100000 ----- ----- 111 ----- 1011011'),
            R5('p.subuRN',        'RRRR2',    '1100000 ----- ----- 111 ----- 1011011'),

            R5('p.clipi',         'I1U',  '0001010 ----- ----- 001 ----- 0110011'),
            R5('p.clipui',        'I1U',  '0001010 ----- ----- 010 ----- 0110011'),
            R5('p.clip',          'R',    '0001010 ----- ----- 101 ----- 0110011'),
            R5('p.clipu',         'R',    '0001010 ----- ----- 110 ----- 0110011'),

            R5('p.extracti',      'I4U',  '11----- ----- ----- 000 ----- 0110011'),
            R5('p.extractui',     'I4U',  '11----- ----- ----- 001 ----- 0110011'),
            R5('p.extract',       'R',    '1000000 ----- ----- 000 ----- 0110011'),
            R5('p.extractu',      'R',    '1000000 ----- ----- 001 ----- 0110011'),
            R5('p.inserti',       'I5U',  '11----- ----- ----- 010 ----- 0110011'),
            R5('p.insert',        'I5U2', '1000000 ----- ----- 010 ----- 0110011'),
            R5('p.bseti',         'I4U',  '11----- ----- ----- 100 ----- 0110011'),
            R5('p.bclri',         'I4U',  '11----- ----- ----- 011 ----- 0110011'),
            R5('p.bset',          'R',    '1000000 ----- ----- 100 ----- 0110011'),
            R5('p.bclr',          'R',    '1000000 ----- ----- 011 ----- 0110011'),

        ])

class CoreV(IsaSubset):

    def __init__(self):
        super().__init__(name='corev', instrs=[

            R5('LB_POSTINC',    'LPOST', '------- ----- ----- 000 ----- 0001011', L='cv.lb' , fast_handler=True, tags=["load"]),
            R5('LBU_POSTINC',   'LPOST', '------- ----- ----- 100 ----- 0001011', L='cv.lbu', fast_handler=True, tags=["load"]),
            R5('LH_POSTINC',    'LPOST', '------- ----- ----- 001 ----- 0001011', L='cv.lh' , fast_handler=True, tags=["load"]),
            R5('LHU_POSTINC',   'LPOST', '------- ----- ----- 101 ----- 0001011', L='cv.lhu', fast_handler=True, tags=["load"]),
            R5('LW_POSTINC',    'LPOST', '------- ----- ----- 010 ----- 0001011', L='cv.lw' , fast_handler=True, tags=["load"]),

            R5('LB_RR_POSTINC',   'LRPOST',  '0000000 ----- ----- 111 ----- 0001011', L='cv.lb' , fast_handler=True, tags=["load"]),
            R5('LBU_RR_POSTINC',  'LRPOST',  '0100000 ----- ----- 111 ----- 0001011', L='cv.lbu', fast_handler=True, tags=["load"]),
            R5('LH_RR_POSTINC',   'LRPOST',  '0001000 ----- ----- 111 ----- 0001011', L='cv.lh' , fast_handler=True, tags=["load"]),
            R5('LHU_RR_POSTINC',  'LRPOST',  '0101000 ----- ----- 111 ----- 0001011', L='cv.lhu', fast_handler=True, tags=["load"]),
            R5('LW_RR_POSTINC',   'LRPOST',  '0010000 ----- ----- 111 ----- 0001011', L='cv.lw' , fast_handler=True, tags=["load"]),

            R5('LB_RR',    'LR', '0000000 ----- ----- 111 ----- 0000011', L='cv.lb' , fast_handler=True, tags=["load"]),
            R5('LBU_RR',   'LR', '0100000 ----- ----- 111 ----- 0000011', L='cv.lbu', fast_handler=True, tags=["load"]),
            R5('LH_RR',    'LR', '0001000 ----- ----- 111 ----- 0000011', L='cv.lh' , fast_handler=True, tags=["load"]),
            R5('LHU_RR',   'LR', '0101000 ----- ----- 111 ----- 0000011', L='cv.lhu', fast_handler=True, tags=["load"]),
            R5('LW_RR',    'LR', '0010000 ----- ----- 111 ----- 0000011', L='cv.lw' , fast_handler=True, tags=["load"]),

            R5('SB_POSTINC',    'SPOST', '------- ----- ----- 000 ----- 0101011', L='cv.sb' , fast_handler=True),
            R5('SH_POSTINC',    'SPOST', '------- ----- ----- 001 ----- 0101011', L='cv.sh' , fast_handler=True),
            R5('SW_POSTINC',    'SPOST', '------- ----- ----- 010 ----- 0101011', L='cv.sw' , fast_handler=True),

            R5('SB_RR_POSTINC',   'SRPOST', '0000000 ----- ----- 100 ----- 0101011',  L='cv.sb' , fast_handler=True),
            R5('SH_RR_POSTINC',   'SRPOST', '0000000 ----- ----- 101 ----- 0101011',  L='cv.sh' , fast_handler=True),
            R5('SW_RR_POSTINC',   'SRPOST', '0000000 ----- ----- 110 ----- 0101011',  L='cv.sw' , fast_handler=True),

            R5('SB_RR',    'SR', '0000000 ----- ----- 100 ----- 0100011', L='cv.sb', fast_handler=True),
            R5('SH_RR',    'SR', '0000000 ----- ----- 101 ----- 0100011', L='cv.sh', fast_handler=True),
            R5('SW_RR',    'SR', '0000000 ----- ----- 110 ----- 0100011', L='cv.sw', fast_handler=True),

            R5('cv.elw',           'L',   '------- ----- ----- 110 ----- 0000011', tags=["load"]),

            R5('cv.starti','HL0','------- ----- 00000 000 0000- 1111011'),
            R5('cv.endi',  'HL0','------- ----- 00000 001 0000- 1111011'),
            R5('cv.count', 'HL0','0000000 00000 ----- 010 0000- 1111011'),
            R5('cv.counti','HL0','------- ----- 00000 011 0000- 1111011'),
            R5('cv.setup', 'HL0','------- ----- ----- 100 0000- 1111011'),
            R5('cv.setupi','HL1','------- ----- ----- 101 0000- 1111011'),

            R5('cv.extract',      'I4U',  '11----- ----- ----- 000 ----- 0110011'),
            R5('cv.extractu',     'I4U',  '11----- ----- ----- 001 ----- 0110011'),
            R5('cv.insert',       'I5U',  '11----- ----- ----- 010 ----- 0110011'),
            R5('cv.bclr',         'I4U',  '11----- ----- ----- 011 ----- 0110011'),
            R5('cv.bset',         'I4U',  '11----- ----- ----- 100 ----- 0110011'),
            R5('cv.extractr',     'R',    '1000000 ----- ----- 000 ----- 0110011'),
            R5('cv.extractur',    'R',    '1000000 ----- ----- 001 ----- 0110011'),
            R5('cv.insertr',      'I5U2', '1000000 ----- ----- 010 ----- 0110011'),
            R5('cv.bclrr',        'R',    '1000000 ----- ----- 011 ----- 0110011'),
            R5('cv.bsetr',        'R',    '1000000 ----- ----- 100 ----- 0110011'),
            R5('cv.bitrev',       'BITREV',   '11000-- ----- ----- 101 ----- 0110011', mapTo="cv_bitrev"),

            R5('cv.ror', 'R',  '0000100 ----- ----- 101 ----- 0110011'),
            R5('cv.ff1', 'R1',  '0001000 00000 ----- 000 ----- 0110011'),
            R5('cv.fl1','R1',   '0001000 00000 ----- 001 ----- 0110011'),
            R5('cv.clb', 'R1',  '0001000 00000 ----- 010 ----- 0110011'),
            R5('cv.cnt', 'R1',  '0001000 00000 ----- 011 ----- 0110011'),

            R5('cv.abs',  'R1', '0000010 00000 ----- 000 ----- 0110011'),
            R5('cv.slet','R',  '0000010 ----- ----- 010 ----- 0110011'),
            R5('cv.sletu','R', '0000010 ----- ----- 011 ----- 0110011'),
            R5('cv.min', 'R',  '0000010 ----- ----- 100 ----- 0110011'),
            R5('cv.minu','R',  '0000010 ----- ----- 101 ----- 0110011'),
            R5('cv.max', 'R',  '0000010 ----- ----- 110 ----- 0110011'),
            R5('cv.maxu','R',  '0000010 ----- ----- 111 ----- 0110011'),
            R5('cv.exths','R1', '0001000 00000 ----- 100 ----- 0110011'),
            R5('cv.exthz','R1', '0001000 00000 ----- 101 ----- 0110011'),
            R5('cv.extbs','R1', '0001000 00000 ----- 110 ----- 0110011'),
            R5('cv.extbz','R1', '0001000 00000 ----- 111 ----- 0110011'),

            R5('cv.clip',         'I1U',  '0001010 ----- ----- 001 ----- 0110011'),
            R5('cv.clipu',        'I1U',  '0001010 ----- ----- 010 ----- 0110011'),
            R5('cv.clipr',          'R',    '0001010 ----- ----- 101 ----- 0110011'),
            R5('cv.clipur',         'R',    '0001010 ----- ----- 110 ----- 0110011'),

            R5('cv.addN',         'RRRU2','00----- ----- ----- 010 ----- 1011011'),
            R5('cv.adduN',        'RRRU2','10----- ----- ----- 010 ----- 1011011'),
            R5('cv.addRN',        'RRRU2','00----- ----- ----- 110 ----- 1011011'),
            R5('cv.adduRN',       'RRRU2','10----- ----- ----- 110 ----- 1011011'),

            R5('cv.subN',         'RRRU2','00----- ----- ----- 011 ----- 1011011'),
            R5('cv.subuN',        'RRRU2','10----- ----- ----- 011 ----- 1011011'),
            R5('cv.subRN',        'RRRU2','00----- ----- ----- 111 ----- 1011011'),
            R5('cv.subuRN',       'RRRU2','10----- ----- ----- 111 ----- 1011011'),

            R5('cv.addNr',          'RRRR2',    '0100000 ----- ----- 010 ----- 1011011'),
            R5('cv.adduNr',         'RRRR2',    '1100000 ----- ----- 010 ----- 1011011'),
            R5('cv.addRNr',         'RRRR2',    '0100000 ----- ----- 110 ----- 1011011'),
            R5('cv.adduRNr',        'RRRR2',    '1100000 ----- ----- 110 ----- 1011011'),

            R5('cv.subNr',          'RRRR2',    '0100000 ----- ----- 011 ----- 1011011'),
            R5('cv.subuNr',         'RRRR2',    '1100000 ----- ----- 011 ----- 1011011'),
            R5('cv.subRNr',         'RRRR2',    '0100000 ----- ----- 111 ----- 1011011'),
            R5('cv.subuRNr',        'RRRR2',    '1100000 ----- ----- 111 ----- 1011011'),

            R5('cv.beqimm',        'SB2', '------- ----- ----- 010 ----- 1100011', fast_handler=True, decode='bxx_decode'),
            R5('cv.bneimm',        'SB2', '------- ----- ----- 011 ----- 1100011', fast_handler=True, decode='bxx_decode'),

            R5('cv.mac',           'RRRR', '0100001 ----- ----- 000 ----- 0110011'),
            R5('cv.msu',           'RRRR', '0100001 ----- ----- 001 ----- 0110011'),

            R5('cv.muls',          'R',    '1000000 ----- ----- 000 ----- 1011011'),
            R5('cv.mulhhs',        'R',    '1100000 ----- ----- 000 ----- 1011011'),
            R5('cv.mulsN',         'RRRU2','10----- ----- ----- 000 ----- 1011011'),
            R5('cv.mulhhsN',       'RRRU2','11----- ----- ----- 000 ----- 1011011'),
            R5('cv.mulsRN',        'RRRU2','10----- ----- ----- 100 ----- 1011011'),
            R5('cv.mulhhsRN',      'RRRU2','11----- ----- ----- 100 ----- 1011011'),
            R5('cv.mulu',          'R',    '0000000 ----- ----- 000 ----- 1011011'),
            R5('cv.mulhhu',        'R',    '0100000 ----- ----- 000 ----- 1011011'),
            R5('cv.muluN',         'RRRU2','00----- ----- ----- 000 ----- 1011011'),
            R5('cv.mulhhuN',       'RRRU2','01----- ----- ----- 000 ----- 1011011'),
            R5('cv.muluRN',        'RRRU2','00----- ----- ----- 100 ----- 1011011'),
            R5('cv.mulhhuRN',      'RRRU2','01----- ----- ----- 100 ----- 1011011'),
            R5('cv.macsN',         'RRRRU','10----- ----- ----- 001 ----- 1011011'),
            R5('cv.machhsN',       'RRRRU','11----- ----- ----- 001 ----- 1011011'),
            R5('cv.macsRN',        'RRRRU','10----- ----- ----- 101 ----- 1011011'),
            R5('cv.machhsRN',      'RRRRU','11----- ----- ----- 101 ----- 1011011'),
            R5('cv.macuN',         'RRRRU','00----- ----- ----- 001 ----- 1011011'),
            R5('cv.machhuN',       'RRRRU','01----- ----- ----- 001 ----- 1011011'),
            R5('cv.macuRN',        'RRRRU','00----- ----- ----- 101 ----- 1011011'),
            R5('cv.machhuRN',      'RRRRU','01----- ----- ----- 101 ----- 1011011'),

        ])

# created list for pulp_nn isa extension
class PulpNn(IsaSubset):

    def __init__(self):
        super().__init__(name='pulpnn', instrs=[

            #add vector instruction ((missing scalar version))
            R5('pv.add.n',         'R',     '0000000 ----- ----- 010 ----- 1010111'),
            R5('pv.add.sc.n',      'R',     '0000000 ----- ----- 011 ----- 1010111'),
            R5('pv.add.c',         'R',     '0000001 ----- ----- 010 ----- 1010111'),
            R5('pv.add.sc.c',      'R',     '0000001 ----- ----- 011 ----- 1010111'),
            #sub vector instruction ((missing scalar version))
            R5('pv.sub.n',         'R',     '0000100 ----- ----- 010 ----- 1010111'),
            R5('pv.sub.sc.n',      'R',     '0000100 ----- ----- 011 ----- 1010111'),
            R5('pv.sub.c',         'R',     '0000101 ----- ----- 010 ----- 1010111'),
            R5('pv.sub.sc.c',      'R',     '0000101 ----- ----- 011 ----- 1010111'),
            # avg signed operands
            R5('pv.avg.n',        'R',   '0001000 ----- ----- 010 ----- 1010111'),
            R5('pv.avg.sc.n',     'R',   '0001000 ----- ----- 011 ----- 1010111'),
            R5('pv.avg.c',        'R',   '0001001 ----- ----- 010 ----- 1010111'),
            R5('pv.avg.sc.c',     'R',   '0001001 ----- ----- 011 ----- 1010111'),
            # avg unsigned operands
            R5('pv.avgu.n',        'R',   '0001100 ----- ----- 010 ----- 1010111'),
            R5('pv.avgu.sc.n',     'R',   '0001100 ----- ----- 011 ----- 1010111'),
            R5('pv.avgu.c',        'R',   '0001101 ----- ----- 010 ----- 1010111'),
            R5('pv.avgu.sc.c',     'R',   '0001101 ----- ----- 011 ----- 1010111'),
            # max signed operands
            R5('pv.max.n',        'R',   '0011000 ----- ----- 010 ----- 1010111'),
            R5('pv.max.sc.n',     'R',   '0011000 ----- ----- 011 ----- 1010111'),
            R5('pv.max.c',        'R',   '0011001 ----- ----- 010 ----- 1010111'),
            R5('pv.max.sc.c',     'R',   '0011001 ----- ----- 011 ----- 1010111'),
            # max unsigned operands
            R5('pv.maxu.n',        'R',   '0011100 ----- ----- 010 ----- 1010111'),
            R5('pv.maxu.sc.n',     'R',   '0011100 ----- ----- 011 ----- 1010111'),
            R5('pv.maxu.c',        'R',   '0011101 ----- ----- 010 ----- 1010111'),
            R5('pv.maxu.sc.c',     'R',   '0011101 ----- ----- 011 ----- 1010111'),
            # min signed operands
            R5('pv.min.n',        'R',   '0010000 ----- ----- 010 ----- 1010111'),
            R5('pv.min.sc.n',     'R',   '0010000 ----- ----- 011 ----- 1010111'),
            R5('pv.min.c',        'R',   '0010001 ----- ----- 010 ----- 1010111'),
            R5('pv.min.sc.c',     'R',   '0010001 ----- ----- 011 ----- 1010111'),
            # min unsigned operands
            R5('pv.minu.n',        'R',   '0010100 ----- ----- 010 ----- 1010111'),
            R5('pv.minu.sc.n',     'R',   '0010100 ----- ----- 011 ----- 1010111'),
            R5('pv.minu.c',        'R',   '0010101 ----- ----- 010 ----- 1010111'),
            R5('pv.minu.sc.c',     'R',   '0010101 ----- ----- 011 ----- 1010111'),
            # srl vector operations
            R5('pv.srl.n',        'R',   '0100000 ----- ----- 010 ----- 1010111'),
            R5('pv.srl.sc.n',     'R',   '0100000 ----- ----- 011 ----- 1010111'),
            R5('pv.srl.c',        'R',   '0100001 ----- ----- 010 ----- 1010111'),
            R5('pv.srl.sc.c',     'R',   '0100001 ----- ----- 011 ----- 1010111'),
            # sra vector operations
            R5('pv.sra.n',        'R',   '0100100 ----- ----- 010 ----- 1010111'),
            R5('pv.sra.sc.n',     'R',   '0100100 ----- ----- 011 ----- 1010111'),
            R5('pv.sra.c',        'R',   '0100101 ----- ----- 010 ----- 1010111'),
            R5('pv.sra.sc.c',     'R',   '0100101 ----- ----- 011 ----- 1010111'),
            # sll vector operations
            R5('pv.sll.n',        'R',   '0101000 ----- ----- 010 ----- 1010111'),
            R5('pv.sll.sc.n',     'R',   '0101000 ----- ----- 011 ----- 1010111'),
            R5('pv.sll.c',        'R',   '0101001 ----- ----- 010 ----- 1010111'),
            R5('pv.sll.sc.c',     'R',   '0101001 ----- ----- 011 ----- 1010111'),
            # or vector operations
            R5('pv.or.n',        'R',   '0101100 ----- ----- 010 ----- 1010111'),
            R5('pv.or.sc.n',     'R',   '0101100 ----- ----- 011 ----- 1010111'),
            R5('pv.or.c',        'R',   '0101101 ----- ----- 010 ----- 1010111'),
            R5('pv.or.sc.c',     'R',   '0101101 ----- ----- 011 ----- 1010111'),
            # xor vector operations
            R5('pv.xor.n',        'R',   '0110000 ----- ----- 010 ----- 1010111'),
            R5('pv.xor.sc.n',     'R',   '0110000 ----- ----- 011 ----- 1010111'),
            R5('pv.xor.c',        'R',   '0110001 ----- ----- 010 ----- 1010111'),
            R5('pv.xor.sc.c',     'R',   '0110001 ----- ----- 011 ----- 1010111'),
            # and vector operations
            R5('pv.and.n',        'R',   '0110100 ----- ----- 010 ----- 1010111'),
            R5('pv.and.sc.n',     'R',   '0110100 ----- ----- 011 ----- 1010111'),
            R5('pv.and.c',        'R',   '0110101 ----- ----- 010 ----- 1010111'),
            R5('pv.and.sc.c',     'R',   '0110101 ----- ----- 011 ----- 1010111'),
            # abs vector operations
            R5('pv.abs.n',        'R',   '0111000 ----- ----- 010 ----- 1010111'),
            R5('pv.abs.c',        'R',   '0111001 ----- ----- 010 ----- 1010111'),
            #dotup
            R5('pv.dotup.n',     'RRRR','1000000 ----- ----- 010 ----- 1010111'),
            R5('pv.dotup.n.sc',  'RRRR','1000000 ----- ----- 011 ----- 1010111'),
            R5('pv.dotup.c',     'RRRR','1000001 ----- ----- 010 ----- 1010111'),
            R5('pv.dotup.c.sc',  'RRRR','1000001 ----- ----- 011 ----- 1010111'),
            R5('pv.dotusp.n',     'RRRR','1000100 ----- ----- 010 ----- 1010111'),
            R5('pv.dotusp.n.sc',  'RRRR','1000100 ----- ----- 011 ----- 1010111'),
            R5('pv.dotusp.c',     'RRRR','1000101 ----- ----- 010 ----- 1010111'),
            R5('pv.dotusp.c.sc',  'RRRR','1000101 ----- ----- 011 ----- 1010111'),
            R5('pv.dotsp.n',     'RRRR','1001100 ----- ----- 010 ----- 1010111'),
            R5('pv.dotsp.n.sc',  'RRRR','1001100 ----- ----- 011 ----- 1010111'),
            R5('pv.dotsp.c',     'RRRR','1001101 ----- ----- 010 ----- 1010111'),
            R5('pv.dotsp.c.sc',  'RRRR','1001101 ----- ----- 011 ----- 1010111'),
            R5('pv.sdotup.n',     'RRRR','1010000 ----- ----- 010 ----- 1010111'),
            R5('pv.sdotup.n.sc',  'RRRR','1010000 ----- ----- 011 ----- 1010111'),
            R5('pv.sdotup.c',     'RRRR','1010001 ----- ----- 010 ----- 1010111'),
            R5('pv.sdotup.c.sc',  'RRRR','1010001 ----- ----- 011 ----- 1010111'),
            R5('pv.sdotusp.n',     'RRRR','1010100 ----- ----- 010 ----- 1010111'),
            R5('pv.sdotusp.n.sc',  'RRRR','1010100 ----- ----- 011 ----- 1010111'),
            R5('pv.sdotusp.c',     'RRRR','1010101 ----- ----- 010 ----- 1010111'),
            R5('pv.sdotusp.c.sc',  'RRRR','1010101 ----- ----- 011 ----- 1010111'),
            R5('pv.sdotsp.n',     'RRRR','1011100 ----- ----- 010 ----- 1010111'),
            R5('pv.sdotsp.n.sc',  'RRRR','1011100 ----- ----- 011 ----- 1010111'),
            R5('pv.sdotsp.c',     'RRRR','1011101 ----- ----- 010 ----- 1010111'),
            R5('pv.sdotsp.c.sc',  'RRRR','1011101 ----- ----- 011 ----- 1010111'),
            # quantization
            R5('pv.qnt.n',       'LRR','1110000 ----- ----- 010 ----- 1010111'),
            # mac & load
            R5('pv.mlsdotup.h', 'RRRU3', '1110000 ----- ----- 000 ----- 1110111'),
            R5('pv.mlsdotusp.h', 'RRRU3', '1110100 ----- ----- 000 ----- 1110111'),
            R5('pv.mlsdotsup.h', 'RRRU3', '1101100 ----- ----- 000 ----- 1110111'),
            R5('pv.mlsdotsp.h', 'RRRU3', '1111100 ----- ----- 000 ----- 1110111'),
            R5('pv.mlsdotup.b', 'RRRU3', '1110000 ----- ----- 001 ----- 1110111'),
            R5('pv.mlsdotusp.b', 'RRRU3', '1110100 ----- ----- 001 ----- 1110111'),
            R5('pv.mlsdotsup.b', 'RRRU3', '1101100 ----- ----- 001 ----- 1110111'),
            R5('pv.mlsdotsp.b', 'RRRU3', '1111100 ----- ----- 001 ----- 1110111'),
            R5('pv.mlsdotup.n', 'RRRU3', '1110000 ----- ----- 010 ----- 1110111'),
            R5('pv.mlsdotusp.n', 'RRRU3', '1110100 ----- ----- 010 ----- 1110111'),
            R5('pv.mlsdotsup.n', 'RRRU3', '1101100 ----- ----- 010 ----- 1110111'),
            R5('pv.mlsdotsp.n', 'RRRU3', '1111100 ----- ----- 010 ----- 1110111'),
            R5('pv.mlsdotup.c', 'RRRU3', '1110000 ----- ----- 011 ----- 1110111'),
            R5('pv.mlsdotusp.c', 'RRRU3', '1110100 ----- ----- 011 ----- 1110111'),
            R5('pv.mlsdotsup.c', 'RRRU3', '1101100 ----- ----- 011 ----- 1110111'),
            R5('pv.mlsdotsp.c', 'RRRU3', '1111100 ----- ----- 011 ----- 1110111'),
        ])

class RnnExt(IsaSubset):

    def __init__(self):
        super().__init__(name='rnnext', instrs=[
            R5('pl.sdotsp.h.0', 'LRRRR','101110- ----- ----- 000 ----- 1110111'),
            R5('pl.sdotsp.h.1', 'LRRRR','101111- ----- ----- 000 ----- 1110111'),
            R5('pl.tanh',     'R1',   '1111100 00000 ----- 000 ----- 1110111'),
            R5('pl.sig',      'R1',   '1111100 00000 ----- 001 ----- 1110111'),
        ])

class Gap9(IsaSubset):

    def __init__(self):
        super().__init__(name='gap9', instrs=[
            R5('pv.cplxmul.h.i',      'RRRR',   '0101011 ----- ----- 000 ----- 1010111', mapTo="gap9_CPLXMUL_H_I"),
            R5('pv.cplxmul.h.i.div2', 'RRRR',   '0101011 ----- ----- 010 ----- 1010111', mapTo="gap9_CPLXMUL_H_I_DIV2"),
            R5('pv.cplxmul.h.i.div4', 'RRRR',   '0101011 ----- ----- 100 ----- 1010111', mapTo="gap9_CPLXMUL_H_I_DIV4"),
            R5('pv.cplxmul.h.i.div8', 'RRRR',   '0101011 ----- ----- 110 ----- 1010111', mapTo="gap9_CPLXMUL_H_I_DIV8"),

            R5('pv.cplxmul.h.r',      'RRRR',   '0101010 ----- ----- 000 ----- 1010111', mapTo="gap9_CPLXMUL_H_R"),
            R5('pv.cplxmul.h.r.div2', 'RRRR',   '0101010 ----- ----- 010 ----- 1010111', mapTo="gap9_CPLXMUL_H_R_DIV2"),
            R5('pv.cplxmul.h.r.div4', 'RRRR',   '0101010 ----- ----- 100 ----- 1010111', mapTo="gap9_CPLXMUL_H_R_DIV4"),
            R5('pv.cplxmul.h.r.div8', 'RRRR',   '0101010 ----- ----- 110 ----- 1010111', mapTo="gap9_CPLXMUL_H_R_DIV8"),

            R5('pv.subrotmj.h',     'R',   '0110110 ----- ----- 000 ----- 1010111', mapTo="gap9_VEC_ADD_16_ROTMJ"),
            R5('pv.subrotmj.h.div2','R',   '0110110 ----- ----- 010 ----- 1010111', mapTo="gap9_VEC_ADD_16_ROTMJ_DIV2"),
            R5('pv.subrotmj.h.div4','R',   '0110110 ----- ----- 100 ----- 1010111', mapTo="gap9_VEC_ADD_16_ROTMJ_DIV4"),
            R5('pv.subrotmj.h.div8','R',   '0110110 ----- ----- 110 ----- 1010111', mapTo="gap9_VEC_ADD_16_ROTMJ_DIV8"),

            R5('pv.cplxconj.h',     'R1',  '0101110 00000 ----- 000 ----- 1010111', mapTo="gap9_CPLX_CONJ_16"),

            R5('pv.add.h.div2',     'R',   '0111010 ----- ----- 010 ----- 1010111', mapTo="gap9_VEC_ADD_16_DIV2"),
            R5('pv.add.h.div4',     'R',   '0111010 ----- ----- 100 ----- 1010111', mapTo="gap9_VEC_ADD_16_DIV4"),
            R5('pv.add.h.div8',     'R',   '0111010 ----- ----- 110 ----- 1010111', mapTo="gap9_VEC_ADD_16_DIV8"),

            R5('pv.sub.h.div2',     'R',   '0110010 ----- ----- 010 ----- 1010111', mapTo="gap9_VEC_SUB_16_DIV2"),
            R5('pv.sub.h.div4',     'R',   '0110010 ----- ----- 100 ----- 1010111', mapTo="gap9_VEC_SUB_16_DIV4"),
            R5('pv.sub.h.div8',     'R',   '0110010 ----- ----- 110 ----- 1010111', mapTo="gap9_VEC_SUB_16_DIV8"),

            R5('pv.pack.h.h',       'R',   '1101001 ----- ----- 000 ----- 1010111', mapTo="gap9_VEC_PACK_SC_H_16"),

            R5('p.bitrev',          'BITREV',   '11000-- ----- ----- 101 ----- 0110011', mapTo="gap9_BITREV"),
        ])

class Int64(IsaSubset):

    def __init__(self):
        super().__init__(name='int64', instrs=[
            R5('add.d',      'R2x64_W64',      '0010000 ----- ----- 000 ----- 0110011'),
            R5('sub.d',      'R2x64_W64',      '0110000 ----- ----- 000 ----- 0110011'),
            R5('sll.d',      'R2x64_W64',      '0010000 ----- ----- 001 ----- 0110011'),
            R5('slt.d',      'R2x64_W32',      '0011000 ----- ----- 010 ----- 0110011'),
            R5('sltu.d',     'R2x64_W32',      '0011000 ----- ----- 011 ----- 0110011'),
            R5('xor.d',      'R2x64_W64',      '0010000 ----- ----- 100 ----- 0110011'),
            R5('srl.d',      'R2x64_W64',      '0010000 ----- ----- 101 ----- 0110011'),
            R5('sra.d',      'R2x64_W64',      '0110000 ----- ----- 101 ----- 0110011'),
            R5('or.d',       'R2x64_W64',      '0110000 ----- ----- 110 ----- 0110011'),
            R5('and.d',      'R2x64_W64',      '0110000 ----- ----- 111 ----- 0110011'),

            R5('slli.d',     'R1x64puImm_W64', '0010000 ----- ----- 001 ----- 0010011'),
            R5('srli.d',     'R1x64puImm_W64', '0010010 ----- ----- 101 ----- 0010011'),
            R5('srai.d',     'R1x64puImm_W64', '0110010 ----- ----- 101 ----- 0010011'),
            R5('addi.d',     'R1x64psImm_W64', '0010001 ----- ----- 001 ----- 0010011'),

            R5('slti.d',     'R1x64psImm_W32', '0011000 ----- ----- 010 ----- 0011011'),
            R5('sltiu.d',    'R1x64puImm_W32', '0011000 ----- ----- 011 ----- 0011011'),
            R5('xori.d',     'R1x64puImm_W64', '0010000 ----- ----- 100 ----- 0011011'),
            R5('ori.d',      'R1x64puImm_W64', '0010000 ----- ----- 110 ----- 0011011'),
            R5('andi.d',     'R1x64puImm_W64', '0010000 ----- ----- 111 ----- 0011011'),

            R5('p.abs.d',    'R1x64_W64',      '0010010 00000 ----- 000 ----- 0110011'),
            R5('p.seq.d',    'R2x64_W32',      '0011011 ----- ----- 010 ----- 0110011'),
            R5('p.slet.d',   'R2x64_W32',      '0011010 ----- ----- 010 ----- 0110011'),
            R5('p.sletu.d',  'R2x64_W32',      '0011010 ----- ----- 011 ----- 0110011'),
            R5('p.sne.d',    'R2x64_W32',      '0011011 ----- ----- 011 ----- 0110011'),
            R5('p.min.d',    'R2x64_W64',      '0010010 ----- ----- 100 ----- 0110011'),
            R5('p.minu.d',   'R2x64_W64',      '0010010 ----- ----- 101 ----- 0110011'),
            R5('p.max.d',    'R2x64_W64',      '0010010 ----- ----- 110 ----- 0110011'),
            R5('p.maxu.d',   'R2x64_W64',      '0010010 ----- ----- 111 ----- 0110011'),
            R5('p.cnt.d',    'R1x64_W32',      '0011010 00000 ----- 001 ----- 0110011'),
            R5('p.exths.d',  'R1x32_W64',      '0110010 00000 ----- 000 ----- 0110011'),
            R5('p.exthz.d',  'R1x32_W64',      '0110010 00000 ----- 001 ----- 0110011'),
            R5('p.extbs.d',  'R1x32_W64',      '0110010 00000 ----- 010 ----- 0110011'),
            R5('p.extbz.d',  'R1x32_W64',      '0110010 00000 ----- 011 ----- 0110011'),
            R5('p.extws.d',  'R1x32_W64',      '0110010 00000 ----- 100 ----- 0110011'),
            R5('p.extwz.d',  'R1x32_W64',      '0110010 00000 ----- 101 ----- 0110011'),

            R5('p.mac.d',    'R2x32p64_W64',   '0111001 ----- ----- 000 ----- 0110011'),
            R5('p.msu.d',    'R2x32p64_W64',   '0111001 ----- ----- 001 ----- 0110011'),
            R5('p.macu.d',   'R2x32p64_W64',   '0111001 ----- ----- 010 ----- 0110011'),
            R5('p.msuu.d',   'R2x32p64_W64',   '0111001 ----- ----- 011 ----- 0110011'),
            R5('p.muls.d',   'R2x32_W64',      '0111001 ----- ----- 100 ----- 0110011'),
            R5('p.mulu.d',   'R2x32_W64',      '0111001 ----- ----- 101 ----- 0110011'),
            R5('p.mulsh.d',  'R2x32_W64',      '0111001 ----- ----- 110 ----- 0110011'),
            R5('p.muluh.d',  'R2x32_W64',      '0111001 ----- ----- 111 ----- 0110011'),
        ])



class RiscvIsa(Isa):

    def __init__(self, name, isa, inc_priv=True, inc_supervisor=True):
        super().__init__(name, isa, [])

        self.full_name = f'isa_{self.name}'

        self.generated = False

        trees = []

        if isa[0:4] == 'rv32':
            self.word_size = 32
        elif isa[0:4] == 'rv64':
            self.word_size = 64
        else:
            raise RuntimeError('Isa should start with either rv32 or rv64')

        extensions = isa[4:]

        while len(extensions) > 0:
            if extensions[0] == 'i':
                if self.word_size == 32:
                    self.add_tree(IsaDecodeTree('i', [Rv32i()]))
                else:
                    self.add_tree(IsaDecodeTree('i', [Rv64i(), Rv32i()]))
                extensions = extensions[1:]

            elif extensions[0] == 'm':
                if self.word_size == 32:
                    self.add_tree(IsaDecodeTree('m', [Rv32m()]))
                else:
                    self.add_tree(IsaDecodeTree('m', [Rv32m(), Rv64m()]))
                extensions = extensions[1:]

            elif extensions[0] == 'a':
                if self.word_size == 32:
                    self.add_tree(IsaDecodeTree('a', [Rv32a()]))
                else:
                    self.add_tree(IsaDecodeTree('a', [Rv32a(), Rv64a()]))
                extensions = extensions[1:]

            elif extensions[0] == 'c':
                if self.word_size == 32:
                    self.add_tree(IsaDecodeTree('c', [Rv32c()]))
                else:
                    self.add_tree(IsaDecodeTree('c', [Rv64c()]))
                extensions = extensions[1:]

            elif extensions[0] == 'f':
                self.add_tree(IsaDecodeTree('f', [Rv32f()]))
                extensions = extensions[1:]

            elif extensions[0] == 'd':
                self.add_tree(IsaDecodeTree('d', [Rv32d()]))
                extensions = extensions[1:]

            elif extensions[0] == 'X':

                extensions = ''

            else:
                extensions = extensions[1:]

        priv_trees = []
        if inc_priv:
            priv_trees.append(Priv())
            priv_trees.append(TrapReturn())
        if inc_supervisor:
            priv_trees.append(PrivSmmu())

        self.add_tree(IsaDecodeTree('priv', priv_trees))


    def get_source(self):
        return f'{self.full_name}.cpp'

    def gen(self, component, builddir, installdir):

        if not self.generated:

            self.generated = True

            full_name = os.path.join(builddir, self.full_name)

            with open(f'{full_name}.cpp.new', 'w') as isaFile:
                with open(f'{full_name}.hpp.new', 'w') as isaFileHeader:
                    Isa.gen(self, isaFile, isaFileHeader)

            if not os.path.exists(f'{full_name}.cpp') or \
                    not filecmp.cmp(f'{full_name}.cpp.new', f'{full_name}.cpp', shallow=False):
                shutil.move(f'{full_name}.cpp.new', f'{full_name}.cpp')

            if not os.path.exists(f'{full_name}.hpp') or \
                    not filecmp.cmp(f'{full_name}.hpp.new', f'{full_name}.hpp', shallow=False):
                shutil.move(f'{full_name}.hpp.new', f'{full_name}.hpp')
