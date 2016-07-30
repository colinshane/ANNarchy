"""

    ProfileGenerator.py

    This file is part of ANNarchy.

    Copyright (C) 2016-2018  Julien Vitay <julien.vitay@gmail.com>,
    Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ANNarchy is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
import ANNarchy.core.Global as Global

class ProfileGenerator(object):
    """
    Base class to extent the generated code by profiling annotations.
    """
    def __init__(self, annarchy_dir, net_id):
        """
        Initialize ProfileGenerator.
        """
        self.annarchy_dir = annarchy_dir
        self._net_id = net_id

    def generate(self):
        raise NotImplementedError

    def generate_body_dict(self):
        """
        Creates a dictionary, contain profile code snippets.
        """
        body_dict = {
            'prof_include': "",
            'prof_step_pre': "",
            'prof_step_post': "",
            'prof_run_pre': "",
            'prof_run_post': "",
            'prof_proj_psp_pre': "",
            'prof_proj_psp_post': "",
            'prof_neur_step_pre': "",
            'prof_neur_step_post': ""
        }
        return body_dict

    def generate_init_population(self, pop):
        raise NotImplementedError

    def generate_init_projection(self, proj):
        raise NotImplementedError

    def annotate_computesum_rate(self, proj, code):
        raise NotImplementedError

    def annotate_computesum_spiking(self, proj, code):
        raise NotImplementedError

    def annotate_update_synapse(self, proj, code):
        raise NotImplementedError

    def annotate_update_neuron(self, pop, code):
        raise NotImplementedError

    def _generate_header(self):
        """
        generate Profiling.h
        """
        from .ProfileTemplate import profile_header

        config_xml = """
        _out_file << "  <config>" << std::endl;
        _out_file << "    <paradigm>%(paradigm)s</paradigm>" << std::endl;
        _out_file << "    <num_threads>%(num_threads)s</num_threads>" << std::endl;
        _out_file << "  </config>" << std::endl;
        """ % { 'paradigm': Global.config["paradigm"], 'num_threads': Global.config["num_threads"]}
        config = Global.config["paradigm"] + '_'  + str(Global.config["num_threads"]) + 'threads'
        return profile_header % { 'config': config, 'config_xml': config_xml }
