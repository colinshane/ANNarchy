/*
 * 	  ANNarchy.h
 *
 *    This file is part of ANNarchy.
 *   
 *   Copyright (C) 2013-2016  Julien Vitay <julien.vitay@gmail.com>,
 *   Helge Ülo Dinkelbach <helge.dinkelbach@gmail.com>
 *
 *   This program is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation, either version 3 of the License, or
 *   (at your option) any later version.
 *
 *   ANNarchy is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 *   You should have received a copy of the GNU General Public License
 *   along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#ifndef __ANNARCHY_ANNARCHY_H__
#define __ANNARCHY_ANNARCHY_H__
    
#include "Includes.h"

class ANNarchy {
public:
    ANNarchy() {
		net_ = Network::instance();

		//AddPopulation

		//AddProjection
	}

    ~ANNarchy() {
        delete net_;
    }

    /*
    std::vector<DATA_TYPE> getRates(int populationID) {
	return (*net_->getPopulation(populationID)->getRates());
    }
    */

    void run(int nbSteps) {
        net_->run(nbSteps);
    }

    Network* getNetwork() {
        return net_;
    }
private:
    Network *net_;
};

//createProjInstance

#endif