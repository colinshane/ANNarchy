# Linux, Seq or OMP
linux_omp_template = """# Makefile generated by ANNarchy
all:
\tcython -%(py_major)s ANNarchyCore%(net_id)s.pyx --cplus
\t%(compiler)s %(cpu_flags)s -shared -fPIC -fpermissive -std=c++0x  %(openmp)s \\
        *.cpp -o ANNarchyCore%(net_id)s.so \\
        %(python_include)s -I%(numpy_include)s \\
        %(python_lib)s %(libs)s
\t mv ANNarchyCore%(net_id)s.so ../..

clean:
\trm -rf *.o
\trm -rf *.so
"""

# Linux, CUDA
linux_cuda_template = """# Makefile generated by ANNarchy
all:
\tcython -%(py_major)s ANNarchyCore%(net_id)s.pyx --cplus
\tnvcc %(cuda_gen)s %(gpu_flags)s  -Xcompiler -fPIC -shared \\
        *.cu *.cpp -o ANNarchyCore%(net_id)s.so \\
        %(python_include)s -I%(numpy_include)s \\
        -lpython%(py_version)s  %(libs)s
\t mv ANNarchyCore%(net_id)s.so ../..

clean:
\trm -rf *.o
\trm -rf *.so
"""

# OSX, Seq only
osx_seq_template = """# Makefile generated by ANNarchy
all:
\tcython -%(py_major)s ANNarchyCore%(net_id)s.pyx --cplus
\t%(compiler)s -stdlib=libc++ -std=c++11 -fPIC -shared %(cpu_flags)s -fpermissive \\
        *.cpp -o ANNarchyCore%(net_id)s.so \\
        %(python_include)s -I%(numpy_include)s \\
        %(python_lib)s %(libs)s
\t mv ANNarchyCore%(net_id)s.so ../..

clean:
\trm -rf *.o
\trm -rf *.so
"""
