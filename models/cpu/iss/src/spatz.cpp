// #include "spatz.hpp"

// /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// //                                                            VECTOR REGISTER FILE
// /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#include "cpu/iss/include/iss.hpp"


Spatz::Spatz(Iss &iss)
    : vregfile(iss), vlsu(iss)
{
}

void Spatz::build()
{
    this->vlsu.build();
}

void Spatz::reset(bool active)
{
}

VRegfile::VRegfile(Iss &iss) : iss(iss){
    VRegfile::reset(true);
}



void Vlsu::data_response(void *__this, vp::io_req *req)
{
}


Vlsu::Vlsu(Iss &iss) : iss(iss)
{
}

void Vlsu::build()
{
    for (int i=0; i<4; i++)
    {
        this->io_itf[i].set_resp_meth(&Vlsu::data_response);
        this->iss.top.new_master_port(this, "vlsu_" + std::to_string(i), &this->io_itf[i]);
    }


}
inline void VRegfile::reset(bool active){
    if (active){
        for (int i = 0; i < ISS_NB_VREGS; i++){
            for (int j = 0; j < NB_VEL; j++){
                this->vregs[i][j] = i == 0 ? 0 : 0x57575757;
            }
        }
    }
}
