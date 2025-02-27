/*
 * Copyright (C) 2020 GreenWaves Technologies, SAS, ETH Zurich and
 *                    University of Bologna
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/* 
 * Authors: Germain Haugou, GreenWaves Technologies (germain.haugou@greenwaves-technologies.com)
 */

#ifndef __GV__DPI_CHIP_WRAPPER_H__
#define __GV__DPI_CHIP_WRAPPER_H__

#include <string>
#include <gv/gvsoc.hpp>

class Dpi_chip_wrapper_callback : public gv::Wire_binding
{
public:
    void update(int data);
    void (*function)(void *_this, int64_t, int);
    void *_this;

    int *pad_value;
    std::string name;
    bool is_cs;
    bool is_sck;
    void *group;
    int cs_id;
    gv::Wire_user *handle;
};

#endif