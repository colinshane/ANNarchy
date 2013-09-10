#include "Population.h"

Population::Population(std::string name, int nbNeurons) {
	name_ = std::move(name);

	nbNeurons_ = nbNeurons;
	rate_ = std::vector<DATA_TYPE>(nbNeurons_, 2.0);
	projections_ = std::vector<std::vector<Projection*> >(nbNeurons_, std::vector<Projection*>());
	
	maxDelay_ = 0;
	dt_ = 1.0;
	std::vector< std::vector<DATA_TYPE>	> delayedRates_ = std::vector< std::vector<DATA_TYPE> >();

#ifdef ANNAR_PROFILE
    char buffer[200];
    try{
        sprintf(buffer, "%s(%02i)_sum.txt", name_.c_str(), omp_get_max_threads());
        cs = fopen(buffer, "w");
        sprintf(buffer, "%s(%02i)_global.txt", name_.c_str(), omp_get_max_threads());
        gl = fopen(buffer, "w");
        sprintf(buffer, "%s(%02i)_local.txt", name_.c_str(), omp_get_max_threads());
        ll = fopen(buffer, "w");
    }catch(std::exception e){
        std::cout << "Cannnot open file '"<<buffer<<"'" << std::endl;
        std::cout << e.what() << std::endl;
        cs = NULL;
        gl = NULL;
        ll = NULL;
    }
#endif
}

Population::~Population() {
    std::cout << "Population::Destructor" << std::endl;

    rate_.erase(rate_.begin(), rate_.end());
    for(auto it=delayedRates_.begin(); it<delayedRates_.end(); it++)
        (*it).erase((*it).begin(), (*it).end());

    for(int n=0; n<nbNeurons_; n++) {
        while(!projections_[n].empty()){
            delete projections_[n].back();
            projections_[n].pop_back();
        }
        //projections_[n].erase(projections_[n].begin(), projections_[n].end());
    }

#ifdef ANNAR_PROFILE
    if(cs)
        fclose(cs);
    if(gl)
        fclose(gl);
    if(ll)
        fclose(ll);
#endif
}

void Population::printRates() {
	for(int n=0; n<nbNeurons_; n++) {
		printf("%.02f ", rate_[n]);
		if((n>0)&&(n%10==0))
			printf("\n");
	}
	printf("\n");
}

DATA_TYPE Population::sum(int neur, int typeID) {
	DATA_TYPE sum=0.0;

	for(int i=0; i< projections_[neur].size(); i++)
		if(projections_[neur][i]->getTarget() == typeID)
			sum += projections_[neur][i]->getSum();

	return sum;
}

std::vector<DATA_TYPE> Population::getRates(std::vector<int> delays, std::vector<int> ranks) {
	std::vector<DATA_TYPE> vec = std::vector<DATA_TYPE>(delays.size(), 0.0);

	if(delays.size() != ranks.size()) {
		std::cout << "Invalid vector ranges. " << std::endl;
		return std::vector<DATA_TYPE>();
	}

	for(unsigned int n = 0; n < ranks.size(); n++) {
		vec[n] = delayedRates_[ranks[n]][delays[n]-1];
	}

	return vec;
}

void Population::setMaxDelay(int delay) {
	// TODO:
	// maybe we should take the current fire rate as initial value
	if(delay > maxDelay_) {
		for(int oldSize = delayedRates_.size(); oldSize < delay; oldSize++)
			delayedRates_.push_back(std::vector<DATA_TYPE>(nbNeurons_, (DATA_TYPE)oldSize));
	}
}

void Population::addProjection(int postRankID, Projection* proj) {
#ifdef _DEBUG
	std::cout << name_ << ": added projection to neuron " << postRankID << std::endl;
#endif
	projections_[postRankID].push_back(proj);
}

void Population::removeProjection(Population* pre) {
	for(int n=0; n<nbNeurons_; n++) {
		for(int p=0; p< (int)projections_[n].size();p++) {
			if(projections_[n][p]->getPrePopulation() == pre)
				projections_[n].erase(projections_[n].begin()+p);
		}
	}
}

void Population::metaSum() {
#ifdef ANNAR_PROFILE
    double start = omp_get_wtime();
#endif

	#pragma omp parallel for
	for(int n=0; n<nbNeurons_; n++) {
		for(int p=0; p< (int)projections_[n].size();p++) {
			projections_[n][p]->computeSum();
		}
	}

#ifdef ANNAR_PROFILE
    double stop = omp_get_wtime();

    if(cs)
        fprintf(cs, "%f\n", (stop-start)*1000.0);
#endif
}

void Population::metaStep() {

}

//
// projection update for post neuron based variables
void Population::metaLearn() {
#ifdef ANNAR_PROFILE
    double start = omp_get_wtime();
#endif

    #pragma omp parallel for
    for(int n=0; n<nbNeurons_; n++) {
    #ifdef _DEBUG
        std::cout << "n: "<< n << " "<< projections_[n].size()<< " projections."<< std::endl;
    #endif
        for(int p=0; p< (int)projections_[n].size();p++) {
            projections_[n][p]->globalLearn();
        }
    }

#ifdef ANNAR_PROFILE
    double stop = omp_get_wtime();

    if(gl)
        fprintf(gl, "%f\n", (stop-start)*1000.0);
#endif

#ifdef ANNAR_PROFILE
    double start2 = omp_get_wtime();
#endif

    #pragma omp parallel for
    for(int n=0; n<nbNeurons_; n++) {
    #ifdef _DEBUG
        std::cout << "n: "<< n << " "<< projections_[n].size()<< " projections."<< std::endl;
    #endif
        for(int p=0; p< (int)projections_[n].size();p++) {
            projections_[n][p]->localLearn();
        }
    }

#ifdef ANNAR_PROFILE
    double stop2 = omp_get_wtime();

    if(ll)
        fprintf(ll, "%f\n", (stop2-start2)*1000.0);
#endif
}

void Population::globalOperations() {

}
