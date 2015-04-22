cuda_profile_body=\
"""
#include "Profiling.h"

Profiling::Profiling() {
}

void Profiling::get_device_prop(int device)
{
	cudaDeviceProp cudaprop;
	cudaGetDeviceProperties(&cudaprop,device);
	device_prop.maxThreadsPerBlock=cudaprop.maxThreadsPerBlock;
	device_prop.ECCEnabled=cudaprop.ECCEnabled;
	device_prop.regsPerMultiprocessor=cudaprop.regsPerMultiprocessor;
	device_prop.maxThreadsPerMultiprocessor=cudaprop.maxThreadsPerMultiProcessor;
	device_prop.major=cudaprop.major;
	device_prop.minor=cudaprop.minor;
}

/*
	Init
*/
void Profiling::init(int extended)
{
 //Profiling Array allocate
        Prof_time=     new Profiling_time[Profiling_time_count+1];
        Prof_time_CPU= new Profiling_time[Profiling_time_CPU_count+1];
        Prof_time_init=new Profiling_time[Profiling_time_init_count];
        Prof_memcopy=  new Profiling_memcopy[Profiling_memcopy_count];

 //additional initialisations
	if (extended){
		init_GPU_prof();
	}
}

void Profiling::init_GPU_prof(void)
{
 //Initial Profiling Dummy
	cudaEvent_t event1, event2;
	long_long start,stop;

	//create events
	cudaEventCreate(&event1);
	cudaEventCreate(&event2);

	//record events around kernel launch
	cudaEventRecord(event1, 0); //where 0 is the default stream

	start = PAPI_get_real_usec();	
	
	stop = PAPI_get_real_usec();
	cudaEventRecord(event2, 0);

	//synchronize
	cudaEventSynchronize(event1); //optional
	cudaEventSynchronize(event2); //wait for the event to be executed!
	float dt_ms;
	//calculate time
	cudaEventElapsedTime(&dt_ms, event1, event2);
}

/*
	Measurement Error measure
*/
void Profiling::error_CPU_time_prof()
{
  if(Profil){
	start_CPU_time_prof(Profiling_time_CPU_count);
	stop_CPU_time_prof(Profiling_time_CPU_count);
  }
}

void Profiling::error_GPU_time_prof()
{
  if(Profil){
	start_GPU_time_prof(Profiling_time_count);
	stop_GPU_time_prof(Profiling_time_count);
  }
}

/*
	GPU Time
*/
void Profiling::start_GPU_time_prof( int number)
{
  if(Profil){
	//create events
	cudaEventCreate(&Prof_time[number].startevent);
	cudaEventCreate(&Prof_time[number].stopevent);

	//record events around kernel launch
	cudaEventRecord(Prof_time[number].startevent, 0); //where 0 is the default stream

	Prof_time[number].start = PAPI_get_real_usec();
  }
}
	
void Profiling::stop_GPU_time_prof( int number,int directevaluate)
{
  if(Profil){
	Prof_time[number].stop = PAPI_get_real_usec();
	cudaEventRecord(Prof_time[number].stopevent, 0);

	if (directevaluate){
			evaluate_GPU_time_prof(number);
	}
  }
}

void Profiling::evaluate_GPU_time_prof( int number)
{
  if(Profil){
	//synchronize
	cudaEventSynchronize(Prof_time[number].startevent);
	cudaEventSynchronize(Prof_time[number].stopevent); //wait for the event to be executed!
	
	float dt_ms;
	//calculate time
	cudaEventElapsedTime(&dt_ms, Prof_time[number].startevent, Prof_time[number].stopevent);

	//pre-evaluate GPU time
	dt_ms-=((float)(Prof_time[number].stop-Prof_time[number].start))/1000.0;//Launch time
	dt_ms/=1000.0;//ms => s

	Prof_time[number].time.summ+=dt_ms;
	Prof_general.GPU_summ+=dt_ms;
	Prof_time[number].time.count++;
	Prof_time[number].time.summsqr+=square(dt_ms);
	(dt_ms<Prof_time[number].time.min)?(Prof_time[number].time.min=dt_ms):1;
	(Prof_time[number].time.max<dt_ms)?(Prof_time[number].time.max=dt_ms):1;//min/max
  }
}

/*
	memcopy
*/
void Profiling::start_memcopy_prof( int number,int bytesize)
{
  if(Profil){
	Prof_memcopy[number].memory=bytesize;

	//create events
	cudaEventCreate(&Prof_memcopy[number].startevent);
	cudaEventCreate(&Prof_memcopy[number].stopevent);

	//record events around kernel launch
	cudaEventRecord(Prof_memcopy[number].startevent, 0); //where 0 is the default stream

	Prof_memcopy[number].start = PAPI_get_real_usec();	
  }
}
	
void Profiling::stop_memcopy_prof( int number,int directevaluate)
{
  if(Profil){
	Prof_memcopy[number].stop = PAPI_get_real_usec();
	cudaEventRecord(Prof_memcopy[number].stopevent, 0);

	if (directevaluate){
			evaluate_memcopy_prof(number);
	}
  }
}

void Profiling::evaluate_memcopy_prof( int number)
{
  if(Profil){
	//synchronize
	cudaEventSynchronize(Prof_memcopy[number].startevent);
	cudaEventSynchronize(Prof_memcopy[number].stopevent); //wait for the event to be executed!
	
	float dt_ms;
	//calculate time
	cudaEventElapsedTime(&dt_ms, Prof_memcopy[number].startevent, Prof_memcopy[number].stopevent);

	//pre-evaluate GPU time
	dt_ms-=((float)(Prof_memcopy[number].stop-Prof_memcopy[number].start))/1000.0;//Launch time
	dt_ms/=1000.0;//ms => s
//calculate time
	Prof_memcopy[number].time.summ+=dt_ms;
	Prof_general.GPU_summ+=dt_ms;//memcopy is part of GPU
	Prof_memcopy[number].time.count++;
	Prof_memcopy[number].time.summsqr+=square(dt_ms);
	(dt_ms<Prof_memcopy[number].time.min)?(Prof_memcopy[number].time.min=dt_ms):1;
	(Prof_memcopy[number].time.max<dt_ms)?(Prof_memcopy[number].time.max=dt_ms):1;//min/max
//calculate memory
	double bytesize=Prof_memcopy[number].memory;
	Prof_memcopy[number].memorysize.summ+=bytesize;
	Prof_memcopy[number].memorysize.count++;
	Prof_memcopy[number].memorysize.summsqr+=square(bytesize);
	(bytesize<Prof_memcopy[number].memorysize.min)?(Prof_memcopy[number].memorysize.min=bytesize):1;
	(Prof_memcopy[number].memorysize.max<bytesize)?(Prof_memcopy[number].memorysize.max=bytesize):1;//min/max
//calculate Throughput
	double memorythroughput=(bytesize)/dt_ms;
	Prof_memcopy[number].memorythroughput.summ+=memorythroughput;
	Prof_memcopy[number].memorythroughput.count++;
	Prof_memcopy[number].memorythroughput.summsqr+=square(memorythroughput);
	(memorythroughput<Prof_memcopy[number].memorythroughput.min)?(Prof_memcopy[number].memorythroughput.min=memorythroughput):1;
	(Prof_memcopy[number].memorythroughput.max<memorythroughput)?(Prof_memcopy[number].memorythroughput.max=memorythroughput):1;//min/max

  }
}

/*
	CPU Time
*/
void Profiling::start_CPU_time_prof( int number)
{
  if(Profil){
	Prof_time_CPU[number].start = PAPI_get_real_usec();	
  }
}
	
void Profiling::stop_CPU_time_prof( int number,int directevaluate)
{
  if(Profil){
	Prof_time_CPU[number].stop = PAPI_get_real_usec();

	if (directevaluate){
			evaluate_CPU_time_prof(number);
	 }
  }
}

void Profiling::evaluate_CPU_time_prof( int number)
{
  if(Profil){
	double dt_ms;

	//pre-evaluate CPU time
	dt_ms=((double)(Prof_time_CPU[number].stop-Prof_time_CPU[number].start))/1000.0;//Launch time
	dt_ms/=1000.0;//ms => s

	Prof_time_CPU[number].time.summ+=dt_ms;
	Prof_time_CPU[number].time.count++;
	Prof_time_CPU[number].time.summsqr+=square(dt_ms);
	(dt_ms<Prof_time_CPU[number].time.min)?(Prof_time_CPU[number].time.min=dt_ms):1;
	(Prof_time_CPU[number].time.max<dt_ms)?(Prof_time_CPU[number].time.max=dt_ms):1;//min/max
  }
}

/*
	Init Time
*/
void Profiling::start_Init_time_prof( int number)
{
  if(Profil){
	Prof_time_init[number].start = PAPI_get_real_usec();	
  }
}
	
void Profiling::stop_Init_time_prof( int number,int directevaluate)
{
  if(Profil){
	Prof_time_init[number].stop = PAPI_get_real_usec();

	if (directevaluate){
		evaluate_Init_time_prof(number);
	}
  }
}

void Profiling::evaluate_Init_time_prof( int number)
{
  if(Profil){
	double dt_ms;

	//pre-evaluate CPU time
	dt_ms=((double)(Prof_time_init[number].stop-Prof_time_init[number].start))/1000.0;//Launch time
	dt_ms/=1000.0;//ms => s

	Prof_time_init[number].time.summ+=dt_ms;
	Prof_time_init[number].time.count++;
	Prof_time_init[number].time.summsqr+=square(dt_ms);
	(dt_ms<Prof_time_init[number].time.min)?(Prof_time_init[number].time.min=dt_ms):1;
	(Prof_time_init[number].time.max<dt_ms)?(Prof_time_init[number].time.max=dt_ms):1;//min/max
  }
}

/*
	Overall Time
*/
void Profiling::start_overall_time_prof()
{
  if(Profil){
	cudaDeviceSynchronize();
	Prof_general.start = PAPI_get_real_usec();	
  }
}
	
void Profiling::stop_overall_time_prof()
{
  if(Profil){
	cudaDeviceSynchronize();

	Prof_general.stop = PAPI_get_real_usec();

	evaluate_overall_time_prof();
  }
}

void Profiling::evaluate_overall_time_prof()
{
  if(Profil){
	Prof_general.CPU_summ=((double)(Prof_general.stop-Prof_general.start))/1000.0/1000.0;//s
  }
}
/*
	RESET
*/
void Profiling::reset_overall_time_prof()
{
	Prof_general.CPU_summ=0;//s
	Prof_general.GPU_summ=0;//s
}
void Profiling::reset_CPU_time_prof(int number)
{
	Prof_time_CPU[number].time.count=0;
	Prof_time_CPU[number].time.summ=0;
	Prof_time_CPU[number].time.summsqr=0;
	Prof_time_CPU[number].time.min=FLT_MAX;
	Prof_time_CPU[number].time.max=FLT_MIN;
}
void Profiling::reset_GPU_time_prof(int number)
{
	Prof_time[number].time.count=0;
	Prof_time[number].time.summ=0;
	Prof_time[number].time.summsqr=0;
	Prof_time[number].time.min=FLT_MAX;
	Prof_time[number].time.max=FLT_MIN;
}
void Profiling::reset_Init_time_prof(int number)
{
	Prof_time_init[number].time.count=0;
	Prof_time_init[number].time.summ=0;
	Prof_time_init[number].time.summsqr=0;
	Prof_time_init[number].time.min=FLT_MAX;
	Prof_time_init[number].time.max=FLT_MIN;
}
void Profiling::reset_memcopy_prof(int number)
{
	Prof_memcopy[number].time.count=0;
	Prof_memcopy[number].time.summ=0;
	Prof_memcopy[number].time.summsqr=0;
	Prof_memcopy[number].time.min=FLT_MAX;
	Prof_memcopy[number].time.max=FLT_MIN;

	Prof_memcopy[number].memorysize.count=0;
	Prof_memcopy[number].memorysize.summ=0;
	Prof_memcopy[number].memorysize.summsqr=0;
	Prof_memcopy[number].memorysize.min=FLT_MAX;
	Prof_memcopy[number].memorysize.max=FLT_MIN;

	Prof_memcopy[number].memorythroughput.count=0;
	Prof_memcopy[number].memorythroughput.summ=0;
	Prof_memcopy[number].memorythroughput.summsqr=0;
	Prof_memcopy[number].memorythroughput.min=FLT_MAX;
	Prof_memcopy[number].memorythroughput.max=FLT_MIN;
}
/*
	Evaluation
*/
void Profiling::evaluate(int disp, int file,const char * filename)
{
	evaluate_calc();
	if (disp)evaluate_disp();
	if (file)evaluate_file(filename);
}

void Profiling::evaluate_calc()
{
	for(int i=0;i<Profiling_time_count+1;i++){
		Prof_time[i].time.avg=Prof_time[i].time.summ/Prof_time[i].time.count;
		Prof_time[i].time.standard=sqrt(Prof_time[i].time.summsqr/Prof_time[i].time.count-square(Prof_time[i].time.avg));
		Prof_time[i].time.prozent_CPU=100.0*Prof_time[i].time.summ/Prof_general.CPU_summ;
		Prof_time[i].time.prozent_GPU=100.0*Prof_time[i].time.summ/Prof_general.GPU_summ;
	}
	for(int i=0;i<Profiling_time_CPU_count+1;i++){
		Prof_time_CPU[i].time.avg=Prof_time_CPU[i].time.summ/Prof_time_CPU[i].time.count;
		Prof_time_CPU[i].time.standard=sqrt(Prof_time_CPU[i].time.summsqr/Prof_time_CPU[i].time.count-square(Prof_time_CPU[i].time.avg));
		Prof_time_CPU[i].time.prozent_CPU=100.0*Prof_time_CPU[i].time.summ/Prof_general.CPU_summ;
		Prof_time_CPU[i].time.prozent_GPU=0;
	}
	for(int i=0;i<Profiling_time_init_count;i++){
		Prof_time_init[i].time.prozent_CPU=100.0*Prof_time_init[i].time.summ/Prof_general.CPU_summ;
	}
	for(int i=0;i<Profiling_memcopy_count;i++){
		Prof_memcopy[i].time.avg=Prof_memcopy[i].time.summ/Prof_memcopy[i].time.count;
		Prof_memcopy[i].time.standard=sqrt(Prof_memcopy[i].time.summsqr/Prof_memcopy[i].time.count-square(Prof_memcopy[i].time.avg));
		Prof_memcopy[i].time.prozent_CPU=100.0*Prof_memcopy[i].time.summ/Prof_general.CPU_summ;
		Prof_memcopy[i].time.prozent_GPU=100.0*Prof_memcopy[i].time.summ/Prof_general.GPU_summ;

		Prof_memcopy[i].memorysize.avg=Prof_memcopy[i].memorysize.summ/Prof_memcopy[i].memorysize.count;
		Prof_memcopy[i].memorysize.standard=sqrt(Prof_memcopy[i].memorysize.summsqr/Prof_memcopy[i].memorysize.count-square(Prof_memcopy[i].memorysize.avg));

		Prof_memcopy[i].memorythroughput.avg=Prof_memcopy[i].memorythroughput.summ/Prof_memcopy[i].memorythroughput.count;
		Prof_memcopy[i].memorythroughput.standard=sqrt(Prof_memcopy[i].memorythroughput.summsqr/Prof_memcopy[i].memorythroughput.count-square(Prof_memcopy[i].memorythroughput.avg));
	}
}
void Profiling::evaluate_disp()
{
	std::cout.precision(8);
	std::cout << "Overall time: "<< std::fixed << Prof_general.CPU_summ 	<< "s " <<"On GPU only: "<< std::fixed << Prof_general.GPU_summ 	<< "s "<< std::endl;
	for(int i=0;i<Profiling_time_init_count;i++){
		int found = (Prof_time_init[i].name.find(":")!=std::string::npos)||(Prof_time_CPU[i].name.find("#")!=std::string::npos);//1 wenn Prof_time_init[i].name ungueltig 
		if ((Prof_time_CPU[i].name=="")||(found))
			std::cout << "Initialisation_Time "<<i;
		else 	
			std::cout << Prof_time_init[i].name;
		std::cout 	<<" time: " 		 << std::fixed << Prof_time_init[i].time.summ 	<< "s "
				<< "Faktor CPU time: " << std::fixed << Prof_time_init[i].time.prozent_CPU/100<< std::endl;
	}
		std::cout 	<< std::endl;
	for(int i=0;i<Profiling_memcopy_count;i++){
		int found = (Prof_memcopy[i].name.find(":")!=std::string::npos)||(Prof_memcopy[i].name.find("#")!=std::string::npos);//1 wenn Prof_memcopy[i].name ungueltig 
		if ((Prof_memcopy[i].name=="")||(found))
			std::cout << "Memcopy_Time "<<i;
		else 	
			std::cout << Prof_memcopy[i].name;
		std::cout 	<<" time: " 		 << std::fixed << Prof_memcopy[i].time.summ 	<< "s "
				<< "Relative to CPU time: " << std::fixed << Prof_memcopy[i].time.prozent_CPU<< "% "
				<< "Relative to GPU time: " << std::fixed << Prof_memcopy[i].time.prozent_GPU<< "% "
				<< "Average time: " 	 << std::fixed << Prof_memcopy[i].time.avg 	<< "s "
				<< "Minimum time: " 	 << std::fixed << Prof_memcopy[i].time.min 	<< "s "
				<< "Maximum time: " 	 << std::fixed << Prof_memcopy[i].time.max 	<< "s "
				<< "Standard deviation: "<< std::fixed << Prof_memcopy[i].time.standard 	<< "s "<< std::endl;

		std::cout 	<<" \tMemory: " 	 << std::fixed << Prof_memcopy[i].memorysize.summ 	<< "Byte "
				<< "Average Memory: " 	 << std::fixed << Prof_memcopy[i].memorysize.avg 	<< "Byte "
				<< "Minimum Memory: " 	 << std::fixed << Prof_memcopy[i].memorysize.min 	<< "Byte "
				<< "Maximum Memory: " 	 << std::fixed << Prof_memcopy[i].memorysize.max 	<< "Byte "
				<< "Standard deviation: "<< std::fixed << Prof_memcopy[i].memorysize.standard 	<< "Byte "<< std::endl;

		std::cout 	<<" \tThroughput: " 	 << std::fixed << Prof_memcopy[i].memorythroughput.summ 	<< "Byte/s "
				<< "Average Memory: " 	 << std::fixed << Prof_memcopy[i].memorythroughput.avg 	<< "Byte/s "
				<< "Minimum Memory: " 	 << std::fixed << Prof_memcopy[i].memorythroughput.min 	<< "Byte/s "
				<< "Maximum Memory: " 	 << std::fixed << Prof_memcopy[i].memorythroughput.max 	<< "Byte/s "
				<< "Standard deviation: "<< std::fixed << Prof_memcopy[i].memorythroughput.standard 	<< "Byte/s "<< std::endl;
	}
		std::cout 	<< std::endl;
	for(int i=0;i<Profiling_time_CPU_count;i++){
		int found = (Prof_time_CPU[i].name.find(":")!=std::string::npos)||(Prof_time_CPU[i].name.find("#")!=std::string::npos);//1 wenn Prof_time_CPU[i].name ungueltig 
		if ((Prof_time_CPU[i].name=="")||(found))
			std::cout << "CPU_Time "<<i;
		else 	
			std::cout << Prof_time_CPU[i].name;
		std::cout 	<<" time: " 		 << std::fixed << Prof_time_CPU[i].time.summ 	<< "s "
				<< "Relative to CPU time: " << std::fixed << Prof_time_CPU[i].time.prozent_CPU<< "% "
				<< "Average time: " 	 << std::fixed << Prof_time_CPU[i].time.avg 	<< "s "
				<< "Minimum time: " 	 << std::fixed << Prof_time_CPU[i].time.min 	<< "s "
				<< "Maximum time: " 	 << std::fixed << Prof_time_CPU[i].time.max 	<< "s "
				<< "Standard deviation: "<< std::fixed << Prof_time_CPU[i].time.standard 	<< "s "<< std::endl;
	}
		std::cout 	<< std::endl;
	for(int i=0;i<Profiling_time_count;i++){
		int found = (Prof_time[i].name.find(":")!=std::string::npos)||(Prof_time[i].name.find("#")!=std::string::npos);//1 wenn Prof_time[i].name ungueltig 
		if ((Prof_time[i].name=="")||(found))
			std::cout << "GPU_Time "<<i;
		else 	
			std::cout << Prof_time[i].name;
		std::cout 	<<" time: " 		 << std::fixed << Prof_time[i].time.summ 	<< "s "
				<< "Relative to CPU time: " << std::fixed << Prof_time[i].time.prozent_CPU<< "% "
				<< "Relative to GPU time: " << std::fixed << Prof_time[i].time.prozent_GPU<< "% "
				<< "Average time: " 	 << std::fixed << Prof_time[i].time.avg 	<< "s "
				<< "Minimum time: " 	 << std::fixed << Prof_time[i].time.min 	<< "s "
				<< "Maximum time: " 	 << std::fixed << Prof_time[i].time.max 	<< "s "
				<< "Standard deviation: "<< std::fixed << Prof_time[i].time.standard 	<< "s "<< std::endl;
	}
}

int Profiling::evaluate_file(const char * filename)
{
	std::ofstream fp;
	fp.open(filename,std::ios::out|std::ios::trunc);
	if (!(fp.is_open()))return 0;
	fp.precision(8);
	fp <<"#"												//Trennzeile 1:CPU Gesammtzeit
	 << "Overall time: in s"<< std::endl;
	fp << std::fixed << Prof_general.CPU_summ << std::endl;
	fp <<"#"												//Trennzeile 2:GPU Gesammtzeit
	 << "On GPU only: in s"<< std::endl;
	fp << std::fixed << Prof_general.GPU_summ << std::endl;
	fp <<"#"												//Trennzeile 3:CPU Zeiten
	 << "Name:Summe(s):Relative(%):Calls(1):Average(s):Minimum(s):Maximum(s):Standard deviation(s):additonal"<< std::endl;
		for(int i=0;i<Profiling_time_CPU_count;i++){
			int found = checkstring(Prof_time_CPU[i].name);//1 wenn Prof_time_CPU[i].name ungueltig 
			if ((Prof_time_CPU[i].name=="")||(found))
				fp << "CPU_Time "<<i;
			else 	
				fp << Prof_time_CPU[i].name;

			fp <<		   ":" << std::fixed << Prof_time_CPU[i].time.summ 
					<< ":" << std::fixed << Prof_time_CPU[i].time.prozent_CPU
					<< ":" << std::fixed << Prof_time_CPU[i].time.count 	
					<< ":" << std::fixed << Prof_time_CPU[i].time.avg 	
					<< ":" << std::fixed << Prof_time_CPU[i].time.min 	
					<< ":" << std::fixed << Prof_time_CPU[i].time.max 	
					<< ":" << std::fixed << Prof_time_CPU[i].time.standard;
			found = checkstring(Prof_time_CPU[i].additonal);//1 wenn Prof_time_CPU[i].name ungueltig 
			if ((Prof_time_CPU[i].additonal=="")||(found))
				fp << ":"<< std::endl;
			else 	
				fp <<":"<< Prof_time_CPU[i].additonal<< std::endl;
		}
	fp <<"#"												//Trennzeile 4:GPU Zeiten
	 << "Name:Summe(s):Relative_CPU(%):Relative_GPU(%):Calls(1):Average(s):Minimum(s):Maximum(s):Standard deviation(s):additonal"<< std::endl;
		for(int i=0;i<Profiling_time_count;i++){
			int found = checkstring(Prof_time[i].name);//1 wenn Prof_time[i].name ungueltig 
			if ((Prof_time[i].name=="")||(found))
				fp << "GPU_Time "<<i;
			else 	
				fp << Prof_time[i].name;

			fp <<	   	":" << std::fixed << Prof_time[i].time.summ 
					<< ":" << std::fixed << Prof_time[i].time.prozent_CPU
					<< ":" << std::fixed << Prof_time[i].time.prozent_GPU
					<< ":" << std::fixed << Prof_time[i].time.count 	
					<< ":" << std::fixed << Prof_time[i].time.avg 	
					<< ":" << std::fixed << Prof_time[i].time.min 	
					<< ":" << std::fixed << Prof_time[i].time.max 	
					<< ":" << std::fixed << Prof_time[i].time.standard;
			found = checkstring(Prof_time[i].additonal);//1 wenn Prof_time[i].name ungueltig 
			if ((Prof_time[i].additonal=="")||(found))
				fp << ":"<< std::endl;
			else 	
				fp <<":"<< Prof_time[i].additonal<< std::endl;
		}
	fp <<"#"												//Trennzeile 5:Initialisierungs Zeiten
	 << "Name:Summe(s):Faktor_CPU(1)"<< std::endl;
		for(int i=0;i<Profiling_time_init_count;i++){
			int found = checkstring(Prof_time_init[i].name);//1 wenn Prof_time_init[i].name ungueltig 
			if ((Prof_time_CPU[i].name=="")||(found))
				fp << "Initialisation_Time "<<i;
			else 	
				fp << Prof_time_init[i].name;

			fp<<		":"<< std::fixed << Prof_time_init[i].time.summ
					<<":" << std::fixed << (Prof_time_init[i].time.prozent_CPU/100.0)<< std::endl;
		}
	fp <<"#"												//Trennzeile 6:Memcopy
	 << "Name:Time summ(s):Relative_CPU(%):Relative_GPU(%):Calls(1):Average(s):Minimum(s):Maximum(s):Standard deviation(s):(Memory)summ(Byte):Average(Byte):Minimum(Byte):Maximum(Byte):Standard deviation(Byte):(Throughput)Average(Byte/s):Minimum(Byte/s):Maximum(Byte/s):Standard deviation(Byte/s):additonal"<< std::endl;
		for(int i=0;i<Profiling_memcopy_count;i++){
			int found = checkstring(Prof_memcopy[i].name);//1 wenn Prof_time_CPU[i].name ungueltig 
			if ((Prof_memcopy[i].name=="")||(found))
				fp << "Memcopy_Time "<<i;
			else 	
				fp << Prof_memcopy[i].name;

			fp <<	   	":" << std::fixed << Prof_memcopy[i].time.summ 
					<< ":" << std::fixed << Prof_memcopy[i].time.prozent_CPU
					<< ":" << std::fixed << Prof_memcopy[i].time.prozent_GPU
					<< ":" << std::fixed << Prof_memcopy[i].time.count 	
					<< ":" << std::fixed << Prof_memcopy[i].time.avg 	
					<< ":" << std::fixed << Prof_memcopy[i].time.min 	
					<< ":" << std::fixed << Prof_memcopy[i].time.max 	
					<< ":" << std::fixed << Prof_memcopy[i].time.standard
					<< ":" << std::fixed << Prof_memcopy[i].memorysize.summ 	
					<< ":" << std::fixed << Prof_memcopy[i].memorysize.avg 	
					<< ":" << std::fixed << Prof_memcopy[i].memorysize.min 	
					<< ":" << std::fixed << Prof_memcopy[i].memorysize.max 	
					<< ":" << std::fixed << Prof_memcopy[i].memorysize.standard
					<< ":" << std::fixed << Prof_memcopy[i].memorythroughput.avg 	
					<< ":" << std::fixed << Prof_memcopy[i].memorythroughput.min 	
					<< ":" << std::fixed << Prof_memcopy[i].memorythroughput.max 	
					<< ":" << std::fixed << Prof_memcopy[i].memorythroughput.standard;
			found = checkstring(Prof_memcopy[i].additonal);//1 wenn Prof_time[i].name ungueltig 
			if ((Prof_memcopy[i].additonal=="")||(found))
				fp << ":"<< std::endl;
			else 	
				fp <<":"<< Prof_memcopy[i].additonal<< std::endl;
		}
	fp <<"#"												//Trennzeile 7:CPU Cycles
	 << "Name:Summe(1):Calls(1):Average(1):Minimum(1):Maximum(1):Standard deviation(1):additonal"<< std::endl;
	fp <<"#"												//Trennzeile 8:Messfehler
	 << "Name:Average(.):Minimum(.):Maximum(.):Standard deviation(.)"<< std::endl;
		int i=Profiling_time_count;
			fp << "GPU time Error:"<< std::fixed << Prof_time[i].time.avg 	
					<< ":" << std::fixed << Prof_time[i].time.min 	
					<< ":" << std::fixed << Prof_time[i].time.max 	
					<< ":" << std::fixed << Prof_time[i].time.standard<< std::endl;
		    i=Profiling_time_CPU_count;
			fp << "CPU time Error:"<< std::fixed << Prof_time_CPU[i].time.avg 	
					<< ":" << std::fixed << Prof_time_CPU[i].time.min 	
					<< ":" << std::fixed << Prof_time_CPU[i].time.max 	
					<< ":" << std::fixed << Prof_time_CPU[i].time.standard<< std::endl;

	fp <<"#"												//Trennzeile 9:Thread statistic
	 << "Name:additonal:Thread count:core count:[Threadnumber[,CPUnumber=Items]*]*(Thread count) Example:Hello World:is great:3:0,2=100:1,1=50,3=50:2,2=1,13=7000"<< std::endl;

	return 1;
}
"""

openmp_profile_body=\
"""
#include "Profiling.h"

/*
 *  Preinitialize Profiling class
 */
Profiling::Profiling() {
    Profiling_time_CPU_count=0;
    Profiling_cycles_CPU_count=0;
    Profiling_thread_count=0;
    Profiling_overall_count=1;
    thread_count=0;
    core_count=0;

    Profil=1;

    Prof_time_CPU=NULL;
    Prof_cycles_CPU=NULL;
    Prof_thread_statistic=NULL;
    Prof_general=NULL;
    Generaltext="";

    // initialize PAPI
    if (PAPI_library_init(PAPI_VER_CURRENT) != PAPI_VER_CURRENT)
        exit(1);

    // initialize time units, common profiling unit is s, this are transforming
    // units for command-line output
    time_units.push_back(std::pair<std::string, double>("us ", 1.0E6));
    time_units.push_back(std::pair<std::string, double>("ms ", 1.0E3));
    time_units.push_back(std::pair<std::string, double>("s ", 1.0));

    // default output in secconds
    used_time_unit = TimeUnits::SECS;
}

/*
 *  Destruct Profiling class
 */
Profiling::~Profiling() {
    //Delete existing Profiling Arrays
    if(Prof_time_CPU!=NULL) {
        for(int i=0;i<Profiling_time_CPU_count+1;i++) //+1->Messfehler
        { 
            delete [] Prof_time_CPU[i].time.maxarray;
            delete [] Prof_time_CPU[i].time.minarray;
        }
        delete[] Prof_time_CPU;
    }

    if(Prof_cycles_CPU!=NULL){
        for(int i=0;i<Profiling_cycles_CPU_count+1;i++)//+1-->Messfehler
        {
            delete [] Prof_cycles_CPU[i].time.maxarray;
            delete [] Prof_cycles_CPU[i].time.minarray;
        }
        delete [] Prof_cycles_CPU;
    }

    if(Prof_general!=NULL)
        delete[] Prof_general;

    if(Prof_thread_statistic!=NULL) {
        for(int i=0;i<Profiling_thread_count;i++)
        {
            for(int j=0;j<thread_count;j++)
            {
                delete [] Prof_thread_statistic[i].thread[j].core;
            }
            delete [] Prof_thread_statistic[i].thread;
        }
        delete [] Prof_thread_statistic;
    }
}

/*
 *  Init
 */
void Profiling::init(int extended) {
    if( Profil ) {
        //Delete preexisting Profiling Arrays
        if(Prof_time_CPU!=NULL){
            for(int i=0;i<Profiling_time_CPU_count+1;i++)//+1->Messfehler
            {
                delete[] Prof_time_CPU[i].time.maxarray;
                delete[] Prof_time_CPU[i].time.minarray;
            }
            delete[] Prof_time_CPU;
        }
        if(Prof_cycles_CPU!=NULL){
            for(int i=0;i<Profiling_cycles_CPU_count+1;i++)//+1-->Messfehler
            {
                delete[] Prof_cycles_CPU[i].time.maxarray;
                delete[] Prof_cycles_CPU[i].time.minarray;
            }
            delete[] Prof_cycles_CPU;
        }

        if(Prof_general!=NULL)
            delete[] Prof_general;
    
%(init)s
    
        //Profiling Array allocate
        Prof_time_CPU= new Profiling_time[Profiling_time_CPU_count+1];
        Prof_cycles_CPU= new Profiling_time[Profiling_cycles_CPU_count+1];
        Prof_general= new Profiling_general[Profiling_overall_count+1];
		Prof_cache_miss = new Profiling_cache_miss[Profiling_total_cache_miss_count+1];
    
%(init2)s
        //additional initializations
        if ((extended & INIT_THREAD)==INIT_THREAD)
            init_thread();
        if ((extended & INIT_OUTLIER)==INIT_OUTLIER)
            init_outlier();
		if ((extended & INIT_PAPI_EVENTS)==INIT_PAPI_EVENTS)
        	init_papi_events();
    }
}

void Profiling::init_thread()
{
    if(Profil){

        //Determinate core count of the System
        if (core_count==0) {
            const PAPI_hw_info_t *hwinfo = NULL;
            if ((hwinfo = PAPI_get_hardware_info()) != NULL){
                core_count=hwinfo->totalcpus;
            } else {
                core_count=4;
                std::cout << "no hardware information retrieved from PAPI, assume hard coded number of cores: " << core_count << std::endl;
            }
        }
        //Delete preexisting thread-Arrays
        if(Prof_thread_statistic!=NULL){
            for(int i=0;i<Profiling_thread_count;i++)
            {
                for(int j=0;j<thread_count;j++)
                {
                    delete[] Prof_thread_statistic[i].thread[j].core;
                }
                delete[] Prof_thread_statistic[i].thread;
            }
            delete[] Prof_thread_statistic;
        }
        //Profiling thread-Array allocate
        Prof_thread_statistic= new Profiling_thread_statistic[Profiling_thread_count];
    	for(int i=0;i<Profiling_thread_count;i++) 
    	{
    		Prof_thread_statistic[i].thread=new Profiling_thread_statistic_core[thread_count];
    		for(int j=0;j<thread_count;j++) 
    		{
    			Prof_thread_statistic[i].thread[j].core=new Profiling_thread_statistic_unit[core_count];
    		}
    	}
    }
}

void Profiling::init_outlier()
{
    if(Profil){
        //Profiling outlier-System arrays allocate
        for(int i=0;i<Profiling_time_CPU_count+1;i++)//+1-->Messfehler
        {
            Prof_time_CPU[i].time.maxarray=new double[Prof_time_CPU[i].time.maxac+1];
            for(int j=0;j<=Prof_time_CPU[i].time.maxac;j++)
                Prof_time_CPU[i].time.maxarray[j]=FLT_MIN;
            
            Prof_time_CPU[i].time.minarray=new double[Prof_time_CPU[i].time.minac+1];
            for(int j=0;j<=Prof_time_CPU[i].time.minac;j++)
                Prof_time_CPU[i].time.minarray[j]=FLT_MAX;
        }
        
        for(int i=0;i<Profiling_cycles_CPU_count+1;i++)//+1-->Messfehler
        {
            Prof_cycles_CPU[i].time.maxarray=new double[Prof_cycles_CPU[i].time.maxac+1];
            for(int j=0;j<=Prof_cycles_CPU[i].time.maxac;j++)
                Prof_cycles_CPU[i].time.maxarray[j]=FLT_MIN;

            Prof_cycles_CPU[i].time.minarray=new double[Prof_cycles_CPU[i].time.minac+1];
            for(int j=0;j<=Prof_cycles_CPU[i].time.minac;j++)
                Prof_cycles_CPU[i].time.minarray[j]=FLT_MAX;
        }
    }
}

void check_papi_error(int err, std::string func = std::string()) {
	std::cout << "Call of '" << func << "' lead to error: " << err << std::endl;
}

void Profiling::init_papi_events() {
	int err = PAPI_NULL;

	// default, no events attached
	total_cache_miss = PAPI_NULL;

	// try to initialize events
	err = PAPI_create_eventset(&total_cache_miss);
	if ( err != PAPI_OK ) {
		check_papi_error(err);
	} else {
		err = PAPI_add_event(total_cache_miss, PAPI_L1_TCM);
		if ( err != PAPI_OK )
			check_papi_error(err, "PAPI_add_event: PAPI_L1_TCM");

		err = PAPI_add_event(total_cache_miss, PAPI_L2_TCM);
		if ( err != PAPI_OK )
			check_papi_error(err, "PAPI_add_event: PAPI_L2_TCM");

		err = PAPI_add_event(total_cache_miss, PAPI_L3_TCM);
		if ( err != PAPI_OK )
			check_papi_error(err, "PAPI_add_event: PAPI_L3_TCM");
	}
}

/*
 *   Error Messurement
 */
void Profiling::error_CPU_time_prof()
{
  if(Profil){
    start_CPU_time_prof(Profiling_time_CPU_count);
    stop_CPU_time_prof(Profiling_time_CPU_count);
  }
}

void Profiling::error_CPU_cycles_prof()
{
  if(Profil){
    start_CPU_cycles_prof(Profiling_cycles_CPU_count);
    stop_CPU_cycles_prof(Profiling_cycles_CPU_count);
  }
}

/*
    CPU Time
*/
void Profiling::start_CPU_time_prof( int number)
{
  if(Profil){
    Prof_time_CPU[number].start = PAPI_get_real_usec();    
  }
}
    
void Profiling::stop_CPU_time_prof( int number,int directevaluate)
{
  if(Profil){
    Prof_time_CPU[number].stop = PAPI_get_real_usec();

    if (directevaluate){
            evaluate_CPU_time_prof(number);
     }
  }
}

void Profiling::evaluate_CPU_time_prof( int number)
{
  if(Profil){
	Prof_time_CPU[number].calculated=0;
	
	double dt_ms;
	std::cout.precision(8);

    //pre-evaluate CPU time
    dt_ms=((double)(Prof_time_CPU[number].stop-Prof_time_CPU[number].start))/1000.0;//Launch time
    dt_ms/=1000.0;//ms => s

    Prof_time_CPU[number].time.summ+=dt_ms;
    Prof_time_CPU[number].time.count++;
    Prof_time_CPU[number].time.summsqr+=square(dt_ms);
    //(dt_ms<Prof_time_CPU[number].time.min)?(Prof_time_CPU[number].time.min=dt_ms):1;
    //(Prof_time_CPU[number].time.max<dt_ms)?(Prof_time_CPU[number].time.max=dt_ms):1;//min/max

    //Outlier-System Max calculation
    if(Prof_time_CPU[number].time.maxarray[0]<dt_ms){
        if (Prof_time_CPU[number].time.maxac==0)
            Prof_time_CPU[number].time.maxarray[0]=dt_ms;
        for(int i=1;i<=Prof_time_CPU[number].time.maxac;i++){
            if(Prof_time_CPU[number].time.maxarray[i]<dt_ms)
                if(i==Prof_time_CPU[number].time.maxac)
                    Prof_time_CPU[number].time.maxarray[i]=dt_ms;
                else
                    Prof_time_CPU[number].time.maxarray[i-1]=Prof_time_CPU[number].time.maxarray[i];
            else{
                Prof_time_CPU[number].time.maxarray[i-1]=dt_ms;
                break;
            }
        }
    }

    //Outlier-System Min calculation
    if(Prof_time_CPU[number].time.minarray[0]>dt_ms){
        if (Prof_time_CPU[number].time.minac==0)
            Prof_time_CPU[number].time.minarray[0]=dt_ms;
        for(int i=1;i<=Prof_time_CPU[number].time.minac;i++){
            if(Prof_time_CPU[number].time.minarray[i]>dt_ms)
            if(i==Prof_time_CPU[number].time.minac)
                    Prof_time_CPU[number].time.minarray[i]=dt_ms;
                else
                    Prof_time_CPU[number].time.minarray[i-1]=Prof_time_CPU[number].time.minarray[i];
            else{
                Prof_time_CPU[number].time.minarray[i-1]=dt_ms;
                break;
            }
        }
    }

	// storing data
	if (Prof_time_CPU[number].storeRawData) {
		Prof_time_CPU[number].time.rawData.push_back(dt_ms);
	}
  }
}

/*
    CPU Cycles
*/
void Profiling::start_CPU_cycles_prof( int number)
{
  if(Profil){
    Prof_cycles_CPU[number].start = PAPI_get_real_cyc();    
  }
}
    
void Profiling::stop_CPU_cycles_prof( int number,int directevaluate)
{
  if(Profil){
    Prof_cycles_CPU[number].stop = PAPI_get_real_cyc();

    if (directevaluate){
            evaluate_CPU_cycles_prof(number);
     }
  }
}

void Profiling::evaluate_CPU_cycles_prof( int number)
{
  if(Profil){
	Prof_cycles_CPU[number].calculated=0;
    double dt;

    //pre-evaluate CPU cycles
    dt=((double)(Prof_cycles_CPU[number].stop-Prof_cycles_CPU[number].start));

    Prof_cycles_CPU[number].time.summ+=dt;
    Prof_cycles_CPU[number].time.count++;
    Prof_cycles_CPU[number].time.summsqr+=square(dt);
    //(dt<Prof_cycles_CPU[number].time.min)?(Prof_cycles_CPU[number].time.min=dt):1;
    //(Prof_cycles_CPU[number].time.max<dt)?(Prof_cycles_CPU[number].time.max=dt):1;//min/max

    //Outlier-System Max calculation
	if(Prof_cycles_CPU[number].time.maxarray[0]<dt){
		if (Prof_cycles_CPU[number].time.maxac==0)
			Prof_cycles_CPU[number].time.maxarray[0]=dt;

		for(int i=1;i<=Prof_cycles_CPU[number].time.maxac;i++){
			if(Prof_cycles_CPU[number].time.maxarray[i]<dt)
				if(i==Prof_cycles_CPU[number].time.maxac)
					Prof_cycles_CPU[number].time.maxarray[i]=dt;
				else
					Prof_cycles_CPU[number].time.maxarray[i-1]=Prof_cycles_CPU[number].time.maxarray[i];
			else{
				Prof_cycles_CPU[number].time.maxarray[i-1]=dt;
				break;
			}
		}
	}

    //Outlier-System Min calculation
	if(Prof_cycles_CPU[number].time.minarray[0]>dt){
		if (Prof_cycles_CPU[number].time.minac==0)
			Prof_cycles_CPU[number].time.minarray[0]=dt;

		for(int i=1;i<=Prof_cycles_CPU[number].time.minac;i++){
			if(Prof_cycles_CPU[number].time.minarray[i]>dt)
				if(i==Prof_cycles_CPU[number].time.minac)
					Prof_cycles_CPU[number].time.minarray[i]=dt;
				else
					Prof_cycles_CPU[number].time.minarray[i-1]=Prof_cycles_CPU[number].time.minarray[i];
			else{
				Prof_cycles_CPU[number].time.minarray[i-1]=dt;
				break;
			}
		}
	}

	// storing data
	if (Prof_cycles_CPU[number].storeRawData) {
		Prof_cycles_CPU[number].time.rawData.push_back(dt);
	}
  }
}

/*
 *  Overall Time
 */
void Profiling::start_overall_time_prof(int number)
{
    if(Profil){
        Prof_general[number].start = PAPI_get_real_usec();    
    }
}
    
void Profiling::stop_overall_time_prof(int number,int directevaluate)
{
    if(Profil) {
        Prof_general[number].stop = PAPI_get_real_usec();
        
        if (directevaluate)
            evaluate_overall_time_prof(number);
    }
}

void Profiling::evaluate_overall_time_prof(int number)
{
    if (Profil) {
        // [hdin] quickfix: added a '+=' to overcome a problem regarding multiple calls of ANNarchy::run
        Prof_general[number].CPU_summ +=((double)(Prof_general[number].stop-Prof_general[number].start))/1000.0/1000.0;//s
    }
}

/**
 *	Cache statistics
 */
void Profiling::start_total_cache_miss( int number ) {
	int err = PAPI_NULL;

	err = PAPI_reset(total_cache_miss);
	if (err != PAPI_OK)
		check_papi_error(err);

	err = PAPI_start(total_cache_miss);
	if (err != PAPI_OK)
		check_papi_error(err);
}

void Profiling::stop_total_cache_miss( int number ) {
	long_long values[3];
	int err = PAPI_NULL;

	err = PAPI_stop(total_cache_miss, values);
	if (err != PAPI_OK)
		check_papi_error(err);

	// add up mean incremental
	Prof_cache_miss[number].n += 1;
	Prof_cache_miss[number].L1 += (values[0] - Prof_cache_miss[number].L1) / Prof_cache_miss[number].n;
	Prof_cache_miss[number].L2 += (values[1] - Prof_cache_miss[number].L2) / Prof_cache_miss[number].n;
	Prof_cache_miss[number].L3 += (values[2] - Prof_cache_miss[number].L3) / Prof_cache_miss[number].n;

	// store if necessary
	if ( Prof_cache_miss[number].storeRawData ) {
		Prof_cache_miss[number].rawL1.push_back(values[0]);
		Prof_cache_miss[number].rawL2.push_back(values[1]);
		Prof_cache_miss[number].rawL3.push_back(values[2]);
	}
}

/*
 *  Thread statistic
 */
void Profiling::thread_statistic_run( int number ) {
  if(Profil){
    Prof_thread_statistic[number].thread[omp_get_thread_num()].core[sched_getcpu()].count++;
  }
}

/*
    RESET
*/
void Profiling::reset_overall_time_prof( int number )
{
    Prof_general[number].CPU_summ=0;//s
}

void Profiling::reset_CPU_time_prof(int number)
{
	Prof_time_CPU[number].calculated=0;

    Prof_time_CPU[number].time.count=0;
    Prof_time_CPU[number].time.summ=0;
    Prof_time_CPU[number].time.summsqr=0;
    //Prof_time_CPU[number].time.min=FLT_MAX;
    //Prof_time_CPU[number].time.max=FLT_MIN;
    for(int j=0;j<=Prof_time_CPU[number].time.maxac;j++)Prof_time_CPU[number].time.maxarray[j]=FLT_MIN;
    for(int j=0;j<=Prof_time_CPU[number].time.minac;j++)Prof_time_CPU[number].time.minarray[j]=FLT_MAX;
}

void Profiling::reset_CPU_cycles_prof(int number)
{
	Prof_cycles_CPU[number].calculated=0;

    Prof_cycles_CPU[number].time.count=0;
    Prof_cycles_CPU[number].time.summ=0;
    Prof_cycles_CPU[number].time.summsqr=0;
    //Prof_cycles_CPU[number].time.min=FLT_MAX;
    //Prof_cycles_CPU[number].time.max=FLT_MIN;
    for(int j=0;j<=Prof_cycles_CPU[number].time.maxac;j++)Prof_cycles_CPU[number].time.maxarray[j]=FLT_MIN;
    for(int j=0;j<=Prof_cycles_CPU[number].time.minac;j++)Prof_cycles_CPU[number].time.minarray[j]=FLT_MAX;
}

void Profiling::reset_thread_statistic(int number)
{
    for(int i=0;i<thread_count;i++)
    {
        for(int j=0;j<core_count;j++)
        {
            Prof_thread_statistic[number].thread[i].core[j].count=0;
        }
    }
}

/*
 *    GET
 *        return: Average
 */
double Profiling::get_CPU_time_prof( int number){
	evaluate_calc(1,number);
	evaluate_recalc(1,number);

	return Prof_time_CPU[number].time.avg;
}

double Profiling::get_CPU_cycles_prof( int number){
	evaluate_calc(2,number);
	evaluate_recalc(2,number);

	return Prof_cycles_CPU[number].time.avg;
}

double Profiling::get_overall_time_prof(int number){
	return Prof_general[number].CPU_summ;
}

/*
    Evaluation
*/
void Profiling::evaluate(int disp, int file,const char * filename)
{
    evaluate_calc();
    if (disp)evaluate_disp();
    if (file)evaluate_file(filename);
    evaluate_recalc();
}

/*
	Calculation
		sec:0 Calculate all
		sec:1 Calculate the CPU time[numer]
		sec:2 Calculate the CPU cycles[numer]
		sec:3 Calculate the threadstatistik[numer]
*/
void Profiling::evaluate_calc(int sec, int number)
{
    for(int i=0;i<Profiling_time_CPU_count+1;i++){//+1 for calc error-stuff
		if ((!Prof_time_CPU[i].calculated)&&((!sec)||((sec==1)&&(number=i)))){
	        if (Prof_time_CPU[i].time.maxac){
	            for(int j=1;j<=Prof_time_CPU[i].time.maxac;j++){
	                Prof_time_CPU[i].time.summ-=Prof_time_CPU[i].time.maxarray[j];
	                Prof_time_CPU[i].time.count--;
	                Prof_time_CPU[i].time.summsqr-=square(Prof_time_CPU[i].time.maxarray[j]);
	            }
	        }

	        if (Prof_time_CPU[i].time.minac){
	            for(int j=1;j<=Prof_time_CPU[i].time.minac;j++){
	                Prof_time_CPU[i].time.summ-=Prof_time_CPU[i].time.minarray[j];
	                Prof_time_CPU[i].time.count--;
	                Prof_time_CPU[i].time.summsqr-=square(Prof_time_CPU[i].time.minarray[j]);
	            }
	        }

            Prof_time_CPU[i].time.min=Prof_time_CPU[i].time.minarray[0];
            Prof_time_CPU[i].time.max=Prof_time_CPU[i].time.maxarray[0];
	        Prof_time_CPU[i].time.avg=Prof_time_CPU[i].time.summ/Prof_time_CPU[i].time.count;
	        Prof_time_CPU[i].time.standard=sqrt(Prof_time_CPU[i].time.summsqr/Prof_time_CPU[i].time.count-square(Prof_time_CPU[i].time.avg));
	        Prof_time_CPU[i].time.prozent_CPU=100.0*Prof_time_CPU[i].time.summ/Prof_general[Prof_time_CPU[i].overall_time].CPU_summ;
	        
	        //Prof_time_CPU[i].calculated=1;
		}
    }
    
    for(int i=0;i<Profiling_cycles_CPU_count+1;i++){//+1 for calc error-stuff
		if ((!Prof_cycles_CPU[i].calculated)&&((!sec)||((sec==2)&&(number=i)))){
	        if (Prof_cycles_CPU[i].time.maxac){
	            for(int j=1;j<=Prof_cycles_CPU[i].time.maxac;j++){
	                Prof_cycles_CPU[i].time.summ-=Prof_cycles_CPU[i].time.maxarray[j];
	                Prof_cycles_CPU[i].time.count--;
	                Prof_cycles_CPU[i].time.summsqr-=square(Prof_cycles_CPU[i].time.maxarray[j]);
	            }
	        }
	        if (Prof_cycles_CPU[i].time.minac){
	            for(int j=1;j<=Prof_cycles_CPU[i].time.minac;j++){
	                Prof_cycles_CPU[i].time.summ-=Prof_cycles_CPU[i].time.minarray[j];
	                Prof_cycles_CPU[i].time.count--;
	                Prof_cycles_CPU[i].time.summsqr-=square(Prof_cycles_CPU[i].time.minarray[j]);
	            }
	        }
	        
            Prof_cycles_CPU[i].time.min=Prof_cycles_CPU[i].time.minarray[0];
            Prof_cycles_CPU[i].time.max=Prof_cycles_CPU[i].time.maxarray[0];
	        Prof_cycles_CPU[i].time.avg=Prof_cycles_CPU[i].time.summ/Prof_cycles_CPU[i].time.count;
	        Prof_cycles_CPU[i].time.standard=sqrt(Prof_cycles_CPU[i].time.summsqr/Prof_cycles_CPU[i].time.count-square(Prof_cycles_CPU[i].time.avg));
	        Prof_cycles_CPU[i].time.prozent_CPU=0;//100.0*Prof_cycles_CPU[i].time.summ/Prof_general.CPU_cycles;
	        
	        //Prof_cycles_CPU[i].calculated=1;
	    }
    }
    
    for(int i=0;i<Profiling_thread_count;i++) {//+1 for calc error-stuff
    	if ((!sec)||((sec==3)&&(number=i))) {
	        int max=0;
	        for(int j=0;j<thread_count;j++)
	        {
	            for(int k=0;k<core_count;k++)
	            {
	                if(Prof_thread_statistic[i].thread[j].core[k].count)max=j;
	            }
	        }
	        Prof_thread_statistic[i].used_threads=max;
	    }
    }
}

/*
 *
 *  recalc: reset changes from evaluate_calc -> needed for thrash-System
 *
 *  change only sum(,squaresumm) and count.
 *
 */
void Profiling::evaluate_recalc(int sec,int number) {
	for(int i=0;i<Profiling_time_CPU_count+1;i++){//+1 for calc error-stuff
		if ((!Prof_time_CPU[i].calculated)&&((!sec)||((sec==1)&&(number=i)))){
			if (Prof_time_CPU[i].time.maxac){
				for(int j=1;j<=Prof_time_CPU[i].time.maxac;j++){
					Prof_time_CPU[i].time.summ+=Prof_time_CPU[i].time.maxarray[j];
					Prof_time_CPU[i].time.count++;
					Prof_time_CPU[i].time.summsqr+=square(Prof_time_CPU[i].time.maxarray[j]);
				}
			}
			if (Prof_time_CPU[i].time.minac){
				for(int j=1;j<=Prof_time_CPU[i].time.minac;j++){
					Prof_time_CPU[i].time.summ+=Prof_time_CPU[i].time.minarray[j];
					Prof_time_CPU[i].time.count++;
					Prof_time_CPU[i].time.summsqr+=square(Prof_time_CPU[i].time.minarray[j]);
				}
			}
			Prof_time_CPU[i].calculated=1;
		}
	}
	for(int i=0;i<Profiling_cycles_CPU_count+1;i++){//+1 for calc error-stuff
		if ((!Prof_cycles_CPU[i].calculated)&&((!sec)||((sec==2)&&(number=i)))){
			if (Prof_cycles_CPU[i].time.maxac){
				for(int j=1;j<=Prof_cycles_CPU[i].time.maxac;j++){
					Prof_cycles_CPU[i].time.summ+=Prof_cycles_CPU[i].time.maxarray[j];
					Prof_cycles_CPU[i].time.count++;
					Prof_cycles_CPU[i].time.summsqr+=square(Prof_cycles_CPU[i].time.maxarray[j]);
				}
			}
			if (Prof_cycles_CPU[i].time.minac){
				for(int j=1;j<=Prof_cycles_CPU[i].time.minac;j++){
					Prof_cycles_CPU[i].time.summ+=Prof_cycles_CPU[i].time.minarray[j];
					Prof_cycles_CPU[i].time.count++;
					Prof_cycles_CPU[i].time.summsqr+=square(Prof_cycles_CPU[i].time.minarray[j]);
				}
			}
			Prof_cycles_CPU[i].calculated=1;
		}
	}
	for(int i=0;i<Profiling_thread_count;i++){
		if ((!sec)||((sec==3)&&(number=i))){
		}
	}
}

//Print to Console
void Profiling::evaluate_disp() {
    if ( used_time_unit == TimeUnits::SECS ) { std::cout.precision(8); } else { std::cout.precision(4); }
    
	for(int i=0;i<Profiling_overall_count;i++) {
		std::cout << "Overall time: "<< std::fixed << Prof_general[i].CPU_summ * time_units[used_time_unit].second	<< time_units[used_time_unit].first << std::endl;
	}

    
    // CPU time
    for(int i=0;i<Profiling_time_CPU_count;i++) {
        if ( Prof_time_CPU[i].time.count == 0 )
            continue; // no data

        int found = (Prof_time_CPU[i].name.find(":")!=std::string::npos)||(Prof_time_CPU[i].name.find("#")!=std::string::npos);//1 wenn Prof_time_CPU[i].name ungueltig 
        if ((Prof_time_CPU[i].name=="")||(found))
            std::cout << "CPU_Time "<<i;
        else     
			std::cout << Prof_time_CPU[i].name+" ";

		std::cout << " time: " << std::fixed << Prof_time_CPU[i].time.summ * time_units[used_time_unit].second << time_units[used_time_unit].first
				  << "Relative to CPU time: " << std::fixed << Prof_time_CPU[i].time.prozent_CPU<< "%% "
				  << "Average time: " << std::fixed << Prof_time_CPU[i].time.avg * time_units[used_time_unit].second << time_units[used_time_unit].first
				  << "Minimum time: " << std::fixed << Prof_time_CPU[i].time.min * time_units[used_time_unit].second << time_units[used_time_unit].first
				  << "Maximum time: " << std::fixed << Prof_time_CPU[i].time.max * time_units[used_time_unit].second << time_units[used_time_unit].first
				  << "Standard deviation: "<< std::fixed << Prof_time_CPU[i].time.standard * time_units[used_time_unit].second << time_units[used_time_unit].first 
                  << std::endl;
    }
    std::cout << std::endl;
    
    // CPU cycles
    for(int i=0;i<Profiling_cycles_CPU_count;i++) {
        if ( Prof_cycles_CPU[i].time.count == 0 )
            continue; // no data
        int found = (Prof_cycles_CPU[i].name.find(":")!=std::string::npos)||(Prof_cycles_CPU[i].name.find("#")!=std::string::npos);//1 wenn Prof_time_CPU[i].name ungueltig 
        if ((Prof_cycles_CPU[i].name=="")||(found))
            std::cout << "CPU_cycles "<<i;
        else     
            std::cout << Prof_cycles_CPU[i].name;
        
        std::cout <<" cycles: " << std::fixed << Prof_cycles_CPU[i].time.summ     << " "
                  //<< "Relative to CPU cycles: " << std::fixed << Prof_cycles_CPU[i].time.prozent_CPU<< " %% "
                  << "Average cycles: "      << std::fixed << Prof_cycles_CPU[i].time.avg     << " " 
                  << "Minimum cycles: "      << std::fixed << Prof_cycles_CPU[i].time.min     << " "
                  << "Maximum cycles: "      << std::fixed << Prof_cycles_CPU[i].time.max     << " "
                  << "Standard deviation: "<< std::fixed << Prof_cycles_CPU[i].time.standard     << " "<< std::endl;
    }
    std::cout     << std::endl;
        
    for(int i=0;i<Profiling_thread_count;i++){
        int found = (Prof_thread_statistic[i].name.find(":")!=std::string::npos)||(Prof_thread_statistic[i].name.find("#")!=std::string::npos);//1 wenn Prof_time_CPU[i].name ungueltig 
        if ((Prof_thread_statistic[i].name=="")||(found))
            std::cout << "Thread statistic "<<i;
        else     
            std::cout << Prof_thread_statistic[i].name;

        std::cout     <<":"<< std::endl;
        for(int j=0;j<thread_count;j++)
        {
            std::cout     <<"  Thread "<<j<<":"<< std::endl;
            for(int k=0;k<core_count;k++)
            {
                if(Prof_thread_statistic[i].thread[j].core[k].count)
                    std::cout     <<"    core "  << k << ": "<< Prof_thread_statistic[i].thread[j].core[k].count<<" units"<< std::endl;
            }
        }
    }
    std::cout << std::endl;
}

//Print to file
//return 0: no error
int Profiling::evaluate_file(const char * filename)
{
    std::ofstream fp;
    fp.open(filename,std::ios::out|std::ios::trunc);
	if (!(fp.is_open()))
		return 1;

	int found = (Generaltext.find("#")!=std::string::npos);//1 wenn Generaltext ungueltig 
	if (!(found))
		fp << Generaltext << std::endl;
    fp.precision(8);

    fp <<"#"                                                //Trennzeile 1:CPU Gesammtzeit
     << "Overall time: in s"<< std::endl;
	for(int i=0;i<Profiling_overall_count;i++){
		fp << std::fixed << Prof_general[i].CPU_summ << std::endl;
	}
    fp <<"#"                                                //Trennzeile 2:GPU Gesammtzeit
     << "On GPU only: in s"<< std::endl;
    fp <<"#"                                                //Trennzeile 3:CPU Zeiten
     << "Name:Overalltimenumber:Summe(s):Relative(%%):Calls(1):Average(s):Minimum(s):Maximum(s):Standard deviation(s):additonal"<< std::endl;
        for(int i=0;i<Profiling_time_CPU_count;i++){
            if ( Prof_time_CPU[i].time.count == 0 )
                continue; // no data
            int found = checkstring(Prof_time_CPU[i].name);//1 wenn Prof_time_CPU[i].name ungueltig 
            if ((Prof_time_CPU[i].name=="")||(found))
                fp << "CPU_Time "<<i;
            else     
                fp << Prof_time_CPU[i].name;

            fp << ":" << std::fixed << Prof_time_CPU[i].overall_time 
               << ":" << std::fixed << Prof_time_CPU[i].time.summ 
               << ":" << std::fixed << Prof_time_CPU[i].time.prozent_CPU
               << ":" << std::fixed << Prof_time_CPU[i].time.count     
               << ":" << std::fixed << Prof_time_CPU[i].time.avg     
               << ":" << std::fixed << Prof_time_CPU[i].time.min     
               << ":" << std::fixed << Prof_time_CPU[i].time.max     
               << ":" << std::fixed << Prof_time_CPU[i].time.standard;
            found = checkstring(Prof_time_CPU[i].additonal);//1 wenn Prof_time_CPU[i].name ungueltig 
            if ((Prof_time_CPU[i].additonal=="")||(found))
                fp << ":"<< std::endl;
            else     
                fp <<":"<< Prof_time_CPU[i].additonal<< std::endl;
        }
    fp <<"#"                                                //Trennzeile 4:GPU Zeiten
     << "Name:Overalltimenumber:Summe(s):Relative_CPU(%%):Relative_GPU(%%):Calls(1):Average(s):Minimum(s):Maximum(s):Standard deviation(s):additonal"<< std::endl;
    fp <<"#"                                                //Trennzeile 5:Initialisierungs Zeiten
     << "Name:Overalltimenumber:Summe(s):Faktor_CPU(1)"<< std::endl;
    fp <<"#"                                                //Trennzeile 6:Memcopy
     << "Name:Overalltimenumber;Time summ(s):Relative_CPU(%%):Relative_GPU(%%):Calls(1):Average(s):Minimum(s):Maximum(s):Standard deviation(s):(Memory)summ(Byte):Average(Byte):Minimum(Byte):Maximum(Byte):Standard deviation(Byte):(Throughput)Average(Byte/s):Minimum(Byte/s):Maximum(Byte/s):Standard deviation(Byte/s):additonal"<< std::endl;
    fp <<"#"                                                //Trennzeile 7:CPU Cycles
     << "Name:Summe(1):Calls(1):Average(1):Minimum(1):Maximum(1):Standard deviation(1):additonal"<< std::endl;
        for(int i=0;i<Profiling_cycles_CPU_count;i++){
            if ( Prof_cycles_CPU[i].time.count == 0 )
                continue; // no data
            int found = checkstring(Prof_cycles_CPU[i].name);//1 wenn name ungueltig 
            if ((Prof_cycles_CPU[i].name=="")||(found))
                fp << "CPU_cycles "<<i;
            else     
                fp << Prof_cycles_CPU[i].name;

            fp //<< ":" << std::fixed << Prof_cycles_CPU[i].overall_time
			   << ":" << std::fixed << Prof_cycles_CPU[i].time.summ
               //<< ":" << std::fixed << Prof_cycles_CPU[i].time.prozent_CPU
               << ":" << std::fixed << Prof_cycles_CPU[i].time.count     
               << ":" << std::fixed << Prof_cycles_CPU[i].time.avg     
               << ":" << std::fixed << Prof_cycles_CPU[i].time.min     
               << ":" << std::fixed << Prof_cycles_CPU[i].time.max     
               << ":" << std::fixed << Prof_cycles_CPU[i].time.standard;

            found = checkstring(Prof_cycles_CPU[i].additonal);//1 wenn name ungueltig 
            if ((Prof_cycles_CPU[i].additonal=="")||(found))
                fp << ":"<< std::endl;
            else     
                fp <<":"<< Prof_cycles_CPU[i].additonal<< std::endl;
        }
    fp <<"#"                                                //Trennzeile 8:Messfehler
     << "Name:Average(.):Minimum(.):Maximum(.):Standard deviation(.)"<< std::endl;
        int i=Profiling_cycles_CPU_count;
            fp << "CPU cycles Error:"<< std::fixed << Prof_cycles_CPU[i].time.avg     
                    << ":" << std::fixed << Prof_cycles_CPU[i].time.min     
                    << ":" << std::fixed << Prof_cycles_CPU[i].time.max     
                    << ":" << std::fixed << Prof_cycles_CPU[i].time.standard<< std::endl;
            i=Profiling_time_CPU_count;
            fp << "CPU time Error:"<< std::fixed << Prof_time_CPU[i].time.avg     
                    << ":" << std::fixed << Prof_time_CPU[i].time.min     
                    << ":" << std::fixed << Prof_time_CPU[i].time.max     
                    << ":" << std::fixed << Prof_time_CPU[i].time.standard<< std::endl;

    fp <<"#"                                                //Trennzeile 9:Thread statistic
     << "Name:additonal:Thread count:core count:[Threadnumber[,CPUnumber=Items]*]*(Thread count) Example:Hello World:is great:3:0,2=100:1,1=50,3=50:2,2=1,13=7000"<< std::endl;
        for(int i=0;i<Profiling_thread_count;i++){
            found = checkstring(Prof_thread_statistic[i].name);//1 wenn name ungueltig 
            if ((Prof_thread_statistic[i].name=="")||(found))
                fp << "Thread statistic "<<i;
            else     
                fp << Prof_thread_statistic[i].name;

            found = checkstring(Prof_thread_statistic[i].additonal);//1 wenn name ungueltig 
            if ((Prof_thread_statistic[i].additonal=="")||(found))
                fp << ":";
            else     
                fp <<":"<< Prof_thread_statistic[i].additonal;

            fp <<           ":" << std::fixed << Prof_thread_statistic[i].used_threads<<":" << std::fixed << core_count;
            for(int j=0;j<Prof_thread_statistic[i].used_threads;j++)
            {
                fp <<":j";
                for(int k=0;k<core_count;k++)
                {
                    if(Prof_thread_statistic[i].thread[j].core[k].count)
                        fp <<","<<k<<"="<< std::fixed << Prof_thread_statistic[i].thread[j].core[k].count;
                }
            }
            fp<< std::endl;
        }

    // [hdin] write out raw data to different files
    for(int i=0;i<Profiling_time_CPU_count;i++){
        if ( Prof_time_CPU[i].time.count == 0 || !Prof_time_CPU[i].storeRawData )
            continue;
        
        std::ofstream outfile(Prof_time_CPU[i].name+"_"+Prof_time_CPU[i].additonal+".csv", std::ios::out | std::ios::trunc);
        std::ostream_iterator<double> oi(outfile, ",\\n");
        copy(Prof_time_CPU[i].time.rawData.begin(), Prof_time_CPU[i].time.rawData.end(), oi);
    }

    for(int i=0;i<Profiling_total_cache_miss_count;i++){
        if ( !Prof_cache_miss[i].storeRawData )
            continue;
        
        std::ofstream outfile(Prof_cache_miss[i].name+"_"+Prof_cache_miss[i].additional+".csv", std::ios::out | std::ios::trunc);
        std::ostream_iterator<double> oi(outfile, ",\\n");
        copy(Prof_cache_miss[i].rawL1.begin(), Prof_cache_miss[i].rawL1.end(), oi);
        outfile<<std::endl;
        copy(Prof_cache_miss[i].rawL2.begin(), Prof_cache_miss[i].rawL2.end(), oi);
        outfile<<std::endl;
        copy(Prof_cache_miss[i].rawL3.begin(), Prof_cache_miss[i].rawL3.end(), oi);
    }

	fp.close();
	return 0;
}

/*
	File merger
		merge file:'infilename1' with 'infilename2'to file:'outfilename'
		Sectionsplitlines(start with '#') and the 'Generalsection' comes from File:infilename1	
	return:	0:no error
			1-3:can't open one of the Files
			4:Infile1 and Infile2 identical makes no sense
			5:one of the infiles is Damaged
*/
int Profiling::mergefiles(const char * infilename1,const char * infilename2,const char * outfilename)
{
	std::string line,hline;
	int section1=0;	
	int section2=0;	
	int overalltimes1=0,overalltimes1_2=0;
	int i=0;
	int end1=0;	
	int end2=0;	
	int no_h_line=0;	

	std::ifstream fpin1;
	fpin1.open(infilename1,std::ios::in);
	if (!(fpin1.is_open()))return 1;

	std::ifstream fpin2;
	if (infilename2!=infilename1)
		fpin2.open(infilename2,std::ios::in);
	else return 4;
	if (!(fpin2.is_open()))return 2;

	std::ofstream fp;
	if ((infilename2!=outfilename)&&(infilename1!=outfilename))
		fp.open(outfilename,std::ios::out|std::ios::trunc);
	else
		fp.open("TEMPORAL_PROFILING_LOG.log",std::ios::out|std::ios::trunc);
	if (!(fp.is_open()))return 3;

//header
	while ( (!section1)&&!end1 )
    {
		if (!getline (fpin1,line))end1=1;
		else
			if (line[0]=='#')section1++;
			fp << line << std::endl;
    }
	while ( (!section2)&&!end2 )
    {
		if (!getline (fpin2,line))end2=1;
		else
			if (line[0]=='#')section2++;
			//else fp << line << std::endl;
    }
//Overall time
	while ( (section1<2)&&!end1 )
    {
		if (!getline (fpin1,line))end1=1;
		else
			if (line[0]=='#'){
				section1++;
				hline=line;
			}
			else{ 
				overalltimes1++;
				fp << line << std::endl;
			}
    }
	while ( (section2<2)&&!end2 )
    {
		if (!getline (fpin2,line))end2=1;
		else
			if (line[0]=='#')section2++;
			else fp << line << std::endl;
    }
	fp << hline << std::endl;
//GPU overall time
	while ( (section1<3)&&!end1 )
    {
		if (!getline (fpin1,line))end1=1;
		else
			if (line[0]=='#'){
				section1++;
				hline=line;
			}
			else{ 
				overalltimes1_2++;
				fp << line << std::endl;
			}
    }
	while ( overalltimes1_2<overalltimes1 )//Fix to the same length of overalltimes(CPU/GPU)
    {
		overalltimes1_2++;
		fp << 0 << std::endl;
    }
	while ( (section2<3)&&!end2 )
    {
		if (!getline (fpin2,line))end2=1;
		else
			if (line[0]=='#')section2++;
			else fp << line << std::endl;
    }
	fp << hline << std::endl;
	i=3;
//rest time
	while ( (!end1)&&(!end2) ){
		i++;
		no_h_line=1;
		while ( (section1<i)&&!end1 )
		{
			if (!getline (fpin1,line))end1=1;
			else
				if (line[0]=='#'){
					section1++;
					hline=line;
					no_h_line=0;
				}
				else{ 
					fp << line << std::endl;
				}
		}
		while ( (section2<i)&&!end2 )
		{
			if (!getline (fpin2,line))end2=1;
			else
				if (line[0]=='#')section2++;
				else{ 
					if ((section2==3)||(section2==4)||(section2==5)||(section2==6)){//convert Overalltimenumbers
						int j=0;
						while(line[j]!=':'){
							fp << line[j];
							j++;
						}
						fp << line[j];
						j++;
						std::string helpstr;
						int k=0;
						while(line[j]!=':'){
							helpstr[k]=line[j];
							j++;
							k++;
						}
						int help=0;
						std::stringstream helphelp(helpstr);
						helphelp >> help;
						help+=overalltimes1;//infilename2's Overalltimes ar afer infilename1's
						fp<<help;
						while(j<line.length()){
							fp << line[j];
							j++;
						}
						fp << std::endl;
				
					}
					else fp << line << std::endl;
				}
		}
		if (!no_h_line)
			fp << hline << std::endl;
	}

	fpin1.close();
	fpin2.close();
	fp.close();
	if (section2!=section1) return 7;
	if ((infilename2==outfilename)||(infilename1==outfilename)){
		fp.open(outfilename,std::ios::out|std::ios::trunc);
		fpin1.open("TEMPORAL_PROFILING_LOG.log",std::ios::in);
		end1=0;
		while ( !end1 )
		{
			if (!getline (fpin1,line))end1=1;
			else fp << line << std::endl;
		}
		fpin1.close();
		fp.close();
	}
	return 0;
}
"""