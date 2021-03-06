from nbconvert.preprocessors import ExecutePreprocessor
from traitlets import Bool, List
from textwrap import dedent

from . import NbGraderPreprocessor

class UnresponsiveKernelError(Exception):
    pass


class Execute(NbGraderPreprocessor, ExecutePreprocessor):

    interrupt_on_timeout = Bool(True)
    allow_errors = Bool(True)
    raise_on_iopub_timeout = Bool(True)
    extra_arguments = List([], help=dedent(
        """
        A list of extra arguments to pass to the kernel. For python kernels,
        this defaults to ``--HistoryManager.hist_file=:memory:``. For other
        kernels this is just an empty list.
        """)
    ).tag(config=True)

    def preprocess(self, nb, resources):
        kernel_name = nb.metadata.get('kernelspec', {}).get('name', 'python')
        if self.extra_arguments == [] and kernel_name == "python":
            self.extra_arguments = ["--HistoryManager.hist_file=:memory:"]

        try:
            output = super(Execute, self).preprocess(nb, resources)
        except RuntimeError:
            raise UnresponsiveKernelError()

        return output
