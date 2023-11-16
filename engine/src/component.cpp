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



void vp::component::get_trace(std::vector<vp::trace *> &traces, std::string path)
{
    if (this->get_path() != "" && path.find(this->get_path()) != 0)
    {
        return;
    }

    for (vp::component *component: this->get_childs())
    {
        component->get_trace(traces, path);
    }

    for (auto x: this->traces.traces)
    {
        if (x.second->get_full_path().find(path) == 0)
        {
            traces.push_back(x.second);
        }
    }

    for (auto x: this->traces.trace_events)
    {
        if (x.second->get_full_path().find(path) == 0)
        {
            traces.push_back(x.second);
        }
    }
}

void vp::component::final_bind()
{
    for (auto port : this->slave_ports)
    {
        port.second->final_bind();
    }

    for (auto port : this->master_ports)
    {
        port.second->final_bind();
    }

    for (auto &x : this->childs)
    {
        x->final_bind();
    }
}



void vp::component::set_vp_config(js::config *config)
{
    this->vp_config = config;
}





js::config *vp::component::get_vp_config()
{
    if (this->vp_config == NULL)
    {
        if (this->parent != NULL)
        {
            this->vp_config = this->parent->get_vp_config();
        }
    }

    vp_assert_always(this->vp_config != NULL, NULL, "No VP config found\n");

    return this->vp_config;
}





int vp::component::build_all()
{
    this->bind_comps();

    this->pre_start_all();

    this->start_all();

    this->final_bind();

    return 0;
}




void vp::component::start_all()
{
    for (auto &x : this->childs)
    {
        x->start_all();
    }

    this->start();
}



void vp::component::stop_all()
{
    for (auto &x : this->childs)
    {
        x->stop_all();
    }

    this->stop();
}


void vp::component::flush_all()
{
    for (auto &x : this->childs)
    {
        x->flush_all();
    }

    this->flush();
}



void vp::component::pre_start_all()
{
    for (auto &x : this->childs)
    {
        x->pre_start_all();
    }

    this->pre_start();
}


vp::time_engine *vp::component::get_time_engine()
{
    if (this->time_engine_ptr == NULL)
    {
        this->time_engine_ptr = (vp::time_engine*)this->get_service("time");
    }

    return this->time_engine_ptr;
}


void vp::component::new_master_port(std::string name, vp::master_port *port)
{
    this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "New master port (name: %s, port: %p)\n", name.c_str(), port);

    port->set_owner(this);
    port->set_context(this);
    port->set_name(name);
    this->add_master_port(name, port);
}



void vp::component::new_master_port(void *comp, std::string name, vp::master_port *port)
{
    this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "New master port (name: %s, port: %p)\n", name.c_str(), port);

    port->set_owner(this);
    port->set_context(comp);
    port->set_name(name);
    this->add_master_port(name, port);
}



void vp::component::add_slave_port(std::string name, vp::slave_port *port)
{
    vp_assert_always(port != NULL, this->get_trace(), "Adding NULL port\n");
    //vp_assert_always(this->slave_ports[name] == NULL, this->get_trace(), "Adding already existing port\n");
    this->slave_ports[name] = port;
}



void vp::component::add_master_port(std::string name, vp::master_port *port)
{
    vp_assert_always(port != NULL, this->get_trace(), "Adding NULL port\n");
    //vp_assert_always(this->master_ports[name] == NULL, this->get_trace(), "Adding already existing port\n");
    this->master_ports[name] = port;
}



void vp::component::new_slave_port(std::string name, vp::slave_port *port)
{
    this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "New slave port (name: %s, port: %p)\n", name.c_str(), port);

    port->set_owner(this);
    port->set_context(this);
    port->set_name(name);
    this->add_slave_port(name, port);
}



void vp::component::new_slave_port(void *comp, std::string name, vp::slave_port *port)
{
    this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "New slave port (name: %s, port: %p)\n", name.c_str(), port);

    port->set_owner(this);
    port->set_context(comp);
    port->set_name(name);
    this->add_slave_port(name, port);
}



void vp::component::add_service(std::string name, void *service)
{
    if (this->parent)
        this->parent->add_service(name, service);
    else if (all_services[name] == NULL)
        all_services[name] = service;
}


void vp::component::conf(string name, string path, vp::component *parent)
{
    if (!this->is_configured)
    {
        this->is_configured = true;
        this->name = name;
        this->parent = parent;
        this->path = path;
        if (parent != NULL)
        {
            parent->add_child(name, this);
        }
    }
}

void vp::component::add_child(std::string name, vp::component *child)
{
    this->childs.push_back(child);
    this->childs_dict[name] = child;
}




vp::component *vp::component::get_component(std::vector<std::string> path_list)
{
    if (path_list.size() == 0)
    {
        return this;
    }

    std::string name = "";
    unsigned int name_pos= 0;
    for (auto x: path_list)
    {
        if (x != "*" && x != "**")
        {
            name = x;
            break;
        }
        name_pos += 1;
    }

    for (auto x:this->childs)
    {
        vp::component *comp;
        if (name == x->get_name())
        {
            comp = x->get_component({ path_list.begin() + name_pos + 1, path_list.end() });
        }
        else if (path_list[0] == "**")
        {
            comp = x->get_component(path_list);
        }
        else if (path_list[0] == "*")
        {
            comp = x->get_component({ path_list.begin() + 1, path_list.end() });
        }
        if (comp)
        {
            return comp;
        }
    }

    return NULL;
}

void vp::component::new_reg(std::string name, vp::reg_1 *reg, uint8_t reset_val, bool reset)
{
    this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "New register (name: %s, width: %d, reset_val: 0x%x, reset: %d)\n",
        name.c_str(), 1, reset_val, reset
    );

    reg->init(this, name, reset ? (uint8_t *)&reset_val : NULL);
    this->regs.push_back(reg);
}

void vp::component::new_reg(std::string name, vp::reg_8 *reg, uint8_t reset_val, bool reset)
{
    this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "New register (name: %s, width: %d, reset_val: 0x%x, reset: %d)\n",
        name.c_str(), 8, reset_val, reset
    );

    reg->init(this, name, reset ? (uint8_t *)&reset_val : NULL);
    this->regs.push_back(reg);
}

void vp::component::new_reg(std::string name, vp::reg_16 *reg, uint16_t reset_val, bool reset)
{
    this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "New register (name: %s, width: %d, reset_val: 0x%x, reset: %d)\n",
        name.c_str(), 16, reset_val, reset
    );

    reg->init(this, name, reset ? (uint8_t *)&reset_val : NULL);
    this->regs.push_back(reg);
}

void vp::component::new_reg(std::string name, vp::reg_32 *reg, uint32_t reset_val, bool reset)
{
    this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "New register (name: %s, width: %d, reset_val: 0x%x, reset: %d)\n",
        name.c_str(), 32, reset_val, reset
    );

    reg->init(this, name, reset ? (uint8_t *)&reset_val : NULL);
    this->regs.push_back(reg);
}

void vp::component::new_reg(std::string name, vp::reg_64 *reg, uint64_t reset_val, bool reset)
{
    this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "New register (name: %s, width: %d, reset_val: 0x%x, reset: %d)\n",
        name.c_str(), 64, reset_val, reset
    );

    reg->init(this, name, reset ? (uint8_t *)&reset_val : NULL);
    this->regs.push_back(reg);
}


void vp::component::bind_comps()
{
    this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "Creating final bindings\n");

    for (auto x : this->get_childs())
    {
        x->bind_comps();
    }

    for (auto x : this->master_ports)
    {
        if (!x.second->is_virtual())
        {
            x.second->bind_to_slaves();
        }
    }
}

void vp::component::create_comps()
{
    js::config *config = this->get_js_config();
    js::config *comps = config->get("vp_comps");
    if (comps == NULL)
    {
        comps = config->get("components");
    }

    if (comps != NULL)
    {
        this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "Creating components\n");

        for (auto x : comps->get_elems())
        {
            std::string comp_name = x->get_str();

            js::config *comp_config = config->get(comp_name);

            std::string vp_component = comp_config->get_child_str("vp_component");

            if (vp_component == "")
                vp_component = "utils.composite_impl";

            this->new_component(comp_name, comp_config, vp_component);
        }
    }
}



void vp::component::dump_traces_recursive(FILE *file)
{
    this->dump_traces(file);

    for (auto& x: this->get_childs())
    {
        x->dump_traces_recursive(file);
    }
}

std::string vp::component::get_component_path(js::config *gv_config, std::string relpath)
{
    js::config *inc_dirs = gv_config->get("include_dirs");
    std::string inc_dirs_str = "";
    for (auto x: inc_dirs->get_elems())
    {
        std::string inc_dir = x->get_str();
        std::string path = inc_dir + "/" + relpath + ".so";
        inc_dirs_str += inc_dirs_str == "" ? inc_dir : ":" + inc_dir;
        struct stat buffer;
        if (stat(path.c_str(), &buffer) == 0)
        {
            return path;
        }
    }

     throw std::invalid_argument("Couldn't find component (name: " + relpath + ", inc_dirs: " + inc_dirs_str );
}


vp::component *vp::component::load_component(js::config *config, js::config *gv_config, vp::component *parent, std::string name, std::string path)
{
    std::string module_name = config->get_child_str("vp_component");

    if (module_name == "")
    {
        module_name = "utils.composite_impl";
    }

#ifdef __M32_MODE__
    if (gv_config->get_child_bool("debug-mode"))
    {
        module_name = "debug_m32." + module_name;
    }
    else
    {
        module_name = "m32." + module_name;
    }
#else
    if (gv_config->get_child_bool("debug-mode"))
    {
        module_name = "debug." + module_name;
    }
#endif


    std::replace(module_name.begin(), module_name.end(), '.', '/');

    std::string module_path = vp::component::get_component_path(gv_config, module_name);

    void *module = dlopen(module_path.c_str(), RTLD_NOW | RTLD_GLOBAL | RTLD_DEEPBIND);
    if (module == NULL)
    {
        throw std::invalid_argument("ERROR, Failed to open periph model (module: " + module_name + ", error: " + std::string(dlerror()) + ")");
    }

    vp::component *(*constructor)(js::config *) = (vp::component * (*)(js::config *)) dlsym(module, "vp_constructor");
    if (constructor)
    {
        return constructor(config);
    }

    vp::component *(*gv_new)(ComponentConf &conf) = (vp::component * (*)(ComponentConf &conf)) dlsym(module, "gv_new");
    if (gv_new)
    {
        ComponentConf conf = {.name=name, .path=path, .parent=parent, .config=config};
        return gv_new(conf);
    }

    throw std::invalid_argument("ERROR, couldn't find neither vp_constructor nor gv_new in loaded module (module: " + module_name + ")");
}

Gvsoc_launcher *vp::component::get_launcher()
{
    if (this->parent)
    {
        return this->parent->get_launcher();
    }

    return this->launcher;
}


void *vp::component::external_bind(std::string comp_name, std::string itf_name, void *handle)
{
    for (auto &x : this->childs)
    {
        void *result = x->external_bind(comp_name, itf_name, handle);
        if (result != NULL)
            return result;
    }

    return NULL;
}

void vp::component::new_service(std::string name, void *service)
{
    this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "New service (name: %s, service: %p)\n", name.c_str(), service);

    if (this->parent)
        this->parent->add_service(name, service);

    all_services[name] = service;
}

void *vp::component::get_service(string name)
{
    if (all_services[name])
        return all_services[name];

    if (this->parent)
        return this->parent->get_service(name);

    return NULL;
}

void vp::component::reset_all(bool active, bool from_itf)
{
    // Small hack to not propagate the reset from top level if the reset has
    // already been done through the interface from another component.
    // This should be all implemented with interfaces to better control
    // the reset propagation.
    this->reset_done_from_itf |= from_itf;

    if (from_itf || !this->reset_done_from_itf)
    {
        this->get_trace()->msg("Reset\n");

        for (auto reg : this->regs)
        {
            reg->reset(active);
        }

        this->block::reset_all(active);

        if (active)
        {
            for (clock_event *event: this->events)
            {
                this->event_cancel(event);
            }
        }

        for (auto &x : this->childs)
        {
            x->reset_all(active);
        }
    }

}

void vp::component::throw_error(std::string error)
{
    throw std::invalid_argument("[\033[31m" + this->get_path() + "\033[0m] " + error);
}


void vp::component::build_instance(std::string name, std::string path, vp::component *parent)
{
    this->conf(name, path, parent);

    this->build_clock(*this);

    reset_port.set_sync_meth(&component::reset_sync);
    this->new_slave_port("reset", &reset_port);

    this->traces.new_trace("comp", this->get_trace(), vp::DEBUG);
    this->traces.new_trace("warning", &this->warning, vp::WARNING);

    this->build();
    this->power.build();
}

void vp::component::reset_sync(void *__this, bool active)
{
    component *_this = (component *)__this;
    _this->reset_done_from_itf = true;
    _this->reset_all(active, true);
}


vp::component *vp::component::new_component(std::string name, js::config *config, std::string module_name)
{
    std::string comp_path = this->get_path() != "" ? this->get_path() + "/" + name : name == "" ? "" : "/" + name;

    vp::component *instance = vp::component::load_component(config, this->get_vp_config(), this, name, comp_path);

    this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "New component (name: %s)\n", name.c_str());

    instance->build_instance(name, comp_path, this);

    return instance;
}

vp::component::component(js::config *config)
    : block(NULL), traces(*this), power(*this), reset_done_from_itf(false)
{
    this->comp_js_config = config;

    //this->conf(path, parent);
}

vp::component::component(vp::ComponentConf &conf)
    : block(NULL), traces(*this), power(*this), reset_done_from_itf(false)
{
    this->comp_js_config = conf.config;
    this->conf(conf.name, conf.path, conf.parent);
}


void vp::component::create_ports()
{
    js::config *config = this->get_js_config();
    js::config *ports = config->get("vp_ports");
    if (ports == NULL)
    {
        ports = config->get("ports");
    }

    if (ports != NULL)
    {
        this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "Creating ports\n");

        for (auto x : ports->get_elems())
        {
            std::string port_name = x->get_str();

            this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "Creating port (name: %s)\n", port_name.c_str());

            if (this->get_master_port(port_name) == NULL && this->get_slave_port(port_name) == NULL)
                this->add_master_port(port_name, new vp::virtual_port(this));
        }
    }
}

void vp::component::create_bindings()
{
    js::config *config = this->get_js_config();
    js::config *bindings = config->get("vp_bindings");
    if (bindings == NULL)
    {
        bindings = config->get("bindings");
    }

    if (bindings != NULL)
    {
        this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "Creating bindings\n");

        for (auto x : bindings->get_elems())
        {
            std::string master_binding = x->get_elem(0)->get_str();
            std::string slave_binding = x->get_elem(1)->get_str();
            int pos = master_binding.find_first_of("->");
            std::string master_comp_name = master_binding.substr(0, pos);
            std::string master_port_name = master_binding.substr(pos + 2);
            pos = slave_binding.find_first_of("->");
            std::string slave_comp_name = slave_binding.substr(0, pos);
            std::string slave_port_name = slave_binding.substr(pos + 2);

            this->get_trace()->msg(vp::trace::LEVEL_DEBUG, "Creating binding (%s:%s -> %s:%s)\n",
                master_comp_name.c_str(), master_port_name.c_str(),
                slave_comp_name.c_str(), slave_port_name.c_str()
            );

            vp::component *master_comp = master_comp_name == "self" ? this : this->get_childs_dict()[master_comp_name];
            vp::component *slave_comp = slave_comp_name == "self" ? this : this->get_childs_dict()[slave_comp_name];

            vp_assert_always(master_comp != NULL, this->get_trace(),
                "Binding from invalid master (master: %s / %s, slave: %s / %s)\n",
                master_comp_name.c_str(), master_port_name.c_str(),
                slave_comp_name.c_str(), slave_port_name.c_str());

            vp_assert_always(slave_comp != NULL, this->get_trace(),
                "Binding from invalid slave (master: %s / %s, slave: %s / %s)\n",
                master_comp_name.c_str(), master_port_name.c_str(),
                slave_comp_name.c_str(), slave_port_name.c_str());

            vp::port *master_port = master_comp->get_master_port(master_port_name);
            vp::port *slave_port = slave_comp->get_slave_port(slave_port_name);

            vp_assert_always(master_port != NULL, this->get_trace(),
                "Binding from invalid master port (master: %s / %s, slave: %s / %s)\n",
                master_comp_name.c_str(), master_port_name.c_str(),
                slave_comp_name.c_str(), slave_port_name.c_str());

            vp_assert_always(slave_port != NULL, this->get_trace(),
                "Binding from invalid slave port (master: %s / %s, slave: %s / %s)\n",
                master_comp_name.c_str(), master_port_name.c_str(),
                slave_comp_name.c_str(), slave_port_name.c_str());

            master_port->bind_to_virtual(slave_port);
        }
    }
}
