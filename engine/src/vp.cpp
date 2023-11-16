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


#include <iostream>
#include <sstream>
#include <string>
#include <stdio.h>
#include <vp/vp.hpp>
#include <stdio.h>
#include "string.h"
#include <iostream>
#include <sstream>
#include <string>
#include <dlfcn.h>
#include <algorithm>
#include <string>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <poll.h>
#include <signal.h>
#include <regex>
#include <sys/types.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <vp/time/time_scheduler.hpp>
#include <vp/proxy.hpp>
#include <vp/queue.hpp>
#include <vp/signal.hpp>
#include <vp/proxy_client.hpp>
#include <vp/launcher.hpp>
#include <sys/stat.h>
#include <vp/trace/trace_engine.hpp>


extern "C" long long int dpi_time_ps();



char vp_error[VP_ERROR_SIZE];



Gv_proxy *proxy = NULL;







void vp::component_clock::clk_reg(component *_this, component *clock)
{
    _this->clock = (clock_engine *)clock;
    for (auto &x : _this->childs)
    {
        x->clk_reg(x, clock);
    }
    for (clock_event *event: _this->events)
    {
        event->set_clock(_this->clock);
    }
}


void vp::component_clock::clk_set_frequency(component *_this, int64_t frequency)
{
    _this->power.set_frequency(frequency);
}


void vp::component_clock::build_clock(component &comp)
{
    clock_port.set_reg_meth((vp::clk_reg_meth_t *)&component_clock::clk_reg);
    clock_port.set_set_frequency_meth((vp::clk_set_frequency_meth_t *)&component_clock::clk_set_frequency);
    comp.new_slave_port("clock", &clock_port);

}


void vp::component_clock::add_clock_event(clock_event *event)
{
    this->events.push_back(event);
}

void vp::component_clock::remove_clock_event(clock_event *event)
{
    for (unsigned i=0; i<this->events.size(); ++i)
    {
        if (this->events[i] == event)
        {
            this->events.erase(this->events.begin() + i);
            break;
        }
    }
}


vp::master_port::master_port(vp::component *owner)
    : vp::port(owner)
{
}



std::vector<std::string> split_name(const std::string &s, char delimiter)
{
    std::vector<std::string> tokens;
    std::string token;
    std::istringstream tokenStream(s);
    while (std::getline(tokenStream, token, delimiter))
    {
        tokens.push_back(token);
    }
    return tokens;
}

vp::config *vp::config::create_config(jsmntok_t *tokens, int *_size)
{
    jsmntok_t *current = tokens;
    config *config = NULL;

    switch (current->type)
    {
    case JSMN_PRIMITIVE:
        if (strcmp(current->str, "True") == 0 || strcmp(current->str, "False") == 0 || strcmp(current->str, "true") == 0 || strcmp(current->str, "false") == 0)
        {
            config = new config_bool(current);
        }
        else
        {
            config = new config_number(current);
        }
        current++;
        break;

    case JSMN_OBJECT:
    {
        int size;
        config = new config_object(current, &size);
        current += size;
        break;
    }

    case JSMN_ARRAY:
    {
        int size;
        config = new config_array(current, &size);
        current += size;
        break;
    }

    case JSMN_STRING:
        config = new config_string(current);
        current++;
        break;

    case JSMN_UNDEFINED:
        break;
    }

    if (_size)
    {
        *_size = current - tokens;
    }

    return config;
}

vp::config *vp::config_string::get_from_list(std::vector<std::string> name_list)
{
    if (name_list.size() == 0)
        return this;
    return NULL;
}

vp::config *vp::config_number::get_from_list(std::vector<std::string> name_list)
{
    if (name_list.size() == 0)
        return this;
    return NULL;
}

vp::config *vp::config_bool::get_from_list(std::vector<std::string> name_list)
{
    if (name_list.size() == 0)
        return this;
    return NULL;
}

vp::config *vp::config_array::get_from_list(std::vector<std::string> name_list)
{
    if (name_list.size() == 0)
        return this;
    return NULL;
}

vp::config *vp::config_object::get_from_list(std::vector<std::string> name_list)
{
    if (name_list.size() == 0)
        return this;

    vp::config *result = NULL;
    std::string name;
    int name_pos = 0;

    for (auto &x : name_list)
    {
        if (x != "*" && x != "**")
        {
            name = x;
            break;
        }
        name_pos++;
    }

    for (auto &x : childs)
    {

        if (name == x.first)
        {
            result = x.second->get_from_list(std::vector<std::string>(name_list.begin() + name_pos + 1, name_list.begin() + name_list.size()));
            if (name_pos == 0 || result != NULL)
                return result;
        }
        else if (name_list[0] == "*")
        {
            result = x.second->get_from_list(std::vector<std::string>(name_list.begin() + 1, name_list.begin() + name_list.size()));
            if (result != NULL)
                return result;
        }
        else if (name_list[0] == "**")
        {
            result = x.second->get_from_list(name_list);
            if (result != NULL)
                return result;
        }
    }

    return result;
}

vp::config *vp::config_object::get(std::string name)
{
    return get_from_list(split_name(name, '/'));
}

vp::config_string::config_string(jsmntok_t *tokens)
{
    value = tokens->str;
}

vp::config_number::config_number(jsmntok_t *tokens)
{
    value = atof(tokens->str);
}

vp::config_bool::config_bool(jsmntok_t *tokens)
{
    value = strcmp(tokens->str, "True") == 0 || strcmp(tokens->str, "true") == 0;
}

vp::config_array::config_array(jsmntok_t *tokens, int *_size)
{
    jsmntok_t *current = tokens;
    jsmntok_t *top = current++;

    for (int i = 0; i < top->size; i++)
    {
        int child_size;
        elems.push_back(create_config(current, &child_size));
        current += child_size;
    }

    if (_size)
    {
        *_size = current - tokens;
    }
}

vp::config_object::config_object(jsmntok_t *tokens, int *_size)
{
    jsmntok_t *current = tokens;
    jsmntok_t *t = current++;

    for (int i = 0; i < t->size; i++)
    {
        jsmntok_t *child_name = current++;
        int child_size;
        config *child_config = create_config(current, &child_size);
        current += child_size;

        if (child_config != NULL)
        {
            childs[child_name->str] = child_config;
        }
    }

    if (_size)
    {
        *_size = current - tokens;
    }
}

void vp::master_port::final_bind()
{
    if (this->is_bound)
    {
        this->finalize();
    }
}

void vp::slave_port::final_bind()
{
    if (this->is_bound)
        this->finalize();
}


std::vector<vp::slave_port *> vp::slave_port::get_final_ports()
{
    return { this };
}



std::vector<vp::slave_port *> vp::master_port::get_final_ports()
{
    std::vector<vp::slave_port *> result;

    for (auto x : this->slave_ports)
    {
        std::vector<vp::slave_port *> slave_ports = x->get_final_ports();
        result.insert(result.end(), slave_ports.begin(), slave_ports.end());
    }

    return result;
}



void vp::master_port::bind_to_slaves()
{
    for (auto x : this->slave_ports)
    {
        for (auto y : x->get_final_ports())
        {
            this->get_owner()->get_trace()->msg(vp::trace::LEVEL_DEBUG, "Creating final binding (%s:%s -> %s:%s)\n",
                this->get_owner()->get_path().c_str(), this->get_name().c_str(),
                y->get_owner()->get_path().c_str(), y->get_name().c_str()
            );

            this->bind_to(y, NULL);
            y->bind_to(this, NULL);
        }
    }
}


void vp::master_port::bind_to_virtual(vp::port *port)
{
    vp_assert_always(port != NULL, this->get_comp()->get_trace(), "Trying to bind master port to NULL\n");
    this->slave_ports.push_back(port);
}

void vp::fatal(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    if (vfprintf(stderr, fmt, ap) < 0) {}
    va_end(ap);
    exit(1);
}



gv::Gvsoc *gv::gvsoc_new(gv::GvsocConf *conf)
{
    if (conf->proxy_socket != -1)
    {
        return new Gvsoc_proxy_client(conf);
    }
    else
    {
        return new Gvsoc_launcher(conf);
    }
}
