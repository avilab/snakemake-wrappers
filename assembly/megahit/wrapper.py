__author__ = "Taavi Päll"
__copyright__ = "Copyright 2019, Taavi Päll"
__email__ = "tapa741@gmail.com"
__license__ = "MIT"

from snakemake.shell import shell
from os.path import dirname

# Check inputs/arguments.
inputs = dict(snakemake.input)
input_names = list(inputs.keys())

# Extract arguments.
extra = snakemake.params.get("extra", "")

# Compose input flags.
if input_names == ["pe1", "pe2"]:
    input_flags = "-1 {pe1} -2 {pe2}"
elif input_names == ["pe12"]:
    input_flags = "--12 {pe12}"
elif input_names == ["se"]:
    input_flags = "-r {se}"
else:
    raise RuntimeError(
        "Reads parameter must contain either:\n"
        "a) two comma-separated lists named 'pe1' and 'pe2' of fasta/q paired-end files\n"
        "b) one comma-separated list named 'pe12' of interleaved fasta/q paired-end files\n"
        "c) one omma-separated list named 'se' of fasta/q single-end files."
    )

# Merge input paths with flags.
inputs.update(
    (k, ",".join(v if isinstance(v, type([])) else [v])) for k, v in inputs.items()
)
input_flags = input_flags.format(**inputs)

# Get output dir name from output path where spades writes its output files.
# Pick output dir from the first output file path.
# See megahit wiki https://github.com/voutcn/megahit/wiki.
outdir = dirname(snakemake.output[0])

# Setup log.
log = snakemake.log_fmt_shell(stdout=False, stderr=True)

# Run command.
shell(
    "(megahit {extra} -f"
    " -t {snakemake.threads}"
    " {input_flags}"
    " -o {outdir}) {log}"
)
