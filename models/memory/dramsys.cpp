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

#include <vp/vp.hpp>
#include <vp/itf/io.hpp>
#include <stdio.h>
#include <string.h>
#include <systemc.h>

class ddr : public vp::component
{

public:
    ddr(js::config *config);

    int build();
    void start();

    static vp::io_req_status_e req(void *__this, vp::io_req *req);

private:
    vp::trace trace;
    vp::io_slave in;
};

ddr::ddr(js::config *config)
    : vp::component(config)
{
}

vp::io_req_status_e ddr::req(void *__this, vp::io_req *req)
{
    ddr *_this = (ddr *)__this;

    uint64_t offset = req->get_addr();
    uint8_t *data = req->get_data();
    uint64_t size = req->get_size();

    _this->trace.msg("IO access (offset: 0x%x, size: 0x%x, is_write: %d)\n", offset, size, req->get_is_write());

    return vp::IO_REQ_OK;
}


int ddr::build()
{
    traces.new_trace("trace", &trace, vp::DEBUG);

    in.set_req_meth(&ddr::req);
    new_slave_port("input", &in);

    return 0;
}

void ddr::start()
{
}

extern "C" vp::component *vp_constructor(js::config *config)
{
    return new ddr(config);
}
