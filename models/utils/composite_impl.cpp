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
#include <utils/composite.hpp>




composite::composite(js::config *config)
    : vp::component(config)
{
}


void composite::dump_traces(FILE *file)
{
    this->power.get_power_trace()->dump(file);
}


int composite::build()
{
    this->create_comps();
    this->create_ports();
    this->create_bindings();

    return 0;
}


void composite::start()
{
}



void composite::add_port(std::string name, vp::port *port)
{
    vp_assert_always(port != NULL, this->get_trace(), "Adding NULL port\n");
    //vp_assert_always(this->ports[name] == NULL, this->get_trace(), "Adding already existing port\n");
    this->ports[name] = port;
}

void composite::power_supply_set(int state)
{
    //printf("%s power set %d\n", this->get_path().c_str(), state);
}


extern "C" vp::component *vp_constructor(js::config *config)
{
    return new composite(config);
}
